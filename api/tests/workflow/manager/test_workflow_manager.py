import json
import logging
import signal
import threading
import uuid
from unittest.mock import patch

import boto3
import pytest
from grants_shared.adapters.aws.sqs_adapter import SQSClient, SQSMessage
from grants_shared.api.maintenance_mode import get_maintenance_mode_config
from sqlalchemy import select

from src.constants.lookup_constants import (
    MgmtWorkflowEventProcessingResult,
    MgmtWorkflowEventType,
    MgmtWorkflowType,
)
from src.db.models.workflow_models import MgmtWorkflowEventHistory
from src.workflow.event.workflow_event import ProcessWorkflowEventContext, WorkflowEvent
from src.workflow.manager.workflow_manager import (
    WorkflowManager,
    WorkflowManagerConfig,
    WorkflowManagerLogEvent,
    handle_event,
)
from src.workflow.registry.workflow_client_registry import get_workflow_client_registry
from src.workflow.state_machine.prototype_state_machine import PrototypeState
from tests.db.models.factories import MgmtUserFactory, ProgramWorkflowFactory
from tests.workflow.workflow_test_util import build_process_workflow_event

logger = logging.getLogger(__name__)


def get_sqs_client(queue_url) -> SQSClient:
    return SQSClient(queue_url=queue_url, sqs_client=boto3.client("sqs", region_name="us-east-1"))


def build_process_message_body(workflow, user, event_to_send: str, event_id=None) -> dict:
    """Build the SQS payload for a process-workflow event."""
    return {
        "event_id": event_id or uuid.uuid4(),
        "acting_mgmt_user_id": user.mgmt_user_id,
        "event_type": MgmtWorkflowEventType.PROCESS_WORKFLOW,
        "process_workflow_context": ProcessWorkflowEventContext(
            mgmt_workflow_id=workflow.mgmt_workflow_id, event_to_send=event_to_send
        ).model_dump(),
    }


@pytest.fixture
def manager_config():
    # Don't long-poll or loop forever - we only want a single batch per test.
    return WorkflowManagerConfig(cycle_duration=0, maximum_batch_count=1)


@pytest.fixture
def valid_message_body(program):
    """A start-workflow payload for the prototype workflow."""
    user = MgmtUserFactory.create()
    return {
        "event_id": str(uuid.uuid4()),
        "acting_mgmt_user_id": str(user.mgmt_user_id),
        "event_type": MgmtWorkflowEventType.START_WORKFLOW,
        "start_workflow_context": {
            "workflow_type": MgmtWorkflowType.BASIC_TEST_WORKFLOW,
            "mgmt_resource_id": str(program.get_resource_id()),
        },
    }


@pytest.fixture
def valid_sqs_message(valid_message_body):
    return SQSMessage(
        Body=json.dumps(valid_message_body),
        ReceiptHandle="test-receipt-handle",
        MessageId=str(uuid.uuid4()),
    )


####################
# Config
####################


def test_workflow_manager_config_reads_workflow_prefixed_env_vars(monkeypatch):
    """The env_prefix is what keeps the shared field names workflow-specific."""
    monkeypatch.setenv("WORKFLOW_CYCLE_DURATION", "4")
    monkeypatch.setenv("WORKFLOW_MAXIMUM_BATCH_COUNT", "7")
    monkeypatch.setenv("WORKFLOW_EVENT_PROCESSING_TIMEOUT_SEC", "11")

    config = WorkflowManagerConfig()

    assert config.cycle_duration == 4
    assert config.maximum_batch_count == 7
    assert config.event_processing_timeout_sec == 11


####################
# The poll loop
####################


def test_workflow_manager_run(workflow_sqs_queue, app, valid_message_body):
    """run() processes batches and tracks metrics correctly."""
    sqs_client = get_sqs_client(workflow_sqs_queue)

    for _ in range(5):
        body = dict(valid_message_body)
        body["event_id"] = str(uuid.uuid4())
        sqs_client.send_message(body)

    config = WorkflowManagerConfig(cycle_duration=0, maximum_batch_count=3)
    workflow_manager = WorkflowManager(config=config)

    with app.app_context():
        workflow_manager.run()

    metrics = workflow_manager.metrics
    assert metrics["batches_processed"] == 3
    assert metrics["events_processed"] >= 3


def test_run_initializes_the_client_registry(workflow_sqs_queue, app, manager_config):
    """The client registry is set up before the first batch runs."""
    workflow_manager = WorkflowManager(config=manager_config)

    with app.app_context():
        workflow_manager.run()

    # Doesn't raise, which it would if init had never been called
    assert get_workflow_client_registry() is not None


