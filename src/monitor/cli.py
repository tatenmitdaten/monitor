import json
import os
import uuid
from typing import Annotated

import boto3
import typer
from click import Choice
from typer import Option

cli = typer.Typer(
    add_completion=False,
    pretty_exceptions_enable=False
)


def start_statemachine(name: str, payload: str | dict[str, object] | None = None):
    env = os.environ.get('APP_ENV', 'dev')
    aws_region = os.environ.get('AWS_REGION', 'eu-central-1')
    try:
        aws_account_id = os.environ['AWS_ACCOUNT_ID']
    except KeyError:
        raise KeyError('AWS_ACCOUNT_ID environment variable not set')
    state_machine_arn = f'arn:aws:states:{aws_region}:{aws_account_id}:stateMachine:{name}-{env}'
    if isinstance(payload, dict):
        payload = json.dumps(payload)
    response = boto3.client('stepfunctions').start_execution(
        stateMachineArn=state_machine_arn,
        name=f'Test-Error-Handling-{uuid.uuid4()}',
        input=payload or '{}',
    )
    execution_arn = response['executionArn']
    execution_link = f'https://{aws_region}.console.aws.amazon.com/states/home?region={aws_region}#/v2/executions/details/{execution_arn}'
    print(execution_link)


def invoke_lambda_function(name: str, payload: dict):
    from rich import print
    env = os.environ.get('APP_ENV', 'dev')
    aws_region = os.environ.get('AWS_REGION', 'eu-central-1')
    try:
        aws_account_id = os.environ['AWS_ACCOUNT_ID']
    except KeyError:
        raise KeyError('AWS_ACCOUNT_ID environment variable not set')
    function_arn = f'arn:aws:lambda:{aws_region}:{aws_account_id}:function:{name}-{env}'
    if isinstance(payload, dict):
        payload = json.dumps(payload)
    response = boto3.client('lambda').invoke(
        FunctionName=function_arn,
        Payload=payload or '{}',

    )
    payload = json.loads(response['Payload'].read())
    print(payload)


@cli.command(name='schedule')
def error_handling_schedule(
        fail: Annotated[bool, Option(help='Fail Lambda execution')] = False,
):
    """
    Test error handling in ScheduleTask
    """
    start_statemachine(
        'ExtractLoadJobQueue',
        {
            'task_type': 'ScheduleTask',
            'job_id': 'test job id',
            'task_id': 'test task id',
            'table_names': [],  # will raise test error in ScheduleTask
            'options': {
                'test_error': True,
                'fail_on_error': fail
            }
        }
    )


@cli.command(name='extractload')
def error_handling_extractload(
        fail: Annotated[bool, Option(help='Fail Lambda execution')] = False,
):
    """
    Test error handling in ExtractLoad
    """
    start_statemachine(
        name='ExtractLoadJobQueue',
        payload={
            'task_type': 'ScheduleTask',
            'job_id': 'test job id',
            'task_id': 'test task id',
            'table_names': ['any'],  # will raise test error in ExtractLoadJob
            'options': {
                'test_error': True,
                'fail_on_error': fail
            }
        }
    )


@cli.command(name='transform')
def error_handling_transform(
        mode: Annotated[str, Option(
            '-m', '--mode',
            help='Error mode',
            click_type=Choice(choices=['error', 'fail', 'test'], case_sensitive=False)
        )]
):
    """
    Test error handling in Transform
    """
    start_statemachine(
        name='Transform',
        payload={
            'args': [f'x-{mode}']
        }
    )


@cli.command(name='lambda')
def error_handling_lambda(
        fail: Annotated[bool, Option(help='Fail Lambda execution')] = False,
        test: Annotated[bool, Option(help='Start dbt test run')] = False,
        function: Annotated[str, Option(
            '-f', '--function',
            help='Lambda function name',
            click_type=Choice(choices=['Transform', 'ExtractLoad'], case_sensitive=False)
        )] = 'ExtractLoad',
):
    """
    Test error handling in Lambda functions (Transform, ExtractLoad)
    """
    if function.lower() == 'transform':
        function = 'TransformFunction'
        if test:
            arg = 'x-test'
        elif fail:
            arg = 'x-fail'
        else:
            arg = 'x-error'
        payload = {'args': [arg]}
    else:
        function = 'ExtractLoadFunction'
        payload = {
            'task_type': 'ErrorTask',
            'job_id': 'test job id',
            'task_id': 'test task id',
            'database_name': 'test database',
            'schema_name': 'test schema',
            'table_name': 'test table',
            'envs': {'FAIL_ON_ERROR': str(fail)}
        }
    invoke_lambda_function(
        name=function,
        payload=payload
    )
