"""
This file contains various utilities for helping test workflows
including setting up data and validation.
"""

import json
import uuid

from grants_shared.adapters import db

from src.constants.lookup_constants import MgmtResourceType, MgmtWorkflowEventType, MgmtWorkflowType
from src.db.models.resource_models import AbstractResourceTableMixin
from src.db.models.user_models import MgmtUser
from src.workflow.base_state_machine import BaseStateMachine
from src.workflow.event.sqs_message_container import SqsMessageContainer
from src.workflow.event.workflow_event import (
    ProcessWorkflowEventContext,
    StartWorkflowEventContext,
    WorkflowEvent,
)
from src.workflow.handler.event_handler import EventHandler
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel
from src.workflow.workflow_config import WorkflowConfig
from tests.db.models.factories import MgmtWorkflowEventHistoryFactory


def build_workflow_config(
    workflow_type: MgmtWorkflowType = MgmtWorkflowType.BASIC_TEST_WORKFLOW,
    persistence_model_cls: type[BaseStatePersistenceModel] = BaseStatePersistenceModel,
    resource_type: MgmtResourceType = MgmtResourceType.PROGRAM,
    allow_concurrent_workflow_for_resource: bool = True,
) -> WorkflowConfig:
    """Build a workflow config"""

    return WorkflowConfig(
        workflow_type=workflow_type,
        persistence_model_cls=persistence_model_cls,
        resource_type=resource_type,
        allow_concurrent_workflow_for_resource=allow_concurrent_workflow_for_resource,
        approval_mapping={},
    )


def build_start_workflow_event(
    workflow_type: MgmtWorkflowType,
    user: MgmtUser | None,
    entity: AbstractResourceTableMixin,
    exclude_start_workflow_context: bool = False,
    receipt_handle: str | None = None,
) -> SqsMessageContainer:
    """Build a start-workflow event for the given entity.

    Any resource-backed entity works here without special-casing - the event only
    carries the resource ID, which every such entity can hand over.
    """
    user_id = user.mgmt_user_id if user else uuid.uuid4()

    if exclude_start_workflow_context:
        start_workflow_context = None
    else:
        start_workflow_context = StartWorkflowEventContext(
            workflow_type=workflow_type,
            mgmt_resource_id=entity.get_resource_id(),
        )

    event = WorkflowEvent(
        event_id=uuid.uuid4(),
        acting_mgmt_user_id=user_id,
        event_type=MgmtWorkflowEventType.START_WORKFLOW,
        start_workflow_context=start_workflow_context,
    )

    workflow_event_history = MgmtWorkflowEventHistoryFactory.create(
        mgmt_workflow_event_history_id=event.event_id,
        event_data=json.loads(event.model_dump_json()),
        mgmt_workflow_id=None,
        workflow=None,
    )

    if receipt_handle is None:
        # Make up a receipt handle if not passed in just so it's set
        receipt_handle = str(uuid.uuid4())

    return SqsMessageContainer(
        receipt_handle=receipt_handle, workflow_event=event, history_event=workflow_event_history
    )


def build_process_workflow_event(
    mgmt_workflow_id: uuid.UUID,
    user: MgmtUser | None,
    event_to_send: str,
    metadata: dict | None = None,
    exclude_process_workflow_context: bool = False,
    receipt_handle: str | None = None,
    event_id: uuid.UUID | None = None,
    put_history_event_in_session: bool = True,
) -> SqsMessageContainer:
    user_id = user.mgmt_user_id if user else uuid.uuid4()

    if event_id is None:
        event_id = uuid.uuid4()

    if exclude_process_workflow_context:
        process_workflow_context = None
    else:
        process_workflow_context = ProcessWorkflowEventContext(
            mgmt_workflow_id=mgmt_workflow_id, event_to_send=event_to_send
        )

    event = WorkflowEvent(
        event_id=event_id,
        acting_mgmt_user_id=user_id,
        event_type=MgmtWorkflowEventType.PROCESS_WORKFLOW,
        process_workflow_context=process_workflow_context,
        metadata=metadata,
    )

    # For most uses of this util, we want the history event to be
    # in the session, but for testing at the top-level of the workflow
    # logic, we want it detached like it would be there.
    event_history_params = dict(
        mgmt_workflow_event_history_id=event.event_id,
        event_data=json.loads(event.model_dump_json()),
        is_successfully_processed=True,
        # Despite having the workflow, we don't attach it here
        # as that wouldn't be connected until the event handler processes it.
        mgmt_workflow_id=None,
        workflow=None,
    )
    if put_history_event_in_session:
        workflow_event_history = MgmtWorkflowEventHistoryFactory.create(**event_history_params)
    else:
        workflow_event_history = MgmtWorkflowEventHistoryFactory.build(**event_history_params)

    if receipt_handle is None:
        # Make up a receipt handle if not passed in just so it's set
        receipt_handle = str(uuid.uuid4())

    return SqsMessageContainer(
        receipt_handle=receipt_handle, workflow_event=event, history_event=workflow_event_history
    )


def send_process_event(
    db_session: db.Session,
    event_to_send: str,
    mgmt_workflow_id: uuid.UUID,
    user: MgmtUser,
    expected_state: str,
    expected_is_active: bool = True,
    metadata: dict | None = None,
) -> BaseStateMachine:
    sqs_container = build_process_workflow_event(
        mgmt_workflow_id=mgmt_workflow_id,
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