@pytest.fixture
def enable_maintenance_mode(monkeypatch):
    """Turn maintenance mode on for the duration of a test.

    The maintenance-mode config is @cached, so clear it around the env change.
    """
    monkeypatch.setenv("ENABLE_MAINTENANCE_MODE", "true")
    get_maintenance_mode_config.cache_clear()
    yield
    get_maintenance_mode_config.cache_clear()


def test_run_idles_when_maintenance_mode_enabled(
    app, workflow_sqs_queue, valid_message_body, enable_maintenance_mode, caplog
):
    """With maintenance mode on, run() idles without fetching from SQS or
    processing a batch, and exits cleanly once a SIGTERM has been received."""
    caplog.set_level(logging.INFO)

    sqs_client = get_sqs_client(workflow_sqs_queue)
    sqs_client.send_message(valid_message_body)

    workflow_manager = WorkflowManager(config=WorkflowManagerConfig(cycle_duration=0))
    # Simulate the SIGTERM the force-new-deployment sends, so the idle loop wakes
    # and exits instead of blocking. Exercise the real handler rather than poking
    # internal state so we cover the shutdown path end to end.
    workflow_manager.handle_exit(signal.SIGTERM, None)

    with app.app_context():
        workflow_manager.run()

    assert workflow_manager.sigterm_received is True

    # No batch was processed - the manager never touched SQS or the DB.
    assert workflow_manager.metrics["batches_processed"] == 0
    assert workflow_manager.metrics["events_processed"] == 0

    # The message we enqueued is still on the queue - fetch_messages was never called.
    remaining = sqs_client.receive_messages(max_messages=1, wait_time=0)
    assert len(remaining) == 1

    # A distinct, queryable skip event was logged.
    skip_records = [
        record
        for record in caplog.records
        if getattr(record, "maintenance_mode_event", None)
        == WorkflowManagerLogEvent.MAINTENANCE_MODE_SKIP
    ]
    assert len(skip_records) == 1


def test_run_stops_after_sigterm(workflow_sqs_queue, app, valid_message_body):
    """A SIGTERM mid-run is handled after the batch it arrived during finishes."""
    sqs_client = get_sqs_client(workflow_sqs_queue)
    sqs_client.send_message(valid_message_body)

    # No batch limit - the SIGTERM is the only thing that ends the loop
    workflow_manager = WorkflowManager(config=WorkflowManagerConfig(cycle_duration=0))

    real_process_batch = workflow_manager.process_batch

    def process_batch_then_signal():
        result = real_process_batch()
        workflow_manager.handle_exit(signal.SIGTERM, None)
        return result

    with (
        app.app_context(),
        patch.object(workflow_manager, "process_batch", process_batch_then_signal),
    ):
        workflow_manager.run()

    assert workflow_manager.metrics["batches_processed"] == 1


####################
# Parsing messages
####################


def test_parse_event(valid_sqs_message, manager_config, workflow_sqs_queue):
    wfm = WorkflowManager(config=manager_config)
    result = wfm.parse_event(valid_sqs_message)

    assert isinstance(result, WorkflowEvent)
    assert str(result.event_id) == json.loads(valid_sqs_message.body)["event_id"]


def test_fetch_messages_keys_history_on_the_event_id(
    workflow_sqs_queue, app, manager_config, valid_message_body
):
    """The history row's primary key is the caller's event ID, and the event lands in
    the JSONB column as an object rather than a serialized string."""
    get_sqs_client(workflow_sqs_queue).send_message(valid_message_body)

    with app.app_context():
        containers = WorkflowManager(config=manager_config).fetch_messages()

    assert len(containers) == 1
    container = containers[0]

    assert container.history_event.mgmt_workflow_event_history_id == uuid.UUID(
        valid_message_body["event_id"]
    )
    assert isinstance(container.history_event.event_data, dict)
    assert container.history_event.event_data["event_id"] == valid_message_body["event_id"]
    assert container.history_event.is_successfully_processed is True


def test_fetch_messages_skips_unparseable_messages(workflow_sqs_queue, app, manager_config):
    """A message we can't turn into a workflow event is skipped rather than killing the batch."""
    boto_client = boto3.client("sqs", region_name="us-east-1")
    boto_client.send_message(QueueUrl=workflow_sqs_queue, MessageBody="not-json-at-all")

    with app.app_context():
        containers = WorkflowManager(config=manager_config).fetch_messages()

    assert containers == []


