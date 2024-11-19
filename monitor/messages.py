import json
import logging
import os
import traceback
import urllib.parse
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Generic
from typing import TypeVar

logger = logging.getLogger()
BaseMessageType = TypeVar('BaseMessageType', bound='BaseMessage')


class BaseMessage(ABC, Generic[BaseMessageType]):

    @property
    def as_dict(self) -> dict[str, Any]:
        return self.__dict__

    @property
    def as_json(self) -> str:
        return json.dumps(self.as_dict, default=str)

    @classmethod
    def from_dict(cls, message: dict):
        # noinspection PyArgumentList
        return cls(**message)

    @classmethod
    def from_error(cls, error: Exception, context) -> BaseMessageType:
        try:
            error_dict = json.loads(str(error))
        except json.JSONDecodeError:
            logger.error(f'Error message is not a JSON string: {str(error)}')
            raise ValueError('Error message is not a JSON string.')
        return cls.from_dict(error_dict)

    @property
    @abstractmethod
    def as_str(self) -> str:
        pass


@dataclass
class ErrorMessage(BaseMessage):
    name: str
    text: str

    @property
    def as_str(self) -> str:
        return (
            f'Error: {self.name}\n'
            f'Message: {self.text}'
        )


@dataclass
class LambdaErrorMessage(ErrorMessage):
    traceback: str
    request_id: str
    cloudwatch: str
    envs: dict[str, str] = field(default_factory=dict)

    @property
    def as_str(self) -> str:
        return super().as_str + '\n' + (
            f'Traceback:\n{self.traceback}\n'
            f'AWS Request ID: {self.request_id}\n'
            f'CloudWatch Logs: {self.cloudwatch}\n'
            f'Environment:\n{json.dumps(self.envs, indent=2)}\n'
        )

    @classmethod
    def from_error(cls, error: Exception, context) -> 'LambdaErrorMessage':
        envs = cls.get_envs()
        return cls(
            name=type(error).__name__,
            text=str(error),
            traceback=traceback.format_exc(),
            request_id=context.aws_request_id,
            cloudwatch=cls.get_cloudwatch_link(
                region=envs['default_region'],
                log_group_name=envs['lambda_log_group_name'],
                log_stream_name=envs['lambda_log_stream_name'],
                aws_request_id=context.aws_request_id
            ),
            envs=envs,
        )

    def add_envs(self):
        self.envs = self.get_envs()

    @staticmethod
    def get_envs():
        envs = {}
        for key in (
                'AWS_EXECUTION_ENV',
                'AWS_DEFAULT_REGION',
                'AWS_LAMBDA_FUNCTION_NAME',
                'AWS_LAMBDA_FUNCTION_MEMORY_SIZE',
                'AWS_LAMBDA_LOG_GROUP_NAME',
                'AWS_LAMBDA_LOG_STREAM_NAME',
        ):
            envs[key.lower()[4:]] = os.environ[key]
        return envs

    @staticmethod
    def get_cloudwatch_link(
            region: str,
            log_group_name: str,
            log_stream_name: str,
            aws_request_id: str
    ) -> str:
        """
        Generate a deep link to the specific Lambda function log in AWS CloudWatch Logs.
        """
        encoded_log_group = urllib.parse.quote(log_group_name, safe='')
        encoded_log_stream = urllib.parse.quote(log_stream_name, safe='')
        filter_pattern = urllib.parse.quote(f'"{aws_request_id}"', safe='')
        return (
            f'https://{region}.console.aws.amazon.com/cloudwatch/home'
            f'?region={region}'
            f'#logsV2:log-groups/log-group/{encoded_log_group}'
            f'/log-events/{encoded_log_stream}'
            f'?filterPattern={filter_pattern}'
        )


@dataclass
class DbtMessage(BaseMessage):
    name: str
    text: str

    @property
    def as_str(self) -> str:
        return self.text


def from_event(event: dict) -> BaseMessageType:
    if 'Error' in event and 'Cause' in event:
        if isinstance(event['Cause'], str):
            event['Cause'] = json.loads(event['Cause'])
        return from_event(event['Cause'])

    match event.get('errorType'):
        case 'LambdaException':
            error_message_dict = json.loads(event['errorMessage'])
            return LambdaErrorMessage(**error_message_dict)
        case 'DbtRuntimeError':
            error_message_dict = json.loads(event['errorMessage'])
            return DbtMessage(**error_message_dict)
        case _:
            text = json.dumps(event, indent=2, default=str)
            return ErrorMessage(name='Unknown', text=text)
