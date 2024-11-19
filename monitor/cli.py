import json
import os
import uuid

import boto3
import typer

cli = typer.Typer()


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


@cli.command(name='schedule')
def error_handling_schedule():
    start_statemachine(
        'ExtractLoadJobQueue',
        {
            "task_name": "ScheduleTask",
            "schema_names": ["error"],  # will raise test error
        }
    )


@cli.command(name='extractload')
def error_handling_extractload():
    start_statemachine(
        'ExtractLoadJobQueue',
        {
            "task_name": "ScheduleTask",
            "schema_names": [],
            "table_names": ["error"],  # will raise test error
        }
    )


@cli.command(name='transform')
def error_handling_transform():
    start_statemachine(
        'Transform-dev',
        {
            "args": ["error"]
        }
    )