####################
# process_batch
####################


def test_process_batch_success(workflow_sqs_queue, app, manager_config):
    """A successfully processed message is deleted off the queue."""
    boto_client = boto3.client("sqs", region_name="us-east-1")
    sqs_client = SQSClient(queue_url=workflow_sqs_queue, sqs_client=boto_client)

    user = MgmtUserFactory.create()
    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    sqs_client.send_message(build_process_message_body(workflow, user, "complete"))

    workflow_manager = WorkflowManager(config=manager_config)
    with app.app_context():
        messages_to_delete, messages_to_keep = workflow_manager.process_batch()

    assert len(messages_to_delete) == 1
    assert len(messages_to_keep) == 0
    assert workflow_manager.metrics["events_processed"] == 1

    # Nothing is left on the queue
    assert sqs_client.receive_messages(max_messages=10, wait_time=0) == []


def test_process_batch_retryable_keeps_message(workflow_sqs_queue, app, manager_config):
    """A retryable error leaves the message on the queue to be picked up again."""
    sqs_client = get_sqs_client(workflow_sqs_queue)

    user = MgmtUserFactory.create()
    # An unrecognized state raises UnexpectedStateError, which is retryable
    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state="not-a-valid-state",
    )

    event_id = uuid.uuid4()
    sqs_client.send_message(build_process_message_body(workflow, user, "complete", event_id))

    workflow_manager = WorkflowManager(config=manager_config)
    with app.app_context():
        messages_to_delete, messages_to_keep = workflow_manager.process_batch()

    assert len(messages_to_delete) == 0
    assert len(messages_to_keep) == 1

    # Reset the visibility timeout so we can confirm the message is still there
    boto3.client("sqs", region_name="us-east-1").change_message_visibility(
        QueueUrl=workflow_sqs_queue, ReceiptHandle=messages_to_keep[0], VisibilityTimeout=0
    )
    remaining = sqs_client.receive_messages(max_messages=5, wait_time=0)
    assert len(remaining) == 1
    assert str(json.loads(remaining[0].body)["event_id"]) == str(event_id)


def test_process_batch_mixed_results(workflow_sqs_queue, app):
    """Success and non-retryable messages are deleted; retryable ones are kept."""
    sqs_client = get_sqs_client(workflow_sqs_queue)
    user = MgmtUserFactory.create()

    # Success
    successful_workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )
    sqs_client.send_message(build_process_message_body(successful_workflow, user, "complete"))

    # Retryable - unrecognized current state
    retryable_workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state="not-a-valid-state",
    )
    sqs_client.send_message(build_process_message_body(retryable_workflow, user, "complete"))

    # Non-retryable - the acting user doesn't exist
    non_retryable_workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )
    non_retryable_body = build_process_message_body(non_retryable_workflow, user, "complete")
    non_retryable_body["acting_mgmt_user_id"] = uuid.uuid4()
    sqs_client.send_message(non_retryable_body)

    workflow_manager = WorkflowManager(
        config=WorkflowManagerConfig(cycle_duration=10, maximum_batch_count=1)
    )
    with app.app_context():
        messages_to_delete, messages_to_keep = workflow_manager.process_batch()

    assert workflow_manager.metrics["events_processed"] == 3
    assert len(messages_to_delete) == 2
    assert len(messages_to_keep) == 1


def test_process_batch_with_empty_queue(workflow_sqs_queue, app, manager_config):
    with app.app_context():
        assert WorkflowManager(config=manager_config).process_batch() == ([], [])


def test_process_batch_runs_events_concurrently(workflow_sqs_queue, app, valid_message_body):
    """Verify process_batch dispatches each event to its own thread.

    A threading.Barrier with a short timeout deterministically distinguishes
    concurrent vs. sequential execution: if the handler ran sequentially the
    first thread would block forever (the others can't arrive at the barrier),
    so the barrier's timeout would fire and the test would fail.
    """
    sqs_client = get_sqs_client(workflow_sqs_queue)

    num_events = 3
    for _ in range(num_events):
        body = dict(valid_message_body)
        body["event_id"] = str(uuid.uuid4())
        sqs_client.send_message(body)

    barrier = threading.Barrier(num_events, timeout=5)

    def fake_handle_event(sqs_container):
        barrier.wait()
        return MgmtWorkflowEventProcessingResult.SUCCESS

    workflow_manager = WorkflowManager(
        config=WorkflowManagerConfig(cycle_duration=0, maximum_batch_count=1)
    )

    with (
        app.app_context(),
        patch("src.workflow.manager.workflow_manager.handle_event", fake_handle_event),
    ):
        messages_to_delete, messages_to_keep = workflow_manager.process_batch()

    assert len(messages_to_delete) == num_events
    assert len(messages_to_keep) == 0


