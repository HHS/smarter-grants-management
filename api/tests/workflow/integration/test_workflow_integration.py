import uuid

import boto3
from grants_shared.adapters.aws.sqs_adapter import SQSClient
from sqlalchemy import select

from src.constants.lookup_constants import MgmtWorkflowEventType, MgmtWorkflowType
from src.db.models.workflow_models import MgmtWorkflow, MgmtWorkflowAudit, MgmtWorkflowEventHistory
from src.workflow.manager.workflow_manager import WorkflowManager, WorkflowManagerConfig
from src.workflow.state_machine.prototype_state_machine import PrototypeState
from tests.db.models.factories import MgmtUserFactory

#################################
#
# These tests verify the whole workflow loop hangs together:
# a message on the queue -> the manager -> the state machine -> an audit row.
#
# They don't aim to cover every branch (the per-module tests do that), just that
# the pieces connect. Once the workflow event API lands, the front of this can be
# an API call rather than a hand-built message.
#
#################################


def send_and_process(app, queue_url: str, payload: dict) -> None:
    """Put a message on the queue and run exactly one batch through the manager."""
    SQSClient(
        queue_url=queue_url, sqs_client=boto3.client("sqs", region_name="us-east-1")
    ).send_message(payload)

    config = WorkflowManagerConfig(cycle_duration=0, maximum_batch_count=1)
    with app.app_context():
        messages_to_delete, messages_to_keep = WorkflowManager(config=config).process_batch()

    assert len(messages_to_delete) == 1, "Expected the event to be processed successfully"
    assert len(messages_to_keep) == 0


def get_audits(db_session, mgmt_workflow_id) -> list[MgmtWorkflowAudit]:
    return list(
        db_session.execute(
            select(MgmtWorkflowAudit)
            .where(MgmtWorkflowAudit.mgmt_workflow_id == mgmt_workflow_id)
            .order_by(MgmtWorkflowAudit.created_at)
        ).scalars()
    )


def test_prototype_workflow_runs_from_start_to_end(
    app, db_session, enable_factory_create, program, workflow_user, workflow_sqs_queue
):
    """Start a prototype workflow off the queue and drive it to a final state."""
    user = MgmtUserFactory.create()
    db_session.commit()

    #####################
    # Start the workflow
    #####################
    start_event_id = uuid.uuid4()
    send_and_process(
        app,
        workflow_sqs_queue,
        {
            "event_id": start_event_id,
            "acting_mgmt_user_id": user.mgmt_user_id,
            "event_type": MgmtWorkflowEventType.START_WORKFLOW,
            "start_workflow_context": {
                "workflow_type": MgmtWorkflowType.PROTOTYPE_WORKFLOW,
                "mgmt_resource_id": program.get_resource_id(),
            },
        },
    )

    # The manager commits in its own session, so drop anything we have cached
    db_session.expire_all()

    workflow = db_session.scalar(
        select(MgmtWorkflow).where(MgmtWorkflow.mgmt_resource_id == program.get_resource_id())
    )
    assert workflow is not None
    assert workflow.workflow_type == MgmtWorkflowType.PROTOTYPE_WORKFLOW
    assert workflow.current_workflow_state == PrototypeState.IN_PROGRESS
    assert workflow.is_active is True

    audits = get_audits(db_session, workflow.mgmt_workflow_id)
    assert len(audits) == 1
    assert audits[0].transition_event == "Start workflow"
    assert audits[0].acting_mgmt_user_id == user.mgmt_user_id
    assert audits[0].mgmt_workflow_event_history_id == start_event_id

    #####################
    # Drive it to the end
    #####################
    complete_event_id = uuid.uuid4()
    send_and_process(
        app,
        workflow_sqs_queue,
        {
            "event_id": complete_event_id,
            "acting_mgmt_user_id": user.mgmt_user_id,
            "event_type": MgmtWorkflowEventType.PROCESS_WORKFLOW,
            "process_workflow_context": {
                "mgmt_workflow_id": workflow.mgmt_workflow_id,
                "event_to_send": "complete",
            },
        },
    )

    db_session.expire_all()

    assert workflow.current_workflow_state == PrototypeState.END
    # Reaching a final state deactivates the workflow
    assert workflow.is_active is False

    # Three transitions total: the start, the caller's `complete`, and the `finalize`
    # the state machine sent itself.
    audits = get_audits(db_session, workflow.mgmt_workflow_id)
    assert [audit.transition_event for audit in audits] == [
        "Start workflow",
        "Complete",
        "Finalize",
    ]
    assert [audit.acting_mgmt_user_id for audit in audits] == [
        user.mgmt_user_id,
        user.mgmt_user_id,
        # The automatic transition is attributed to the internal workflow user
        workflow_user.mgmt_user_id,
    ]

    # Both events are recorded, keyed on the event IDs from the messages, and linked
    # to the workflow they turned out to be for.
    history_events = list(
        db_session.execute(
            select(MgmtWorkflowEventHistory).where(
                MgmtWorkflowEventHistory.mgmt_workflow_id == workflow.mgmt_workflow_id
            )
        ).scalars()
    )
    assert {event.mgmt_workflow_event_history_id for event in history_events} == {
        start_event_id,
        complete_event_id,
    }
    assert all(event.is_successfully_processed for event in history_events)


def test_prototype_workflow_rejects_an_event_the_state_does_not_allow(
    app, db_session, enable_factory_create, program, workflow_user, workflow_sqs_queue
):
    """An event that isn't valid for the current state is a non-retryable error.

    The message comes off the queue (retrying wouldn't help) but the workflow is
    left untouched apart from the failed history row.
    """
    user = MgmtUserFactory.create()
    db_session.commit()

    send_and_process(
        app,
        workflow_sqs_queue,
        {
            "event_id": uuid.uuid4(),
            "acting_mgmt_user_id": user.mgmt_user_id,
            "event_type": MgmtWorkflowEventType.START_WORKFLOW,
            "start_workflow_context": {
                "workflow_type": MgmtWorkflowType.PROTOTYPE_WORKFLOW,
                "mgmt_resource_id": program.get_resource_id(),
            },
        },
    )
    db_session.expire_all()

    workflow = db_session.scalar(
        select(MgmtWorkflow).where(MgmtWorkflow.mgmt_resource_id == program.get_resource_id())
    )

    # `finalize` is a real event, just not from IN_PROGRESS
    bad_event_id = uuid.uuid4()
    send_and_process(
        app,
        workflow_sqs_queue,
        {
            "event_id": bad_event_id,
            "acting_mgmt_user_id": user.mgmt_user_id,
            "event_type": MgmtWorkflowEventType.PROCESS_WORKFLOW,
            "process_workflow_context": {
                "mgmt_workflow_id": workflow.mgmt_workflow_id,
                "event_to_send": "finalize",
            },
        },
    )
    db_session.expire_all()

    # The workflow didn't move
    assert workflow.current_workflow_state == PrototypeState.IN_PROGRESS
    assert workflow.is_active is True
    assert len(get_audits(db_session, workflow.mgmt_workflow_id)) == 1

    # The failed event is still recorded and flagged as unprocessed. It stays linked to
    # the workflow it was aimed at - the link is made before the event is validated,
    # which is what makes a rejected event traceable to its workflow.
    failed_event = db_session.scalar(
        select(MgmtWorkflowEventHistory).where(
            MgmtWorkflowEventHistory.mgmt_workflow_event_history_id == bad_event_id
        )
    )
    assert failed_event is not None
    assert failed_event.is_successfully_processed is False
    assert failed_event.mgmt_workflow_id == workflow.mgmt_workflow_id
