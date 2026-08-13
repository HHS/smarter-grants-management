from sqlalchemy import select

from src.constants.lookup_constants import WorkflowType
from src.db.models.workflow_models import WorkflowAudit
from src.workflow.handler.event_handler import EventHandler
from src.workflow.state_machine.prototype_state_machine import PrototypeState
from tests.db.models.factories import ProgramWorkflowFactory, UserFactory
from tests.workflow.state_machine.test_state_machines import BasicState
from tests.workflow.workflow_test_util import (
    build_process_workflow_event,
    build_start_workflow_event,
)


def _get_audits(db_session, workflow_id) -> list[WorkflowAudit]:
    return list(
        db_session.execute(
            select(WorkflowAudit)
            .where(WorkflowAudit.workflow_id == workflow_id)
            .order_by(WorkflowAudit.created_at)
        ).scalars()
    )


def test_workflow_audit_created_on_start_workflow(db_session, enable_factory_create, program):
    """Test that a workflow audit record is created when starting a workflow."""
    user = UserFactory.create()

    sqs_container = build_start_workflow_event(
        workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
    )

    state_machine = EventHandler(db_session, sqs_container).process()

    audit_records = _get_audits(db_session, state_machine.workflow.workflow_id)

    # Should have exactly one audit record for the start_workflow transition
    assert len(audit_records) == 1
    audit_record = audit_records[0]

    # Verify the audit record fields
    assert audit_record.workflow_id == state_machine.workflow.workflow_id
    assert audit_record.acting_user_id == user.user_id
    assert audit_record.transition_event == "Start workflow"
    assert audit_record.source_state == BasicState.START
    assert audit_record.target_state == BasicState.MIDDLE
    assert (
        audit_record.workflow_event_history_id
        == sqs_container.history_event.workflow_event_history_id
    )


def test_workflow_audit_created_on_process_workflow(db_session, enable_factory_create):
    """Test that a workflow audit record is created when processing a workflow event."""
    user = UserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state="middle",
    )

    sqs_container = build_process_workflow_event(
        workflow.workflow_id, user=user, event_to_send="middle_to_end"
    )

    EventHandler(db_session, sqs_container).process()

    audit_records = _get_audits(db_session, workflow.workflow_id)

    assert len(audit_records) == 1
    audit_record = audit_records[0]

    assert audit_record.workflow_id == workflow.workflow_id
    assert audit_record.acting_user_id == user.user_id
    assert audit_record.transition_event == "Middle to end"
    assert audit_record.source_state == "middle"
    assert audit_record.target_state == "end"
    assert (
        audit_record.workflow_event_history_id
        == sqs_container.history_event.workflow_event_history_id
    )


def test_workflow_audit_captures_metadata(db_session, enable_factory_create):
    """Test that workflow audit records capture metadata from the state machine event."""
    user = UserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state="middle",
    )

    test_metadata = {"test_key": "test_value", "another_key": 123}
    sqs_container = build_process_workflow_event(
        workflow.workflow_id,
        user=user,
        event_to_send="middle_to_end",
        metadata=test_metadata,
    )

    EventHandler(db_session, sqs_container).process()

    audit_record = db_session.execute(
        select(WorkflowAudit).where(WorkflowAudit.workflow_id == workflow.workflow_id)
    ).scalar_one()

    assert audit_record.audit_metadata == test_metadata


def test_workflow_audit_multiple_transitions(db_session, enable_factory_create, program):
    """Test that multiple audit records are created across multiple events."""
    user = UserFactory.create()

    sqs_container = build_start_workflow_event(
        workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
    )

    state_machine = EventHandler(db_session, sqs_container).process()
    workflow_id = state_machine.workflow.workflow_id

    sqs_container2 = build_process_workflow_event(
        workflow_id, user=user, event_to_send="middle_to_end"
    )
    EventHandler(db_session, sqs_container2).process()

    audit_records = _get_audits(db_session, workflow_id)

    assert len(audit_records) == 2

    assert audit_records[0].transition_event == "Start workflow"
    assert audit_records[0].source_state == "start"
    assert audit_records[0].target_state == "middle"

    assert audit_records[1].transition_event == "Middle to end"
    assert audit_records[1].source_state == "middle"
    assert audit_records[1].target_state == "end"


def test_workflow_audit_different_users(db_session, enable_factory_create, program):
    """Test that audit records correctly track different users performing actions."""
    user1 = UserFactory.create()
    user2 = UserFactory.create()

    sqs_container = build_start_workflow_event(
        workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
        user=user1,
        entity=program,
    )
    state_machine = EventHandler(db_session, sqs_container).process()
    workflow_id = state_machine.workflow.workflow_id

    sqs_container2 = build_process_workflow_event(
        workflow_id, user=user2, event_to_send="middle_to_end"
    )
    EventHandler(db_session, sqs_container2).process()

    audit_records = _get_audits(db_session, workflow_id)

    assert len(audit_records) == 2
    assert audit_records[0].acting_user_id == user1.user_id
    assert audit_records[1].acting_user_id == user2.user_id


def test_workflow_audit_automatic_transitions_use_system_user(
    db_session, enable_factory_create, workflow_user
):
    """Test that automatic transitions (via 'after' parameter) use the system user."""
    # The workflow_user fixture creates the system user and points the env var at it

    # A regular user who sends the event that kicks off the automatic transition
    regular_user = UserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    # `complete` transitions to FINALIZING and then the state machine sends `finalize`
    # on its own, so this one event produces two audit records:
    # 1. Complete (user-initiated) - regular_user
    # 2. Finalize (automatic via 'after') - the internal workflow user
    sqs_container = build_process_workflow_event(
        workflow.workflow_id, user=regular_user, event_to_send="complete"
    )

    EventHandler(db_session, sqs_container).process()
    db_session.commit()

    audit_records = _get_audits(db_session, workflow.workflow_id)

    assert len(audit_records) == 2

    assert audit_records[0].acting_user_id == regular_user.user_id
    assert audit_records[0].transition_event == "Complete"
    assert audit_records[0].source_state == PrototypeState.IN_PROGRESS
    assert audit_records[0].target_state == PrototypeState.FINALIZING

    # The automatic transition is attributed to the internal workflow user
    assert audit_records[1].acting_user_id == workflow_user.user_id
    assert audit_records[1].transition_event == "Finalize"
    assert audit_records[1].source_state == PrototypeState.FINALIZING
    assert audit_records[1].target_state == PrototypeState.END
