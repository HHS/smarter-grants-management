import dataclasses
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import (
    VIEW_PRIVILEGE_FOR_RESOURCE_TYPE,
    ApprovalResponseType,
    ApprovalType,
    Privilege,
    ResourceType,
    WorkflowType,
)
from src.db.models.user_models import User
from src.db.models.workflow_models import (
    Workflow,
    WorkflowApproval,
    WorkflowAudit,
    WorkflowEventHistory,
)
from src.workflow.base_state_machine import BaseStateMachine
from src.workflow.registry.workflow_registry import WorkflowRegistry
from src.workflow.service.approval_service import get_approver_query
from src.workflow.workflow_config import WorkflowConfig

logger = logging.getLogger(__name__)


####################################
# Response objects
#
# The response is a reshaped view of the data model rather than a direct dump of it,
# so it gets built explicitly here instead of the schema reaching through relationships.
####################################


@dataclasses.dataclass
class UserRef:
    user_id: uuid.UUID
    email: str | None


@dataclasses.dataclass
class WorkflowEventRef:
    event_id: uuid.UUID
    sent_at: datetime


@dataclasses.dataclass
class AuditEventRef:
    workflow_audit_id: uuid.UUID
    acting_user: UserRef
    transition_event: str
    source_state: str
    target_state: str
    event: WorkflowEventRef
    audit_metadata: dict | None
    created_at: datetime


@dataclasses.dataclass
class ApprovalRef:
    workflow_approval_id: uuid.UUID
    approving_user: UserRef
    event_id: uuid.UUID
    is_still_valid: bool
    comment: str | None
    approval_type: ApprovalType
    approval_response_type: ApprovalResponseType
    created_at: datetime


@dataclasses.dataclass
class ApprovalConfigEntry:
    approval_type: ApprovalType
    required_privileges: list[Privilege]
    allowed_approval_response_types: set[ApprovalResponseType]
    possible_users: list[UserRef]


@dataclasses.dataclass
class WorkflowDetail:
    workflow_id: uuid.UUID
    workflow_type: WorkflowType
    current_workflow_state: str
    is_active: bool
    resource_id: uuid.UUID
    resource_type: ResourceType
    created_at: datetime
    updated_at: datetime
    workflow_approvals: list[ApprovalRef]
    workflow_approval_config: dict[str, ApprovalConfigEntry]
    valid_events: list[str]


def _to_user_ref(user: User) -> UserRef:
    return UserRef(user_id=user.user_id, email=user.email)


def _to_audit_event_ref(audit: WorkflowAudit) -> AuditEventRef:
    return AuditEventRef(
        workflow_audit_id=audit.workflow_audit_id,
        acting_user=_to_user_ref(audit.acting_user),
        transition_event=audit.transition_event,
        source_state=audit.source_state,
        target_state=audit.target_state,
        event=WorkflowEventRef(
            event_id=audit.event.workflow_event_history_id, sent_at=audit.event.sent_at
        ),
        audit_metadata=audit.audit_metadata,
        created_at=audit.created_at,
    )


def _to_approval_ref(approval: WorkflowApproval) -> ApprovalRef:
    return ApprovalRef(
        workflow_approval_id=approval.workflow_approval_id,
        approving_user=_to_user_ref(approval.approving_user),
        event_id=approval.workflow_event_history_id,
        is_still_valid=approval.is_still_valid,
        comment=approval.comment,
        approval_type=approval.approval_type,
        approval_response_type=approval.approval_response_type,
        created_at=approval.created_at,
    )


def _workflow_load_options() -> tuple[Any, ...]:
    return (
        selectinload(Workflow.workflow_approvals).selectinload(WorkflowApproval.approving_user),
    )


def _get_workflow(db_session: db.Session, workflow_id: uuid.UUID) -> Workflow | None:
    stmt = (
        select(Workflow)
        .where(Workflow.workflow_id == workflow_id)
        .options(*_workflow_load_options())
    )
    return db_session.execute(stmt).scalars().one_or_none()


