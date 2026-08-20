import uuid

import apiflask.exceptions
import pytest
from grants_shared.adapters import db
from grants_shared.adapters.aws.sqs_adapter import SQSClient

from src.auth.internal_resource import get_internal_resource
from src.constants.lookup_constants import (
    ApprovalResponseType,
    Privilege,
    WorkflowEventType,
    WorkflowType,
)
from src.services.workflows.ingest_workflow_event import ingest_workflow_event
from src.workflow.event.workflow_event import WorkflowEvent
from src.workflow.state_machine.prototype_state_machine import PrototypeState
from src.workflow.workflow_constants import WorkflowConstants
from tests.db.models.factories import (
    PartnerFactory,
    ProgramFactory,
    ProgramWorkflowFactory,
    UserFactory,
)
from tests.test_utils.auth_test_utils import setup_user_with_roles
from tests.workflow.workflow_test_util import create_approver

# The concurrency tests need a registered workflow that disallows concurrent workflows,
# which the prototype (the engine default) doesn't. Importing the test-only state
# machines registers BasicTestStateMachine, which does, along with the two that
# configure approvals.
from tests.workflow.state_machine.test_state_machines import (  # isort:skip
    ApprovalState,
    BasicState,
    LimitedApprovalResponseState,
)

#################################
#
# Tests for the validation the event API runs before putting an event on the queue.
#
# AuthZ is covered end-to-end at the route level, so apart from the section at the
# bottom every test here uses a user that passes it.
#
#################################


@pytest.fixture
def internal_send_user(db_session, enable_factory_create, internal_resource):
    return setup_user_with_roles(
        db_session,
        [get_internal_resource(db_session)],
        privileges=[Privilege.INTERNAL_WORKFLOW_EVENT_SEND],
    )


def get_queued_events(queue_url: str) -> list[WorkflowEvent]:
    messages = SQSClient(queue_url=queue_url).receive_messages(wait_time=0)
    return [WorkflowEvent.model_validate_json(message.body) for message in messages]


# ========================================
# Start Workflow Validation
# ========================================


def test_start_workflow_success(
    db_session: db.Session, enable_factory_create, internal_send_user, workflow_sqs_queue
):
    """A valid start event is queued with the resource ID and calling user attached."""
    program = ProgramFactory.create()

    event_id = ingest_workflow_event(
        db_session,
        {
            "event_type": WorkflowEventType.START_WORKFLOW,
            "start_workflow_context": {
                "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                "resource_id": program.get_resource_id(),
            },
        },
        internal_send_user,
    )

    queued = get_queued_events(workflow_sqs_queue)
    assert len(queued) == 1
    assert queued[0].event_id == event_id
    assert queued[0].acting_user_id == internal_send_user.user_id
    assert queued[0].event_type == WorkflowEventType.START_WORKFLOW
    assert queued[0].start_workflow_context.workflow_type == WorkflowType.PROTOTYPE_WORKFLOW
    assert queued[0].start_workflow_context.resource_id == program.get_resource_id()


