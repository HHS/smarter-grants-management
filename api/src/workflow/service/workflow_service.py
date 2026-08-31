import logging
import uuid
from typing import Any

from sqlalchemy import select

from src.adapters import db
from src.db.models.resource_models import AbstractResourceTableMixin, Resource
from src.db.models.workflow_models import Workflow
from src.db.resource_lookup import get_resource_model
from src.workflow.base_state_machine import BaseStateMachine
from src.workflow.workflow_config import WorkflowConfig
from src.workflow.workflow_errors import (
    ConcurrentWorkflowError,
    EntityNotFound,
    ImplementationMissingError,
    InactiveWorkflowError,
    InvalidEntityForWorkflow,
    WorkflowDoesNotExistError,
)

logger = logging.getLogger(__name__)


def get_workflow_entity(
    db_session: db.Session,
    resource_id: uuid.UUID,
    config: WorkflowConfig,
) -> AbstractResourceTableMixin:
    """Get the entity a workflow is being attached to, by its resource ID.

    Handles validating that the resource exists, that its type is the one the
    workflow is configured for, and that we know which table backs that type.

    Expected usage:

        entity = get_workflow_entity(...)
        workflow = Workflow(..., resource_id=entity.get_resource_id())
    """
    log_extra: dict[str, Any] = {
        "workflow_type": config.workflow_type,
        "resource_id": resource_id,
        "expected_resource_type": config.resource_type,
    }

    resource = db_session.get(Resource, resource_id)
    if resource is None:
        logger.warning("Resource not found for workflow", extra=log_extra)
        raise EntityNotFound("Resource not found")

    log_extra["resource_type"] = resource.resource_type

    # The caller only sends a resource ID, so the type comes from the resource row
    # itself rather than being taken on trust from the event.
    if resource.resource_type != config.resource_type:
        logger.warning("Resource type does not match workflow configuration", extra=log_extra)
        raise InvalidEntityForWorkflow("Resource type does not match workflow configuration")

    # A resource type with no table behind it (opportunity, today) errors rather than
    # silently resolving to nothing.
    entity_cls = get_resource_model(resource.resource_type)
    if entity_cls is None:
        logger.warning("Resource type is not supported for workflow", extra=log_extra)
        raise ImplementationMissingError("Resource type is not supported for workflow")

    entity = db_session.get(entity_cls, resource_id)
    if entity is None:
        # Resource automation creates the resource row and the entity row together,
        # so a resource without its entity means something has gone wrong upstream.
        logger.error("Resource has no corresponding entity", extra=log_extra)
        raise EntityNotFound("Resource has no corresponding entity")

    return entity


def is_event_valid_for_workflow(
    event: str, state_machine: type[BaseStateMachine] | BaseStateMachine
) -> bool:
    """Get whether an event could be sent to a given workflow.

    Note that this does NOT say whether it's valid for the current
    state of the workflow, just that it's one of the possible events.
    """
    return event in state_machine.get_valid_events()


def get_and_validate_workflow(
    db_session: db.Session, workflow_id: uuid.UUID, log_extra: dict | None = None
) -> Workflow:
    """Fetch a workflow and error if it doesn't exist.

    Verifies:
    * The workflow exists
    * The workflow is_active and can receive events
    """
    if log_extra is None:
        log_extra = {"workflow_id": workflow_id}

    workflow = db_session.scalar(select(Workflow).where(Workflow.workflow_id == workflow_id))

    if workflow is None:
        logger.warning("Workflow does not exist - cannot process event", extra=log_extra)
        raise WorkflowDoesNotExistError("Workflow does not exist, cannot process events against it")

    if not workflow.is_active:
        logger.warning("Workflow is not active - cannot receive events", extra=log_extra)
        raise InactiveWorkflowError("Workflow is not active - cannot receive events")

    return workflow


def validate_no_concurrent_workflow(
    db_session: db.Session,
    resource_id: uuid.UUID,
    config: WorkflowConfig,
) -> None:
    """Validate that no active workflow of the given type already exists for the resource.

    If the workflow config allows concurrent workflows, this is a no-op.
    Otherwise, raises ConcurrentWorkflowError if an active workflow already exists.
    """
    if config.allow_concurrent_workflow_for_resource:
        return

    workflow_type = config.workflow_type

    existing_workflow = db_session.scalar(
        select(Workflow).where(
            Workflow.workflow_type == workflow_type,
            Workflow.resource_id == resource_id,
            Workflow.is_active.is_(True),
        )
    )

    if existing_workflow is not None:
        logger.warning(
            "An active workflow already exists for this resource",
            extra={
                "workflow_type": workflow_type,
                "resource_id": resource_id,
                "existing_workflow_id": existing_workflow.workflow_id,
            },
        )
        raise ConcurrentWorkflowError(
            "An active workflow of this type already exists for this resource"
        )
