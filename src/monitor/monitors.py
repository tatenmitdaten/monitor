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
