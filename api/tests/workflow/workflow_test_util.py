"""
This file contains various utilities for helping test workflows
including setting up data and validation.
"""

import json
import uuid
from typing import Any

from grants_shared.adapters import db

from src.constants.lookup_constants import (
    ExternalUserType,
    Privilege,
    ResourceType,
    WorkflowEventType,
    WorkflowType,
)
from src.db.models.resource_models import AbstractResourceTableMixin
from src.db.models.user_models import User
from src.db.models.workflow_models import WorkflowApproval
from src.workflow.base_state_machine import BaseStateMachine
from src.workflow.event.sqs_message_container import SqsMessageContainer
from src.workflow.event.workflow_event import (
    ProcessWorkflowEventContext,
    StartWorkflowEventContext,
    WorkflowEvent,
)
from src.workflow.handler.event_handler import EventHandler
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel
from src.workflow.state_persistence.program_persistence_model import ProgramPersistenceModel
from src.workflow.workflow_config import WorkflowConfig
from src.workflow.workflow_constants import WorkflowConstants
from tests.db.models.factories import (
    LinkExternalUserFactory,
    UserFactory,
    WorkflowEventHistoryFactory,
)
from tests.test_utils.auth_test_utils import setup_user_with_roles

####################
# Persistence models for resource types that have no real workflow yet.
#
# A workflow's resource type comes off its persistence model, so testing the engine
# against another resource type means defining a model for it.
####################


class PartnerTestPersistenceModel(BaseStatePersistenceModel):
    @classmethod
    def get_resource_type(cls) -> ResourceType:
        return ResourceType.PARTNER


class GrantorOrganizationTestPersistenceModel(BaseStatePersistenceModel):
    @classmethod
    def get_resource_type(cls) -> ResourceType:
        return ResourceType.GRANTOR_ORGANIZATION


class OpportunityTestPersistenceModel(BaseStatePersistenceModel):
    """A resource type that is valid but has no table in mgmt yet."""

    @classmethod
    def get_resource_type(cls) -> ResourceType:
        return ResourceType.OPPORTUNITY


def build_workflow_config(
    workflow_type: WorkflowType = WorkflowType.BASIC_TEST_WORKFLOW,
    persistence_model_cls: type[BaseStatePersistenceModel] = ProgramPersistenceModel,
    allow_concurrent_workflow_for_resource: bool = True,
) -> WorkflowConfig:
    """Build a workflow config"""

    return WorkflowConfig(
        workflow_type=workflow_type,
        persistence_model_cls=persistence_model_cls,
        allow_concurrent_workflow_for_resource=allow_concurrent_workflow_for_resource,
        approval_mapping={},
    )


def build_start_workflow_event(
    workflow_type: WorkflowType,
    user: User | None,
    entity: AbstractResourceTableMixin,
    exclude_start_workflow_context: bool = False,
    receipt_handle: str | None = None,
) -> SqsMessageContainer:
    """Build a start-workflow event for the given entity.

    Any resource-backed entity works here without special-casing - the event only
    carries the resource ID, which every such entity can hand over.
    """
    user_id = user.user_id if user else uuid.uuid4()

    if exclude_start_workflow_context:
        start_workflow_context = None
    else:
        start_workflow_context = StartWorkflowEventContext(
            workflow_type=workflow_type,
            resource_id=entity.get_resource_id(),
        )

    event = WorkflowEvent(
        event_id=uuid.uuid4(),
        acting_user_id=user_id,
        event_type=WorkflowEventType.START_WORKFLOW,
        start_workflow_context=start_workflow_context,
    )

    workflow_event_history = WorkflowEventHistoryFactory.create(
        workflow_event_history_id=event.event_id,
        event_data=json.loads(event.model_dump_json()),
        workflow_id=None,
        workflow=None,
    )

    if receipt_handle is None:
        # Make up a receipt handle if not passed in just so it's set
        receipt_handle = str(uuid.uuid4())

    return SqsMessageContainer(
        receipt_handle=receipt_handle, workflow_event=event, history_event=workflow_event_history
    )


