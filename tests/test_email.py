import json


def notification():
    def lambda_handler(event, _):
        return {}

    payload = {
        "errorMessage": "Test Error",
        "errorType": "RuntimeError",
        "requestId": "RequestId",
        "stackTrace": [
            "/var/task/monitor/app.py",
        ]

    }
    input_ = {
        "test": {
            "action": "test",
        }
    }
    cause = {
        "Cause": json.dumps(payload),
        "Error": "RuntimeError",
        "ExecutionArn": "arn:aws:states:eu-central-1:testtest:execution:Test-prod:d145050b-002f-4a77-aa0c-503bb30d90be",
        "Input": json.dumps(input_),
    }
    event = {
        "Error": "States.TaskFailed",
        "Cause": json.dumps(cause)
    }
    response = lambda_handler(event, None)
    assert response == {'Status': 'SUCCESS'}