def test_process_batch_event_timeout_keeps_message(workflow_sqs_queue, app, valid_message_body):
    """A handler that exceeds the per-event timeout has its message kept on the queue."""
    get_sqs_client(workflow_sqs_queue).send_message(valid_message_body)

    def slow_handle_event(sqs_container):
        # The handler just needs to still be running when future.result(timeout=0)
        # is called - any brief wait suffices. ThreadPoolExecutor waits for this
        # to finish on shutdown, so keep it short so the test stays fast.
        threading.Event().wait(0.05)
        return MgmtWorkflowEventProcessingResult.SUCCESS

    workflow_manager = WorkflowManager(
        config=WorkflowManagerConfig(
            cycle_duration=0,
            maximum_batch_count=1,
            event_processing_timeout_sec=0,
        )
    )

    with (
        app.app_context(),
        patch("src.workflow.manager.workflow_manager.handle_event", slow_handle_event),
    ):
        messages_to_delete, messages_to_keep = workflow_manager.process_batch()

    assert messages_to_delete == []
    assert len(messages_to_keep) == 1


####################
# handle_event
####################


def test_handle_event_success(app, db_session, enable_factory_create):
    user = MgmtUserFactory.create()
    event_id = uuid.uuid4()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    sqs_container = build_process_workflow_event(
        mgmt_workflow_id=workflow.mgmt_workflow_id,
        user=user,
        event_to_send="complete",
        event_id=event_id,
        put_history_event_in_session=False,
    )

    with app.app_context():
        result = handle_event(sqs_container)

    assert result == MgmtWorkflowEventProcessingResult.SUCCESS

    saved_history_event = db_session.scalar(
        select(MgmtWorkflowEventHistory).where(
            MgmtWorkflowEventHistory.mgmt_workflow_event_history_id == event_id
        )
    )
    assert saved_history_event is not None
    assert saved_history_event.is_successfully_processed is True
    # The history row is linked back to the workflow the event turned out to be for
    assert saved_history_event.mgmt_workflow_id == workflow.mgmt_workflow_id


def test_handle_event_retryable_error(app, enable_factory_create):
    user = MgmtUserFactory.create()

    # An unrecognized state raises UnexpectedStateError, which is retryable
    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state="not-a-valid-state",
    )

    sqs_container = build_process_workflow_event(
        mgmt_workflow_id=workflow.mgmt_workflow_id,
        user=user,
        event_to_send="complete",
        put_history_event_in_session=False,
    )

    with app.app_context():
        result = handle_event(sqs_container)

    assert result == MgmtWorkflowEventProcessingResult.RETRYABLE_ERROR


def test_handle_event_non_retryable_error(app, db_session, enable_factory_create):
    """A non-retryable error still persists the history row, flagged as failed."""
    event_id = uuid.uuid4()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    sqs_container = build_process_workflow_event(
        mgmt_workflow_id=workflow.mgmt_workflow_id,
        # No user means UserDoesNotExist, which is non-retryable
        user=None,
        event_to_send="complete",
        event_id=event_id,
        put_history_event_in_session=False,
    )

    with app.app_context():
        result = handle_event(sqs_container)

    assert result == MgmtWorkflowEventProcessingResult.NON_RETRYABLE_ERROR

    saved_history_event = db_session.scalar(
        select(MgmtWorkflowEventHistory).where(
            MgmtWorkflowEventHistory.mgmt_workflow_event_history_id == event_id,
            MgmtWorkflowEventHistory.is_successfully_processed.is_(False),
        )
    )
    assert saved_history_event is not None


@patch("src.workflow.manager.workflow_manager.EventHandler._pre_process_event")
def test_handle_event_general_error(mock_event_handler_preprocess, app, enable_factory_create):
    """Any other error is classified as a general error."""
    mock_event_handler_preprocess.side_effect = Exception("Unexpected error")

    user = MgmtUserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    sqs_container = build_process_workflow_event(
        mgmt_workflow_id=workflow.mgmt_workflow_id,
        user=user,
        event_to_send="complete",
        put_history_event_in_session=False,
    )

    with app.app_context():
        result = handle_event(sqs_container)

    assert result == MgmtWorkflowEventProcessingResult.GENERAL_ERROR