def _verify_workflow_read_access(
    db_session: db.Session, user: User, workflow: Workflow
) -> tuple[WorkflowConfig, type[BaseStateMachine]]:
    """Verify the user can read the workflow, and return its config + state machine for reuse."""
    resource_type = workflow.resource.resource_type

    required_privilege = VIEW_PRIVILEGE_FOR_RESOURCE_TYPE.get(resource_type)
    if required_privilege is None:
        logger.info(
            "Workflow resource type is not readable through this endpoint",
            extra=workflow.get_log_extra(include_joined_values=True),
        )
        raise_flask_error(403, "Forbidden")

    AuthorizationEnforcer(db_session).verify_access(
        user=user,
        required_privileges={required_privilege},
        resource=workflow.resource.concrete_resource,
    )

    return WorkflowRegistry.get_state_machine_for_workflow_type(workflow.workflow_type)


def _build_approval_config(
    db_session: db.Session, workflow: Workflow, config: WorkflowConfig
) -> dict[str, ApprovalConfigEntry]:
    approval_config: dict[str, ApprovalConfigEntry] = {}

    for event_name, event_approval_config in config.approval_mapping.items():
        possible_users = db_session.execute(
            get_approver_query(db_session, workflow, event_approval_config)
        ).scalars()

        approval_config[event_name] = ApprovalConfigEntry(
            approval_type=event_approval_config.approval_type,
            required_privileges=event_approval_config.required_privileges,
            allowed_approval_response_types=event_approval_config.allowed_approval_response_types,
            possible_users=[_to_user_ref(u) for u in possible_users],
        )

    return approval_config


def _get_valid_events(
    db_session: db.Session,
    workflow: Workflow,
    config: WorkflowConfig,
    state_machine_cls: type[BaseStateMachine],
) -> list[str]:
    if not workflow.is_active:
        return []

    persistence_model = config.persistence_model_cls(db_session, workflow)
    state_machine = state_machine_cls(persistence_model)
    return state_machine.get_valid_events_for_current_state()


def _to_workflow_detail(
    db_session: db.Session,
    workflow: Workflow,
    config: WorkflowConfig,
    state_machine_cls: type[BaseStateMachine],
) -> WorkflowDetail:
    approvals = sorted(workflow.workflow_approvals, key=lambda a: a.created_at)

    return WorkflowDetail(
        workflow_id=workflow.workflow_id,
        workflow_type=workflow.workflow_type,
        current_workflow_state=workflow.current_workflow_state,
        is_active=workflow.is_active,
        resource_id=workflow.resource_id,
        resource_type=workflow.resource.resource_type,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        workflow_approvals=[_to_approval_ref(a) for a in approvals],
        workflow_approval_config=_build_approval_config(db_session, workflow, config),
        valid_events=_get_valid_events(db_session, workflow, config, state_machine_cls),
    )


def get_workflow_and_verify_access(
    db_session: db.Session, user: User, workflow_id: uuid.UUID
) -> WorkflowDetail:
    """Get a workflow by ID, verifying the user can view it.

    Raises:
        404: If no workflow with that ID exists
        403: If the user lacks the privilege to view it
    """
    workflow = _get_workflow(db_session, workflow_id)
    if workflow is None:
        raise_flask_error(404, f"Could not find Workflow with ID {workflow_id}")

    config, state_machine_cls = _verify_workflow_read_access(db_session, user, workflow)
    return _to_workflow_detail(db_session, workflow, config, state_machine_cls)


def get_workflow_by_event_id_and_verify_access(
    db_session: db.Session, user: User, event_id: uuid.UUID
) -> WorkflowDetail:
    """Get the workflow associated with an event ID, verifying the user can view it.

    Raises:
        404: If no event with that ID exists, or the event has no associated workflow
        403: If the user lacks the privilege to view it
    """
    stmt = (
        select(WorkflowEventHistory)
        .where(WorkflowEventHistory.workflow_event_history_id == event_id)
        .options(selectinload(WorkflowEventHistory.workflow).options(*_workflow_load_options()))
    )
    event = db_session.execute(stmt).scalars().one_or_none()

    if event is None:
        raise_flask_error(404, f"Could not find Event with ID {event_id}")

    if event.workflow is None:
        raise_flask_error(404, f"Could not find Workflow for Event with ID {event_id}")

    config, state_machine_cls = _verify_workflow_read_access(db_session, user, event.workflow)
    return _to_workflow_detail(db_session, event.workflow, config, state_machine_cls)
