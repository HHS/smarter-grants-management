import logging
import signal

import boto3
import pytest
from grants_shared.api.maintenance_mode import get_maintenance_mode_config

from src.task.workflow_queue_task import (
    WorkflowQueueListener,
    WorkflowQueueListenerConfig,
    WorkflowQueueListenerLogEvent,
)


@pytest.fixture
def listener_config():
    # Don't long-poll or loop forever - we only want a single batch per test.
    return WorkflowQueueListenerConfig(
        workflow_cycle_duration=0,
        workflow_maximum_batch_count=1,
    )


def send_messages(queue_url, count):
    sqs = boto3.client("sqs", region_name="us-east-1")
    for i in range(count):
        sqs.send_message(QueueUrl=queue_url, MessageBody=f'{{"example_field": "value{i}"}}')


def get_queue_message_count(queue_url):
    sqs = boto3.client("sqs", region_name="us-east-1")
    attributes = sqs.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"]
    )
    return int(attributes["Attributes"]["ApproximateNumberOfMessages"])


def test_process_batch_consumes_messages(workflow_sqs_queue, listener_config):
    send_messages(workflow_sqs_queue, 3)

    messages = WorkflowQueueListener(listener_config).process_batch()

    assert len(messages) == 3
    assert {message.body for message in messages} == {
        '{"example_field": "value0"}',
        '{"example_field": "value1"}',
        '{"example_field": "value2"}',
    }
    # Consuming a message takes it off the queue
    assert get_queue_message_count(workflow_sqs_queue) == 0


def test_process_batch_with_empty_queue(workflow_sqs_queue, listener_config):
    assert WorkflowQueueListener(listener_config).process_batch() == []


def test_listen_stops_at_batch_limit(workflow_sqs_queue, listener_config):
    send_messages(workflow_sqs_queue, 1)

    # Would otherwise poll forever - the batch limit is what lets this return
    WorkflowQueueListener(listener_config).listen()

    assert get_queue_message_count(workflow_sqs_queue) == 0


def test_listen_stops_after_sigterm(workflow_sqs_queue, listener_config):
    # Unset the batch limit so the sigterm flag is the only thing ending the loop
    listener_config.workflow_maximum_batch_count = None
    listener = WorkflowQueueListener(listener_config)
    listener.handle_exit(15, None)

    listener.listen()


@pytest.fixture
def enable_maintenance_mode(monkeypatch):
    """Turn maintenance mode on for the duration of a test.

    The maintenance-mode config is @cached, so clear it around the env change.
    """
    monkeypatch.setenv("ENABLE_MAINTENANCE_MODE", "true")
    get_maintenance_mode_config.cache_clear()
    yield
    get_maintenance_mode_config.cache_clear()


def test_listen_idles_when_maintenance_mode_enabled(
    workflow_sqs_queue, listener_config, enable_maintenance_mode, caplog
):
    """With maintenance mode on the listener idles rather than returning, so ECS
    doesn't restart it in a loop for the length of the maintenance window."""
    caplog.set_level(logging.INFO)
    send_messages(workflow_sqs_queue, 1)

    listener = WorkflowQueueListener(listener_config)
    # Simulate the SIGTERM the force-new-deployment sends, so the idle loop wakes
    # and exits instead of blocking. Exercise the real handler rather than poking
    # internal state so we cover the shutdown path end to end.
    listener.handle_exit(signal.SIGTERM, None)

    listener.listen()

    # The message is untouched - the listener never polled the queue
    assert get_queue_message_count(workflow_sqs_queue) == 1

    skip_records = [
        record
        for record in caplog.records
        if getattr(record, "maintenance_mode_event", None)
        == WorkflowQueueListenerLogEvent.MAINTENANCE_MODE_SKIP
    ]
    assert len(skip_records) == 1
    assert skip_records[0].message == "Skipping workflow processing due to maintenance mode"


def test_workflow_queue_listener_cli(cli_runner, workflow_sqs_queue, monkeypatch):
    send_messages(workflow_sqs_queue, 1)
    monkeypatch.setenv("WORKFLOW_CYCLE_DURATION", "0")
    monkeypatch.setenv("WORKFLOW_MAXIMUM_BATCH_COUNT", "1")

    result = cli_runner.invoke(args=["task", "workflow-queue-listener"])

    assert result.exit_code == 0
    assert get_queue_message_count(workflow_sqs_queue) == 0
