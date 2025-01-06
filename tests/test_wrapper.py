import json
import os

import pytest

from monitor.monitors import BaseMonitor
from monitor.wrapper import lambda_monitor
from monitor.wrapper import LambdaErrorMessage
from monitor.wrapper import LambdaException


def test_get_cloudwatch_link():
    link = LambdaErrorMessage.get_cloudwatch_link(
        region='eu-central-1',
        log_group_name='/aws/lambda/ExtractLoadFunction-dev',
        log_stream_name='2024/10/31/[$LATEST]1ef30f6c48d24e3287ee2b41908216b2',
        aws_request_id='24dfa092-ca3b-400c-954d-7ce9cfbf4bc3'
    )
    assert link == 'https://eu-central-1.console.aws.amazon.com/cloudwatch/home?region=eu-central-1#logsV2:log-groups/log-group/%2Faws%2Flambda%2FExtractLoadFunction-dev/log-events/2024%2F10%2F31%2F%5B%24LATEST%5D1ef30f6c48d24e3287ee2b41908216b2?filterPattern=%2224dfa092-ca3b-400c-954d-7ce9cfbf4bc3%22'


@pytest.fixture
def aws_lambda_vars():
    vars_map = {
        'AWS_EXECUTION_ENV': 'python3.12',
        'AWS_DEFAULT_REGION': 'eu-central-1',
        'AWS_LAMBDA_FUNCTION_NAME': 'TestFunction-dev',
        'AWS_LAMBDA_FUNCTION_VERSION': '$LATEST',
        'AWS_LAMBDA_FUNCTION_MEMORY_SIZE': '128',
        'AWS_LAMBDA_LOG_GROUP_NAME': '/aws/lambda/TestFunction-dev',
        'AWS_LAMBDA_LOG_STREAM_NAME': '2024/10/31/[$LATEST]1ef30f6c48d24e3287ee2b41908216b2',
    }
    for key, value in vars_map.items():
        os.environ[key] = value
    yield
    for key in vars_map:
        del os.environ[key]


@pytest.fixture
def context():
    class Context:
        aws_request_id = '24dfa092-ca3b-400c-954d-7ce9cfbf4bc3'

    return Context()


def test_lambda_error_handler(aws_lambda_vars, context):
    os.environ['FAIL_ON_ERROR'] = 'true'

    @lambda_monitor(
        monitor=BaseMonitor()
    )
    def my_lambda_handler(_, __):
        raise RuntimeError('Test Error')

    with pytest.raises(LambdaException) as wrapper:
        my_lambda_handler({}, context)
    error = wrapper.value

    error_dict = json.loads(error.__str__())
    error_message = LambdaErrorMessage.from_dict(error_dict)
    error_message.traceback = error_message.traceback.split('\n')[0]
    expected = LambdaErrorMessage(
        name='RuntimeError',
        text='Test Error',
        traceback='Traceback (most recent call last):',
        request_id='24dfa092-ca3b-400c-954d-7ce9cfbf4bc3',
        cloudwatch='https://eu-central-1.console.aws.amazon.com/cloudwatch/home?region=eu-central-1#logsV2:log-groups/log-group/%2Faws%2Flambda%2FTestFunction-dev/log-events/2024%2F10%2F31%2F%5B%24LATEST%5D1ef30f6c48d24e3287ee2b41908216b2?filterPattern=%2224dfa092-ca3b-400c-954d-7ce9cfbf4bc3%22',
        envs={
            'execution_env': 'python3.12',
            'default_region': 'eu-central-1',
            'lambda_function_name': 'TestFunction-dev',
            'lambda_function_memory_size': '128',
            'lambda_log_group_name': '/aws/lambda/TestFunction-dev',
            'lambda_log_stream_name': '2024/10/31/[$LATEST]1ef30f6c48d24e3287ee2b41908216b2'
        })

    assert expected == error_message
