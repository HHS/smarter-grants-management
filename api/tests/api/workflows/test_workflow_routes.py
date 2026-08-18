import uuid

import pytest
from grants_shared.adapters.aws.sqs_adapter import SQSClient

from src.auth.api_jwt_auth import create_jwt_for_user
from src.auth.internal_resource import get_internal_resource
from src.constants.lookup_constants import (
    ApprovalResponseType,
    Privilege,
    WorkflowEventType,
    WorkflowType,
)
from src.workflow.event.workflow_event import WorkflowEvent
from src.workflow.state_machine.prototype_state_machine import PrototypeState
from src.workflow.workflow_constants import WorkflowConstants
from tests.db.models.factories import (
    ProgramFactory,
    ProgramWorkflowFactory,
    UserApiKeyFactory,
    UserFactory,
)
from tests.test_utils.auth_test_utils import setup_user_with_roles
from tests.workflow.workflow_test_util import create_approver

# Importing the test-only state machines registers ApprovalTestStateMachine, the only
# registered workflow that configures approvals.
from tests.workflow.state_machine.test_state_machines import ApprovalState  # isort:skip

#################################
#
# Tests for PUT /v1/workflows/events.
#
# The detailed validation cases live in
# tests/services/workflows/test_ingest_workflow_event.py - these cover the route
# itself: auth, the request schema, and the response.
#
#################################


####################################
# Fixtures
####################################


@pytest.fixture
def internal_send_user(db_session, enable_factory_create, internal_resource):
    """A user holding the internal workflow-send privilege on the internal resource."""
    return setup_user_with_roles(
        db_session,
        [get_internal_resource(db_session)],
        privileges=[Privilege.INTERNAL_WORKFLOW_EVENT_SEND],
    )


@pytest.fixture
def internal_send_user_jwt(db_session, internal_send_user):
    token, _ = create_jwt_for_user(internal_send_user, db_session)
    db_session.commit()
    return token


@pytest.fixture
def internal_send_user_api_key(db_session, internal_send_user):
    api_key = UserApiKeyFactory.create(user=internal_send_user)
    db_session.commit()
    return api_key.key_id


def put_event(client, payload: dict, headers: dict | None = None):
    return client.put("/v1/workflows/events", json=payload, headers=headers or {})


def get_queued_events(queue_url: str) -> list[WorkflowEvent]:
    messages = SQSClient(queue_url=queue_url).receive_messages(wait_time=0)
    return [WorkflowEvent.model_validate_json(message.body) for message in messages]


####################################
# Happy Path
####################################


def test_put_workflow_event_start_workflow_200(
    client,
    db_session,
    enable_factory_create,
    internal_send_user,
    internal_send_user_jwt,
    workflow_sqs_queue,
):
    """A valid start event is accepted and lands on the workflow queue."""
    program = ProgramFactory.create()
    db_session.commit()

    response = put_event(
        client,
        {
            "event_type": WorkflowEventType.START_WORKFLOW,
            "start_workflow_context": {
                "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                "resource_id": str(program.get_resource_id()),
            },
        },
        {"X-MGMT-Token": internal_send_user_jwt},
    )

    assert response.status_code == 200
    assert response.json["message"] == "Event received"
    assert "event_id" in response.json["data"]

    queued = get_queued_events(workflow_sqs_queue)
    assert len(queued) == 1
    assert str(queued[0].event_id) == response.json["data"]["event_id"]
    assert queued[0].acting_user_id == internal_send_user.user_id
    assert queued[0].event_type == WorkflowEventType.START_WORKFLOW
    assert queued[0].start_workflow_context.workflow_type == WorkflowType.PROTOTYPE_WORKFLOW
    assert queued[0].start_workflow_context.resource_id == program.get_resource_id()


def test_put_workflow_event_process_workflow_200(
    client, db_session, enable_factory_create, internal_send_user_jwt, workflow_sqs_queue
):
    """A valid process event is accepted and lands on the workflow queue."""
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )
    db_session.commit()

    response = put_event(
        client,
        {
            "event_type": WorkflowEventType.PROCESS_WORKFLOW,
            "process_workflow_context": {
                "workflow_id": str(workflow.workflow_id),
                "event_to_send": "complete",
            },
            "metadata": {"comment": "looks good"},
        },
        {"X-MGMT-Token": internal_send_user_jwt},
    )

    assert response.status_code == 200

    queued = get_queued_events(workflow_sqs_queue)
    assert len(queued) == 1
    assert queued[0].process_workflow_context.workflow_id == workflow.workflow_id
    assert queued[0].process_workflow_context.event_to_send == "complete"
    assert queued[0].metadata == {"comment": "looks good"}


def test_put_workflow_event_api_key_auth_200(
    client, db_session, enable_factory_create, internal_send_user_api_key, workflow_sqs_queue
):
    """The endpoint accepts an API key as well as a JWT."""
    program = ProgramFactory.create()
    db_session.commit()

    response = put_event(
        client,
        {
            "event_type": WorkflowEventType.START_WORKFLOW,
            "start_workflow_context": {
                "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                "resource_id": str(program.get_resource_id()),
            },
        },
        {"X-API-Key": internal_send_user_api_key},
    )

    assert response.status_code == 200
    assert len(get_queued_events(workflow_sqs_queue)) == 1


####################################
# AuthN / AuthZ
####################################