def build_process_workflow_event(
    workflow_id: uuid.UUID,
    user: User | None,
    event_to_send: str,
    metadata: dict | None = None,
    exclude_process_workflow_context: bool = False,
    receipt_handle: str | None = None,
    event_id: uuid.UUID | None = None,
    put_history_event_in_session: bool = True,
) -> SqsMessageContainer:
    user_id = user.user_id if user else uuid.uuid4()

    if event_id is None:
        event_id = uuid.uuid4()

    if exclude_process_workflow_context:
        process_workflow_context = None
    else:
        process_workflow_context = ProcessWorkflowEventContext(
            workflow_id=workflow_id, event_to_send=event_to_send
        )

    event = WorkflowEvent(
        event_id=event_id,
        acting_user_id=user_id,
        event_type=WorkflowEventType.PROCESS_WORKFLOW,
        process_workflow_context=process_workflow_context,
        metadata=metadata,
    )

    # For most uses of this util, we want the history event to be
    # in the session, but for testing at the top-level of the workflow
    # logic, we want it detached like it would be there.
    event_history_params = dict(
        workflow_event_history_id=event.event_id,
        event_data=json.loads(event.model_dump_json()),
        is_successfully_processed=True,
        # Despite having the workflow, we don't attach it here
        # as that wouldn't be connected until the event handler processes it.
        workflow_id=None,
        workflow=None,
    )
    if put_history_event_in_session:
        workflow_event_history = WorkflowEventHistoryFactory.create(**event_history_params)
    else:
        workflow_event_history = WorkflowEventHistoryFactory.build(**event_history_params)

    if receipt_handle is None:
        # Make up a receipt handle if not passed in just so it's set
        receipt_handle = str(uuid.uuid4())

    return SqsMessageContainer(
        receipt_handle=receipt_handle, workflow_event=event, history_event=workflow_event_history
    )


def send_process_event(
    db_session: db.Session,
    event_to_send: str,
    workflow_id: uuid.UUID,
    user: User,
    expected_state: str,
    expected_is_active: bool = True,
    metadata: dict | None = None,
    approval_response_type: str | None = None,
    comment: str | None = None,
) -> BaseStateMachine:
    # approval_response_type/comment are just metadata fields, but they're passed
    # often enough by the approval tests to be worth their own parameters.
    if approval_response_type is not None or comment is not None:
        metadata = dict(metadata) if metadata else {}
        if approval_response_type is not None:
            metadata[WorkflowConstants.APPROVAL_RESPONSE_TYPE] = approval_response_type
        if comment is not None:
            metadata[WorkflowConstants.COMMENT] = comment

    sqs_container = build_process_workflow_event(
        workflow_id=workflow_id,
        user=user,
        event_to_send=event_to_send,
        metadata=metadata,
    )

    state_machine = EventHandler(db_session, sqs_container).process()
    assert (
        state_machine.workflow.current_workflow_state == expected_state
    ), f"Expected {expected_state} but got {state_machine.workflow.current_workflow_state}"
    assert state_machine.workflow.is_active == expected_is_active

    return state_machine


def create_approver(
    db_session: db.Session,
    resource: AbstractResourceTableMixin,
    privileges: list[Privilege],
) -> User:
    """Create a user with an email who holds the given privileges via a role on the resource.

    Pass the resource the workflow is attached to for a user who can approve under v1,
    or a resource above it in the hierarchy for one who deliberately cannot.
    """
    user = UserFactory.create()
    # Approval emails go to the login.gov email, and the recipient query only picks
    # up users that have one.
    LinkExternalUserFactory.create(user=user, external_user_type=ExternalUserType.LOGIN_GOV)

    setup_user_with_roles(db_session, resources=[resource], user=user, privileges=privileges)

    return user


def validate_approvals(
    state_machine: BaseStateMachine,
    expected_approvals: list[dict[str, Any] | WorkflowApproval],
) -> None:
    """Utility function to validate the approvals.

    For expected_approvals, pass in a list of dicts/WorkflowApproval objects of the format

    {
      "approving_user_id": user.user_id,
      "approval_type": ApprovalType.X,
      "is_still_valid": True/False
      "approval_response_type": ApprovalResponseType.X,
      "comment": "hello",
    }

    If a field is excluded, it will not be checked (useful to skip over dummy test data)
    The length of the approvals must however match in the order they were created.
    """

    approvals = sorted(
        state_machine.workflow.workflow_approvals, key=lambda approval: approval.created_at
    )
    assert len(approvals) == len(expected_approvals)

    for approval, expected_approval in zip(approvals, expected_approvals, strict=True):

        # If we passed in an approval object, just check the IDs
        # to verify it's in the right spot
        if isinstance(expected_approval, WorkflowApproval):
            assert approval.workflow_approval_id == expected_approval.workflow_approval_id
        else:
            # Only compare the fields that were passed in
            for field, value in expected_approval.items():
                assert (
                    getattr(approval, field) == value
                ), f"Values do not match for approval for field {field}"
