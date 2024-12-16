import functools
import logging
import os
from typing import Any
from typing import Callable

from monitor.messages import DbtMessage
from monitor.messages import LambdaErrorMessage
from monitor.monitors import BaseMonitor


class LambdaException(Exception):
    pass


def lambda_monitor(
        monitor: BaseMonitor,
):
    """
    Decorator factory for AWS Lambda handlers
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(event: dict[str, Any], context: Any):
            try:
                os.environ['AWS_REQUEST_ID'] = context.aws_request_id
                return func(event, context)
            except Exception as error:
                logging.error(error, exc_info=True)
                if type(error).__name__ == 'DbtRuntimeError':
                    if os.environ.get('FAIL_ON_ERROR', 'false').lower() == 'true':
                        raise error
                    else:
                        message = DbtMessage.from_error(error, context)
                        monitor.notify(message)
                        return {
                            'statusCode': 200,
                            'message': message.as_str
                        }
                else:
                    message = LambdaErrorMessage.from_error(error, context)
                    if os.environ.get('FAIL_ON_ERROR', 'false').lower() == 'true':
                        raise LambdaException(message.as_json)
                    else:
                        monitor.notify(message)
                        return {
                            'statusCode': 500,
                            'message': message.as_dict
                        }

        return wrapper

    return decorator
