import logging
import signal
import threading

import boto3
import pytest

from src.api.maintenance_mode import get_maintenance_mode_config
from src.task.sqs_processor import BaseSqsProcessor, SqsProcessorConfig


class DrainingProcessor(BaseSqsProcessor):
    """A minimal processor that just takes whatever's on the queue off it.

    Stands in for a real consumer so these tests cover the base class rather than
    anything workflow-specific.
    """

    maintenance_mode_log_event = "maintenance_mode_test_processing_skipped"

    def __init__(self, queue_url: str, config: SqsProcessorConfig):
        self._queue_url = queue_url
        super().__init__(config)
        self.on_start_call_count = 0

    @property
    def queue_url(self) -> str:
        return self._queue_url

    def on_start(self) -> None:
        self.on_start_call_count += 1

    def process_batch(self) -> list:
        messages = self.sqs_client.receive_messages(wait_time=self.config.cycle_duration)
        self.sqs_client.delete_message_batch([message.receipt_handle for message in messages])
        return messages


@pytest.fixture
def single_batch_config():
    # Don't long-poll or loop forever - we only want a single batch per test.
    return SqsProcessorConfig(cycle_duration=0, maximum_batch_count=1)


@pytest.fixture
def processor(workflow_sqs_queue, single_batch_config):
    """A processor pointed at the local mock queue.

    Reuses the workflow queue fixture rather than standing up another one - the base
    class doesn't care which queue it's given.
    """
    return DrainingProcessor(workflow_sqs_queue, single_batch_config)


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


####################
# Config
####################


def test_config_defaults():
    config = SqsProcessorConfig()

    assert config.cycle_duration == 10
    # No limit under ordinary circumstances - the loop runs until it's signalled
    assert config.maximum_batch_count is None


####################
# The poll loop
####################


def test_run_stops_at_batch_limit(processor, workflow_sqs_queue):
    send_messages(workflow_sqs_queue, 1)

    # Would otherwise poll forever - the batch limit is what lets this return
    processor.run()

    assert processor.metrics["batches_processed"] == 1
    assert get_queue_message_count(workflow_sqs_queue) == 0


def test_run_calls_on_start_once_before_the_first_batch(workflow_sqs_queue):
    processor = DrainingProcessor(
        workflow_sqs_queue, SqsProcessorConfig(cycle_duration=0, maximum_batch_count=3)
    )

    processor.run()

    assert processor.metrics["batches_processed"] == 3
    assert processor.on_start_call_count == 1


def test_run_stops_after_sigterm(workflow_sqs_queue):
    """A SIGTERM is handled between batches, not mid-batch."""
    # No batch limit - the signal is the only thing that ends the loop
    processor = DrainingProcessor(workflow_sqs_queue, SqsProcessorConfig(cycle_duration=0))

    batches_seen = []
    real_process_batch = processor.process_batch

    def process_batch_then_signal():
        result = real_process_batch()
        batches_seen.append(result)
        # Exercise the real handler rather than poking internal state
        processor.handle_exit(signal.SIGTERM, None)
        return result

    processor.process_batch = process_batch_then_signal
    processor.run()

    assert processor.sigterm_received is True
    assert len(batches_seen) == 1
    assert processor.metrics["batches_processed"] == 1


def test_handle_interrupt_exits_immediately(processor):
    """A keyboard interrupt doesn't wait for the current batch."""
    with pytest.raises(SystemExit):
        processor.handle_interrupt(signal.SIGINT, None)


####################
# Maintenance mode
####################


@pytest.fixture
def enable_maintenance_mode(monkeypatch):
    """Turn maintenance mode on for the duration of a test.

    The maintenance-mode config is @cached, so clear it around the env change.
    """
    monkeypatch.setenv("ENABLE_MAINTENANCE_MODE", "true")
    get_maintenance_mode_config.cache_clear()
    yield
    get_maintenance_mode_config.cache_clear()


def test_run_idles_during_maintenance_rather_than_returning(
    processor, workflow_sqs_queue, enable_maintenance_mode, caplog
):
    """During a maintenance window the processor waits for a SIGTERM instead of exiting.

    Returning early would have ECS restart the task in a loop for the length of the
    window, so idling is the behavior worth pinning down. The message we enqueue
    proves nothing was consumed while idling.
    """
    caplog.set_level(logging.INFO)
    send_messages(workflow_sqs_queue, 1)

    # Simulate the SIGTERM a force-new-deployment sends so the idle loop wakes
    processor.handle_exit(signal.SIGTERM, None)

    processor.run()

    assert processor.metrics["batches_processed"] == 0
    assert processor.on_start_call_count == 0
    # The message is untouched - the queue was never polled
    assert get_queue_message_count(workflow_sqs_queue) == 1

    skip_records = [
        record
        for record in caplog.records
        if getattr(record, "maintenance_mode_event", None)
        == DrainingProcessor.maintenance_mode_log_event
    ]
    assert len(skip_records) == 1


def test_idle_during_maintenance_wakes_on_a_later_sigterm(
    processor, workflow_sqs_queue, enable_maintenance_mode
):
    """The idle wait is released by a signal that arrives after it starts blocking."""

    def send_sigterm_shortly():
        processor.handle_exit(signal.SIGTERM, None)

    timer = threading.Timer(0.05, send_sigterm_shortly)
    timer.start()
    try:
        # Blocks until the timer above fires - hangs forever if the signal doesn't
        # release the wait, which the suite-level timeout would surface.
        processor.run()
    finally:
        timer.cancel()

    assert processor.sigterm_received is True
    assert processor.metrics["batches_processed"] == 0
