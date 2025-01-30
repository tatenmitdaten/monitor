import functools
import logging
import os
from typing import Any
from typing import Callable

from monitor.messages import ErrorMessage
from monitor.messages import LambdaErrorMessage
from monitor.messages import SimpleMessage
from monitor.monitors import BaseMonitor

payload = dict[str, Any]


class LambdaException(Exception):
    pass


# noinspection PyUnusedLocal
def lambda_monitor(
        monitor: BaseMonitor,
        notify_hook: Callable[[Any], str | None] = lambda x: None
):
    """
    Decorator factory for AWS Lambda handlers
    """

    def decorator(func: Callable[[payload, Any], payload]):

        @functools.wraps(func)
        def wrapper(event: payload, context: Any):
            os.environ['AWS_REQUEST_ID'] = context.aws_request_id
            try:
                response = func(event, context)
                if text := notify_hook(response):
                    if 'error' in response:
                        monitor.notify(ErrorMessage(name=response['error'], text=text))
                    else:
                        monitor.notify(SimpleMessage(text=text))
            except Exception as error:
                logging.error(error, exc_info=True)
                message = LambdaErrorMessage.from_error(error, event, context)
                if os.environ.get('FAIL_ON_ERROR', 'false').lower() == 'true':
                    raise LambdaException(message.as_json)
                else:
                    monitor.notify(message)
                    return {
                        'statusCode': 500,
                        'message': message.as_dict
                    }
            return response

        return wrapper

    return decorator
