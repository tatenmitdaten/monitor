import os
import zoneinfo
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from typing import cast
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
        datetime_str = datetime.now(timezone).strftime("%d.%m.%Y %H:%M:%S")
        subject = f'⚠ ELT-Fehler ({message.name or 'unbekannt'}) - {datetime_str}'
        message = cast(str, message.as_str)  # workaround for PyCharm bug
        return send_email(subject, message, to_addresses, self.sender_address)


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
