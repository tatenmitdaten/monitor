import datetime
import json
import os
import socket
import urllib.parse
import urllib.request
import zoneinfo
from dataclasses import dataclass
from logging import getLogger
from typing import cast
from typing import Generator
from typing import Generic

import boto3
from botocore.exceptions import ClientError
from monitor.messages import BaseMessageType

env = os.environ.get('APP_ENV', 'dev')
timezone = zoneinfo.ZoneInfo('Europe/Berlin')

logger = getLogger()


class BaseMonitor(Generic[BaseMessageType]):

    def notify(self, message: BaseMessageType) -> None:
        pass


@dataclass
class EmailMonitor(BaseMonitor):
    sender_address: str
    business_addresses: list[str]
    developer_addresses: tuple[str] = (
        'christian.schaefer@tatenmitdaten.com',
    )

    def notify(self, message: BaseMessageType):
        to_addresses = list(self.developer_addresses)
        if env == 'prod':
            to_addresses.extend(self.business_addresses)
        datetime_str = datetime.datetime.now(timezone).strftime("%d.%m.%Y %H:%M:%S")
        subject = f'⚠ ELT-Fehler ({message.name or 'unbekannt'}) - {datetime_str}'
        message = cast(str, message.as_str)  # workaround for PyCharm bug
        return send_email(subject, message, to_addresses, self.sender_address)


@dataclass
class SlackWebhook:
    info: str
    alert: str


@dataclass
class SlackMonitor(BaseMonitor):
    dev: SlackWebhook
    prod: SlackWebhook

    @property
    def webhook(self) -> SlackWebhook:
        if env == 'prod':
            return self.prod
        return self.dev

    def notify(self, message: BaseMessageType):
        text = [message.as_str]
        webhook = self.webhook.info
        if not message.__dict__.get('success', True) or 'traceback' in message:
            webhook = self.webhook.alert
            text.insert(0, '<!channel>')
        send_slack_message(webhook, text=' '.join(text))

    @staticmethod
    def split_message(message: str) -> list:
        if len(message) > 3000:
            lines = message.split('\n')
            messages = []
            message = ''
            for line in lines:
                if len(message) + len(line) > 3000:
                    messages.append(message)
                    message = ''
                message += line + '\n'
            messages.append(message)
            return messages
        return [message]

    @staticmethod
    def parse_results(results: dict) -> Generator[str, None, None]:
        summary = results.get('summary', '') or ''
        message = results.get('messages', '') or ''
        if 'traceback' in results:
            summary = f':no_entry:  {SlackMonitor.get_lambda_crash_summary()}'
            message = results.get('traceback')
        timing = ''
        started_at, ended_at = results.get('started_at'), results.get('ended_at')
        if started_at and ended_at:
            start = datetime.datetime.strptime(started_at, '%Y-%m-%d %H:%M:%S')
            end = datetime.datetime.strptime(ended_at, '%Y-%m-%d %H:%M:%S')
            timing = f' started at {started_at} ({(end - start).seconds}s)'
        for counter, short_message in enumerate(SlackMonitor.split_message(message)):
            if short_message:
                short_message = f'\n```{short_message}```'
            if counter == 0:
                yield summary + timing + short_message
            else:
                yield f'continued long message...{short_message}'

    def send_results(self, results: dict, channel: str = 'info'):
        for message in self.parse_results(results):
            if not results.get('success', True) or 'traceback' in results:
                channel = 'alert'
            if message:
                if channel == 'alert':
                    send_slack_message('alert', '<!channel> ' + message)
                send_slack_message('info', message)

    @staticmethod
    def get_lambda_crash_summary() -> str:
        function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")
        log_stream_group = urllib.parse.quote_plus(os.environ.get("AWS_LAMBDA_LOG_GROUP_NAME", ""))
        log_stream_name = urllib.parse.quote_plus(os.environ.get("AWS_LAMBDA_LOG_STREAM_NAME", ""))
        log_stream_url = 'https://eu-central-1.console.aws.amazon.com/cloudwatch/home?' \
                         'region=eu-central-1#logsV2:log-groups/log-group/' \
                         f'{log_stream_group}/log-events/{log_stream_name}'
        return f'`{function_name}` crashed, see <{log_stream_url}|log stream> for details'


def send_slack_message(webhook: str, text: str | None, payload: dict | None = None):
    payload = payload or {'text': text}
    request = urllib.request.Request(
        url=f'https://hooks.slack.com/services/{webhook}',
        data=json.dumps(payload).encode('ascii'),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            if response.status != 200:
                logger.info(response.status)
                logger.info(response.content)
    except socket.timeout:
        logger.info(f"Request to https://hooks.slack.com/services/{webhook} timed out.")


def send_email(subject: str, message: str, to_addresses: list[str], source: str):
    client = boto3.client('ses', region_name='eu-central-1')
    email_message = {
        'Subject': {'Data': subject},
        'Body': {'Text': {'Data': message}},
    }
    try:
        response = client.send_email(
            Source=source,
            Destination={'ToAddresses': to_addresses},
            Message=email_message  # type: ignore
        )
        message_id = response['MessageId']
        logger.info(f'Email sent to {to_addresses}. Message ID: {message_id}')
    except ClientError as e:
        logger.error(e.__str__())
        raise