def test_start_workflow_resource_not_found_404(
    db_session: db.Session, internal_send_user, workflow_sqs_queue
):
    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        ingest_workflow_event(
            db_session,
            {
                "event_type": WorkflowEventType.START_WORKFLOW,
                "start_workflow_context": {
                    "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                    "resource_id": uuid.uuid4(),
                },
            },
            internal_send_user,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "The specified resource was not found"
    assert get_queued_events(workflow_sqs_queue) == []


def test_start_workflow_resource_type_mismatch_422(
    db_session: db.Session, enable_factory_create, internal_send_user, workflow_sqs_queue
):
    """A real resource of the wrong type for the workflow is a 422.

    The prototype workflow attaches to programs - a partner is a perfectly valid
    resource, just not one this workflow accepts. Note the caller never sends a
    resource type; it's read off the resource row and compared to the config.
    """
    partner = PartnerFactory.create()

    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        ingest_workflow_event(
            db_session,
            {
                "event_type": WorkflowEventType.START_WORKFLOW,
                "start_workflow_context": {
                    "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                    "resource_id": partner.get_resource_id(),
                },
            },
            internal_send_user,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "The provided entity is not valid for this workflow type"
    assert get_queued_events(workflow_sqs_queue) == []


def test_start_workflow_concurrent_workflow_422(
    db_session: db.Session, enable_factory_create, internal_send_user, workflow_sqs_queue
):
    """An active workflow of the same type for the resource blocks starting another."""
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=BasicState.MIDDLE,
        is_active=True,
    )

    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        ingest_workflow_event(
            db_session,
            {
                "event_type": WorkflowEventType.START_WORKFLOW,
                "start_workflow_context": {
                    "workflow_type": WorkflowType.BASIC_TEST_WORKFLOW,
                    "resource_id": workflow.resource_id,
                },
            },
            internal_send_user,
        )

    assert exc_info.value.status_code == 422
    assert (
        exc_info.value.message == "An active workflow of this type already exists for this entity"
    )
    assert get_queued_events(workflow_sqs_queue) == []


# ========================================
# Process Workflow Validation
# ========================================


def test_process_workflow_success(
    db_session: db.Session, enable_factory_create, internal_send_user, workflow_sqs_queue
):
    """A valid process event is queued with the workflow ID and event attached."""
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    event_id = ingest_workflow_event(
        db_session,
        {
            "event_type": WorkflowEventType.PROCESS_WORKFLOW,
            "process_workflow_context": {
                "workflow_id": workflow.workflow_id,
                "event_to_send": "complete",
            },
        },
        internal_send_user,
    )

    queued = get_queued_events(workflow_sqs_queue)
    assert len(queued) == 1
    assert queued[0].event_id == event_id
    assert queued[0].process_workflow_context.workflow_id == workflow.workflow_id
    assert queued[0].process_workflow_context.event_to_send == "complete"


def test_process_workflow_does_not_exist_404(
    db_session: db.Session, internal_send_user, workflow_sqs_queue
):
    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        ingest_workflow_event(
            db_session,
            {
                "event_type": WorkflowEventType.PROCESS_WORKFLOW,
                "process_workflow_context": {
                    "workflow_id": uuid.uuid4(),
                    "event_to_send": "complete",
                },
            },
            internal_send_user,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "The specified workflow was not found"
    assert get_queued_events(workflow_sqs_queue) == []


def test_process_workflow_inactive_422(
    db_session: db.Session, enable_factory_create, internal_send_user, workflow_sqs_queue
):
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.END,
        is_active=False,
    )

    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        ingest_workflow_event(
            db_session,
            {
                "event_type": WorkflowEventType.PROCESS_WORKFLOW,
                "process_workflow_context": {
                    "workflow_id": workflow.workflow_id,
                    "event_to_send": "complete",
                },
            },
            internal_send_user,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "This workflow is not currently active"
    assert get_queued_events(workflow_sqs_queue) == []


def test_process_workflow_event_not_on_state_machine_422(
    db_session: db.Session, enable_factory_create, internal_send_user, workflow_sqs_queue
):
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        ingest_workflow_event(
            db_session,
            {
                "event_type": WorkflowEventType.PROCESS_WORKFLOW,
                "process_workflow_context": {
                    "workflow_id": workflow.workflow_id,
                    "event_to_send": "not_a_real_event",
                },
            },
            internal_send_user,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "The specified event is not valid for this workflow"
    assert get_queued_events(workflow_sqs_queue) == []


def test_process_workflow_event_wrong_for_current_state_is_still_queued(
    db_session: db.Session, enable_factory_create, internal_send_user, workflow_sqs_queue
):
    """A real event that the current state doesn't allow still gets queued.

    Deliberate, and worth pinning: the API only checks the event exists on the state
    machine at all. Whether it's legal from the current state is the engine's call when
    it processes the message, where it becomes a non-retryable error.
    """
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    ingest_workflow_event(
        db_session,
        {
            "event_type": WorkflowEventType.PROCESS_WORKFLOW,
            "process_workflow_context": {
                # `finalize` is a real event, just not one IN_PROGRESS allows
                "workflow_id": workflow.workflow_id,
                "event_to_send": "finalize",
            },
        },
        internal_send_user,
    )

    assert len(get_queued_events(workflow_sqs_queue)) == 1


# ========================================
# Approval Event Validation
# ========================================


@pytest.fixture
def approval_workflow(enable_factory_create):
    """A workflow sitting in the state its primary approval is given from."""
    return ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW,
        current_workflow_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
    )


def send_primary_approval(db_session, workflow, user, metadata=None):
    return ingest_workflow_event(
        db_session,
        {
            "event_type": WorkflowEventType.PROCESS_WORKFLOW,
            "process_workflow_context": {
                "workflow_id": workflow.workflow_id,
                "event_to_send": "receive_primary_approval",
            },
            "metadata": metadata if metadata is not None else {},
        },
        user,
    )


def test_approval_event_missing_response_type_422(
    db_session: db.Session, internal_send_user, approval_workflow, workflow_sqs_queue
):
    """An approval event has to say what the response was.

    The state machine branches on the response type, so an event without one would be
    a message the engine can't act on. Catching it here keeps it off the queue.
    """
    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        send_primary_approval(db_session, approval_workflow, internal_send_user)

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Approval response type not found in metadata"
    assert get_queued_events(workflow_sqs_queue) == []


def test_approval_event_unrecognized_response_type_422(
    db_session: db.Session, internal_send_user, approval_workflow, workflow_sqs_queue
):
    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        send_primary_approval(
            db_session,
            approval_workflow,
            internal_send_user,
            metadata={WorkflowConstants.APPROVAL_RESPONSE_TYPE: "not_a_response_type"},
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Approval response type is not a valid value"
    assert get_queued_events(workflow_sqs_queue) == []


def test_approval_event_response_type_disallowed_by_config_422(
    db_session: db.Session, enable_factory_create, internal_send_user, workflow_sqs_queue
):
    """A response type the approval's configuration doesn't allow is rejected.

    `declined` is a real transition on this state machine, so the event itself passes
    validation - it's the approval config that narrows which responses are acceptable.
    """
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.LIMITED_APPROVAL_TEST_WORKFLOW,
        current_workflow_state=LimitedApprovalResponseState.PENDING_PRIMARY_APPROVAL,
    )

    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        send_primary_approval(
            db_session,
            workflow,
            internal_send_user,
            metadata={WorkflowConstants.APPROVAL_RESPONSE_TYPE: ApprovalResponseType.DECLINED},
        )

    assert exc_info.value.status_code == 422
    assert (
        exc_info.value.message
        == "Approval response type is not allowed for this approval configuration."
    )
    assert get_queued_events(workflow_sqs_queue) == []


def test_approval_event_with_valid_response_type_is_queued(
    db_session: db.Session, internal_send_user, approval_workflow, workflow_sqs_queue
):
    """The metadata rides along on the queued event for the engine to act on."""
    send_primary_approval(
        db_session,
        approval_workflow,
        internal_send_user,
        metadata={WorkflowConstants.APPROVAL_RESPONSE_TYPE: ApprovalResponseType.APPROVED},
    )

    queued = get_queued_events(workflow_sqs_queue)
    assert len(queued) == 1
    assert queued[0].metadata == {
        WorkflowConstants.APPROVAL_RESPONSE_TYPE: ApprovalResponseType.APPROVED
    }


def test_non_approval_event_ignores_missing_response_type(
    db_session: db.Session, enable_factory_create, internal_send_user, workflow_sqs_queue
):
    """Only events in the workflow's approval mapping get the metadata check."""
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW,
        current_workflow_state=ApprovalState.MIDDLE,
    )

    ingest_workflow_event(
        db_session,
        {
            "event_type": WorkflowEventType.PROCESS_WORKFLOW,
            "process_workflow_context": {
                "workflow_id": workflow.workflow_id,
                "event_to_send": "middle_to_end",
            },
        },
        internal_send_user,
    )

    assert len(get_queued_events(workflow_sqs_queue)) == 1


# ========================================
# AuthZ
# ========================================


def test_user_without_internal_privilege_403(
    db_session: db.Session, enable_factory_create, internal_resource, workflow_sqs_queue
):
    """Start events stay internal-only.

    An approver's way in is tied to the approval an event represents, and a start
    event has no workflow to approve against - so there's nothing for a non-internal
    user to qualify under here.
    """
    program = ProgramFactory.create()
    user = UserFactory.create()

    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        ingest_workflow_event(
            db_session,
            {
                "event_type": WorkflowEventType.START_WORKFLOW,
                "start_workflow_context": {
                    "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                    "resource_id": program.get_resource_id(),
                },
            },
            user,
        )

    assert exc_info.value.status_code == 403
    assert get_queued_events(workflow_sqs_queue) == []


def test_approver_can_send_their_approval_event(
    db_session: db.Session, internal_resource, approval_workflow, workflow_sqs_queue
):
    """An approver sends the event their approval represents without the internal privilege.

    The privilege sits on the grant office rather than the program because users are
    never attached to a program resource directly.
    """
    program = approval_workflow.resource.concrete_resource
    approver = create_approver(
        db_session, program.grant_office, privileges=[Privilege.UPDATE_PROGRAM]
    )

    send_primary_approval(
        db_session,
        approval_workflow,
        approver,
        metadata={WorkflowConstants.APPROVAL_RESPONSE_TYPE: ApprovalResponseType.APPROVED},
    )

    queued = get_queued_events(workflow_sqs_queue)
    assert len(queued) == 1
    assert queued[0].acting_user_id == approver.user_id


def test_user_who_cannot_do_the_approval_403(
    db_session: db.Session, internal_resource, approval_workflow, workflow_sqs_queue
):
    """Holding some privilege on the resource isn't enough - it has to be the approval's.

    The primary approval requires UPDATE_PROGRAM; this user only has VIEW_PROGRAM,
    which qualifies them for the secondary approval and nothing else.
    """
    program = approval_workflow.resource.concrete_resource
    user = create_approver(db_session, program.grant_office, privileges=[Privilege.VIEW_PROGRAM])

    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        send_primary_approval(
            db_session,
            approval_workflow,
            user,
            metadata={WorkflowConstants.APPROVAL_RESPONSE_TYPE: ApprovalResponseType.APPROVED},
        )

    assert exc_info.value.status_code == 403
    assert get_queued_events(workflow_sqs_queue) == []


def test_approver_cannot_send_a_non_approval_event_403(
    db_session: db.Session, enable_factory_create, internal_resource, workflow_sqs_queue
):
    """An approver's access is scoped to approval events, not the whole workflow.

    `middle_to_end` is a perfectly valid event, just not one in the approval mapping,
    so there's no approval for the user to qualify under.
    """
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW,
        current_workflow_state=ApprovalState.MIDDLE,
    )
    program = workflow.resource.concrete_resource
    approver = create_approver(
        db_session, program.grant_office, privileges=[Privilege.UPDATE_PROGRAM]
    )

    with pytest.raises(apiflask.exceptions.HTTPError) as exc_info:
        ingest_workflow_event(
            db_session,
            {
                "event_type": WorkflowEventType.PROCESS_WORKFLOW,
                "process_workflow_context": {
                    "workflow_id": workflow.workflow_id,
                    "event_to_send": "middle_to_end",
                },
            },
            approver,
        )

    assert exc_info.value.status_code == 403
    assert get_queued_events(workflow_sqs_queue) == []