def test_put_workflow_event_no_token_401(client, workflow_sqs_queue):
    response = put_event(
        client,
        {
            "event_type": WorkflowEventType.START_WORKFLOW,
            "start_workflow_context": {
                "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                "resource_id": str(uuid.uuid4()),
            },
        },
    )

    assert response.status_code == 401
    assert get_queued_events(workflow_sqs_queue) == []


def test_put_workflow_event_invalid_jwt_401(client, workflow_sqs_queue):
    response = put_event(
        client,
        {
            "event_type": WorkflowEventType.START_WORKFLOW,
            "start_workflow_context": {
                "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                "resource_id": str(uuid.uuid4()),
            },
        },
        {"X-MGMT-Token": "not-a-real-token"},
    )

    assert response.status_code == 401
    assert get_queued_events(workflow_sqs_queue) == []


def test_put_workflow_event_invalid_api_key_401(client, workflow_sqs_queue):
    response = put_event(
        client,
        {
            "event_type": WorkflowEventType.START_WORKFLOW,
            "start_workflow_context": {
                "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                "resource_id": str(uuid.uuid4()),
            },
        },
        {"X-API-Key": "not-a-real-key"},
    )

    assert response.status_code == 401
    assert get_queued_events(workflow_sqs_queue) == []


def test_put_workflow_event_approver_200(
    client, db_session, enable_factory_create, internal_resource, workflow_sqs_queue
):
    """An approver sends their approval event without holding the internal privilege.

    The other way through authZ, exercised over the real auth stack rather than by
    calling the service directly.
    """
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW,
        current_workflow_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
    )
    approver = create_approver(
        db_session,
        workflow.resource.concrete_resource.grant_office,
        privileges=[Privilege.UPDATE_PROGRAM],
    )
    token, _ = create_jwt_for_user(approver, db_session)
    db_session.commit()

    response = put_event(
        client,
        {
            "event_type": WorkflowEventType.PROCESS_WORKFLOW,
            "process_workflow_context": {
                "workflow_id": str(workflow.workflow_id),
                "event_to_send": "receive_primary_approval",
            },
            "metadata": {
                WorkflowConstants.APPROVAL_RESPONSE_TYPE: ApprovalResponseType.APPROVED,
            },
        },
        {"X-MGMT-Token": token},
    )

    assert response.status_code == 200, response.json

    queued = get_queued_events(workflow_sqs_queue)
    assert len(queued) == 1
    assert queued[0].acting_user_id == approver.user_id


def test_put_workflow_event_authenticated_without_privilege_403(
    client, db_session, enable_factory_create, internal_resource, workflow_sqs_queue
):
    """An authenticated user without the internal privilege is refused."""
    program = ProgramFactory.create()
    user = UserFactory.create()
    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()

    response = put_event(
        client,
        {
            "event_type": WorkflowEventType.START_WORKFLOW,
            "start_workflow_context": {
                "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                "resource_id": str(program.get_resource_id()),
            },
        },
        {"X-MGMT-Token": token},
    )

    assert response.status_code == 403
    assert response.json["message"] == "Forbidden"
    assert get_queued_events(workflow_sqs_queue) == []


####################################
# Request Validation
####################################


@pytest.mark.parametrize(
    "payload,expected_error_field",
    [
        # start_workflow with no start context
        (
            {"event_type": WorkflowEventType.START_WORKFLOW},
            "start_workflow_context",
        ),
        # process_workflow with no process context
        (
            {"event_type": WorkflowEventType.PROCESS_WORKFLOW},
            "process_workflow_context",
        ),
        # start_workflow carrying the wrong context
        (
            {
                "event_type": WorkflowEventType.START_WORKFLOW,
                "start_workflow_context": {
                    "workflow_type": WorkflowType.PROTOTYPE_WORKFLOW,
                    "resource_id": "b3e1a3f0-0f4c-4b1c-9c2a-3f6b0a1d2e3f",
                },
                "process_workflow_context": {
                    "workflow_id": "b3e1a3f0-0f4c-4b1c-9c2a-3f6b0a1d2e3f",
                    "event_to_send": "complete",
                },
            },
            "process_workflow_context",
        ),
        # No event type at all
        ({}, "event_type"),
        # Unrecognized event type
        ({"event_type": "not_an_event_type"}, "event_type"),
        # Start context missing its resource ID
        (
            {
                "event_type": WorkflowEventType.START_WORKFLOW,
                "start_workflow_context": {"workflow_type": WorkflowType.PROTOTYPE_WORKFLOW},
            },
            "start_workflow_context.resource_id",
        ),
        # Empty event_to_send
        (
            {
                "event_type": WorkflowEventType.PROCESS_WORKFLOW,
                "process_workflow_context": {
                    "workflow_id": "b3e1a3f0-0f4c-4b1c-9c2a-3f6b0a1d2e3f",
                    "event_to_send": "",
                },
            },
            "process_workflow_context.event_to_send",
        ),
    ],
)
def test_put_workflow_event_request_validation_422(
    client, internal_send_user_jwt, workflow_sqs_queue, payload, expected_error_field
):
    """Malformed requests are rejected by the schema before anything is queued."""
    response = put_event(client, payload, {"X-MGMT-Token": internal_send_user_jwt})

    assert response.status_code == 422
    error_fields = {error["field"] for error in response.json["errors"]}
    assert expected_error_field in error_fields
    assert get_queued_events(workflow_sqs_queue) == []
