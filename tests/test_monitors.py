import os

from monitor.messages import ErrorMessage
from monitor.monitors import dev_channel_set
from monitor.monitors import EmailMonitor
from monitor.monitors import SlackMonitor


def test_slack_channel_info():
    dev_channel_set.info.send('Test Message Info')


def test_slack_channel_alert():
    dev_channel_set.alert.send('Test Message Alert')


def test_slack_monitor():
    monitor = SlackMonitor(None, dev_channel_set)
    message = ErrorMessage('Test Error', 'Test Message')
    monitor.notify(message)


def test_email_monitor():
    os.environ['AWS_PROFILE'] = 'sandbox'
    monitor = EmailMonitor('christian.schaefer@tatenmitdaten.com', [])
    message = ErrorMessage('Test Error', 'Test Message')
    monitor.notify(message)
