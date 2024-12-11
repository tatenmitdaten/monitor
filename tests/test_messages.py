from monitor.messages import from_event


def test_step_function_error_handler1():
    event = {
        "Cause": "The cause could not be determined because Lambda did not return an error type. Returned payload: {\"errorMessage\":\"2024-11-26T00:36:39.604Z 5b1c368c-fa4f-448d-8d37-595d2633cc9b Task timed out after 600.15 seconds\"}",
        "Error": "Lambda.Unknown",
        "ExecutionArn": "arn:aws:states:eu-central-1:123456789:execution:ExtractLoad-prod:12747c42-6fca-4e74-9eb6-0b36555e75b4",
        "Input": "{\"job_id\":\"74d69da730b04488b7978b40719861e3\"}",
        "InputDetails": {
            "Included": True
        },
        "Name": "12747c42-6fca-4e74-9eb6-0b36555e75b4",
        "RedriveCount": 0,
        "RedriveStatus": "REDRIVABLE",
        "StartDate": 1732579237465,
        "StateMachineArn": "arn:aws:states:eu-central-1:073230366257:stateMachine:ExtractLoad-prod",
        "Status": "FAILED",
        "StopDate": 1732581399675
    }
    message = from_event(event)
    print(message.as_str)


def test_step_function_error_handler2():
    event = {
        "Error": "States.TaskFailed",
        "Cause": "{\"Cause\":\"The cause could not be determined because Lambda did not return an error type. Returned payload: {\\\"errorMessage\\\":\\\"2024-12-01T22:42:19.181Z d53c5f6b-eb1d-49bd-a1f9-98b0112f1781 Task timed out after 900.01 seconds\\\"}\",\"Error\":\"Lambda.Unknown\",\"ExecutionArn\":\"arn:aws:states:eu-central-1:550813846955:execution:ExtractLoad-prod:16b05321-9cdf-4027-bc86-170d90311048\",\"Input\":\"{\\\"job_id\\\":\\\"122afa1e5f2d414ba3df3f697fbb541a\\\",\\\"clean\\\":{\\\"task_type\\\":\\\"CleanTask\\\",\\\"task_id\\\":\\\"ed1117eb96a8487b8ed7acc5550c82c7\\\",\\\"job_id\\\":\\\"122afa1e5f2d414ba3df3f697fbb541a\\\",\\\"database_name\\\":\\\"sources\\\",\\\"schema_name\\\":\\\"eventim\\\",\\\"table_name\\\":\\\"ext_fact_event_transaction\\\"},\\\"extract\\\":[{\\\"task_type\\\":\\\"ExtractTask\\\",\\\"task_id\\\":\\\"4bfc839fb5bc4c29b55c8f25cfad8e58\\\",\\\"job_id\\\":\\\"122afa1e5f2d414ba3df3f697fbb541a\\\",\\\"database_name\\\":\\\"sources\\\",\\\"schema_name\\\":\\\"eventim\\\",\\\"table_name\\\":\\\"ext_fact_event_transaction\\\"}],\\\"load\\\":{\\\"task_type\\\":\\\"LoadTask\\\",\\\"task_id\\\":\\\"6ddcfdf9a2b2484786e052ad24d7766c\\\",\\\"job_id\\\":\\\"122afa1e5f2d414ba3df3f697fbb541a\\\",\\\"database_name\\\":\\\"sources\\\",\\\"schema_name\\\":\\\"eventim\\\",\\\"table_name\\\":\\\"ext_fact_event_transaction\\\"}}\",\"InputDetails\":{\"Included\":true},\"Name\":\"16b05321-9cdf-4027-bc86-170d90311048\",\"RedriveCount\":0,\"RedriveStatus\":\"REDRIVABLE\",\"StartDate\":1733089875458,\"StateMachineArn\":\"arn:aws:states:eu-central-1:550813846955:stateMachine:ExtractLoad-prod\",\"Status\":\"FAILED\",\"StopDate\":1733092939260}"
    }
    message = from_event(event)
    print(message.as_str)


def test_step_function_error_handler3():
    event = {
        "Error": "LambdaException",
        "Cause": "{\"errorMessage\": \"{\\\"name\\\": \\\"DbtTestError\\\", \\\"text\\\": \\\"Fail\\\", \\\"traceback\\\": \\\"Traceback (most recent call last):\\\\n  File \\\\\\\"/var/task/monitor/wrapper.py\\\\\\\", line 27, in wrapper\\\\n    return func(event, context)\\\\n           ^^^^^^^^^^^^^^^^^^^^\\\\n  File \\\\\\\"/var/task/app.py\\\\\\\", line 14, in lambda_handler\\\\n    return dbt_lambda.app.lambda_handler(event, context)\\\\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\\\\n  File \\\\\\\"/var/task/dbt_lambda/app.py\\\\\\\", line 33, in lambda_handler\\\\n    raise DbtTestError('Fail')\\\\ndbt_lambda.app.DbtTestError: Fail\\\\n\\\", \\\"request_id\\\": \\\"dadaf7fd-c55a-441a-9345-e8b0945a1c32\\\", \\\"cloudwatch\\\": \\\"https://eu-central-1.console.aws.amazon.com/cloudwatch/home?region=eu-central-1#logsV2:log-groups/log-group/%2Faws%2Flambda%2FTransformFunction-dev/log-events/2024%2F12%2F11%2F%5B%24LATEST%5D07ff23830fd346cbb8a95ecac68cca1b?filterPattern=%22dadaf7fd-c55a-441a-9345-e8b0945a1c32%22\\\", \\\"envs\\\": {\\\"execution_env\\\": \\\"AWS_Lambda_python3.12\\\", \\\"default_region\\\": \\\"eu-central-1\\\", \\\"lambda_function_name\\\": \\\"TransformFunction-dev\\\", \\\"lambda_function_memory_size\\\": \\\"384\\\", \\\"lambda_log_group_name\\\": \\\"/aws/lambda/TransformFunction-dev\\\", \\\"lambda_log_stream_name\\\": \\\"2024/12/11/[$LATEST]07ff23830fd346cbb8a95ecac68cca1b\\\"}}\", \"errorType\": \"LambdaException\", \"requestId\": \"dadaf7fd-c55a-441a-9345-e8b0945a1c32\", \"stackTrace\": [\"  File \\\"/var/task/monitor/wrapper.py\\\", line 43, in wrapper\\n    raise LambdaException(message.as_json)\\n\"]}"
    }
    message = from_event(event)
    print(message.as_str)
