from monitor.messages import from_event


def test_step_function_error_handler():
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
