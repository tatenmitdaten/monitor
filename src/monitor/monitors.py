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
from typing import Generic

import boto3
from botocore.exceptions import ClientError

from monitor.messages import BaseMessageType
from monitor.messages import ErrorMessage

env = os.environ.get('APP_ENV', 'dev')
timezone = zoneinfo.ZoneInfo('Europe/Berlin')

logger = getLogger()


class BaseMonitor(Generic[BaseMessageType]):

    def notify(self, message: BaseMessageType) -> None:
        print(message.as_str)


@dataclass
class Email:
    subject: str
    message: str
    to_addresses: list[str]
    source: str

    def send(self):
        client = boto3.client('ses', region_name='eu-central-1')
        email_message = {
            'Subject': {'Data': self.subject},
            'Body': {'Text': {'Data': self.message}},
        }
        try:
            response = client.send_email(
                Source=self.source,
                Destination={'ToAddresses': self.to_addresses},
                Message=email_message  # type: ignore
            )
            message_id = response['MessageId']
            logger.info(f'Email sent to {self.to_addresses}. Message ID: {message_id}')
        except ClientError as e:
            logger.error(e.__str__())
            raise


@dataclass
class EmailMonitor(BaseMonitor):
    sender_address: str
    prod_addresses: list[str]
    dev_addresses: tuple[str] = (
        'christian.schaefer@tatenmitdaten.com',
    )

    def notify(self, message: BaseMessageType):
        to_addresses = list(self.dev_addresses)
        if env == 'prod':
            to_addresses.extend(self.prod_addresses)
        datetime_str = datetime.datetime.now(timezone).strftime("%d.%m.%Y %H:%M:%S")
        email = Email(
            subject=f'⚠ ELT-Fehler ({message.name or 'unbekannt'}) - {datetime_str}',
            message=cast(str, message.as_str),  # workaround for PyCharm bug
            to_addresses=to_addresses,
            source=self.sender_address
        )
        return email.send()


@dataclass
class SlackChannel:
    name: str
    webhook_path: str

    @property
    def webhook_url(self) -> str:
        return f'https://hooks.slack.com/services/{self.webhook_path}'

    def send(self, text: str | None, payload: dict | None = None):
        payload = payload or {'text': text}
        request = urllib.request.Request(
            url=self.webhook_url,
            data=json.dumps(payload).encode('ascii'),
            headers={"Content-Type": "application/json"}
        )
        logger.info(f'Sending message to {self.name} Slack channel')
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                if response.status != 200:
                    logger.info(response.status)
                    logger.info(response.content)
        except socket.timeout:
            logger.info(f"Request to {self.webhook_url} timed out 3 times.")


@dataclass(frozen=True)
class SlackChannelSet:
    info: SlackChannel
    alert: SlackChannel


dev_channel_set = SlackChannelSet(
    info=SlackChannel(
        'test-slack-monitor-info',
        'T023N0JQGCT/B085359997G/Fsu6con2cq6NDtYdZhcKiX6M'
    ),
    alert=SlackChannel(
        'test-slack-monitor-alert',
        'T023N0JQGCT/B085YMDB29W/6WKsQJilssDiQMooCu3mFO9g'
    )
)


@dataclass
class SlackMonitor(BaseMonitor):
    prod_channels: SlackChannelSet | None
    dev_channels: SlackChannelSet = dev_channel_set

    @property
    def channels(self) -> SlackChannelSet:
        return self.prod_channels if env == 'prod' else self.dev_channels

    def notify(self, message: BaseMessageType):
        logger.info(message.as_str)
        if isinstance(message, ErrorMessage):
            channel = self.channels.alert
            text = f'<!channel> {message.as_str}'
        else:
            channel = self.channels.info
            text = message.as_str
        channel.send(text=text)

    """
    def send_results(self, results: dict):
        for message in self.parse_results(results):
            is_alert = 'traceback' in results or not results.get('success', True)
            channel = self.channels.alert if is_alert else self.channels.info
            if message:
                channel.send(text=message)

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
    def get_lambda_crash_summary() -> str:
        function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        if not function_name:
            return 'Lambda crashed'
        cloudwatch_link = LambdaErrorMessage.get_cloudwatch_link(
            region='eu-central-1',
            log_group_name=os.environ['AWS_LAMBDA_LOG_GROUP_NAME'],
            log_stream_name=os.environ['AWS_LAMBDA_LOG_STREAM_NAME'],
            aws_request_id=os.environ.get('AWS_REQUEST_ID', '')
        )
        return f'`{function_name}` crashed, see <{cloudwatch_link}|cloudwatch> for details'
    """
