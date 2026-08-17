import logging

from grants_shared.adapters import db
from sqlalchemy import Select, select

from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import ApprovalResponseType, ApprovalType, ResourceInheritance
from src.db.models.user_models import User
from src.db.models.workflow_models import Workflow, WorkflowApproval
from src.workflow.event.state_machine_event import StateMachineEvent
from src.workflow.workflow_config import ApprovalConfig, WorkflowConfig
from src.workflow.workflow_constants import WorkflowConstants
from src.workflow.workflow_errors import (
    DisallowedApprovalResponseTypeError,
    InvalidWorkflowResponseTypeError,
)

logger = logging.getLogger(__name__)


def get_approvals_for_workflow(
    db_session: db.Session,
    workflow: Workflow,
    approval_type: ApprovalType,
    approving_user: User | None = None,
    is_valid_events: bool = True,
) -> list[WorkflowApproval]:
    """Get a list of approvals for a given workflow."""
    # We query the DB rather than using workflow.workflow_approvals
    # so we can filter.
    stmt = (
        select(WorkflowApproval)
        .where(WorkflowApproval.workflow == workflow)
        .where(WorkflowApproval.approval_type == approval_type)
    )

    if approving_user is not None:
        stmt = stmt.where(WorkflowApproval.approving_user_id == approving_user.user_id)

    if is_valid_events:
        stmt = stmt.where(WorkflowApproval.is_still_valid.is_(True))

    approvals = db_session.execute(stmt).scalars()

    return list(approvals)


def get_approval_response_type_from_metadata(
    metadata: dict | None, log_extra: dict | None = None
) -> ApprovalResponseType:
    """Get the approval response type from a metadata dict."""
    if log_extra is None:
        log_extra = {}
    raw_value = None
    if metadata is not None:
        raw_value = metadata.get(WorkflowConstants.APPROVAL_RESPONSE_TYPE)

    if raw_value is None:
        logger.warning("Approval response type not found in metadata", extra=log_extra)
        raise InvalidWorkflowResponseTypeError("Approval response type not found in metadata")

    try:
        return ApprovalResponseType(raw_value)
    except ValueError as e:
        logger.warning("Approval response type is not a valid value")
        raise InvalidWorkflowResponseTypeError("Approval response type is not a valid value") from e


def validate_approval_response_type(
    approval_response_type: ApprovalResponseType,
    approval_config: ApprovalConfig,
    log_extra: dict | None = None,
) -> None:
    """Validate an approval response type against the approval config."""
    if log_extra is None:
        log_extra = {}

    if approval_response_type in approval_config.allowed_approval_response_types:
        return

    logger.warning(
        "Approval response type not allowed for this approval config",
        extra=log_extra
        | {
            "allowed_types": ", ".join(
                [t.value for t in approval_config.allowed_approval_response_types]
            )
        },
    )
    raise DisallowedApprovalResponseTypeError(
        "Approval response type is not allowed for this approval configuration.",
        allowed_approval_response_types=approval_config.allowed_approval_response_types,
    )


def get_approval_response_type(state_machine_event: StateMachineEvent) -> ApprovalResponseType:
    """Get the approval response type from the state machine event (for state machine usage)."""
    return get_approval_response_type_from_metadata(
        state_machine_event.metadata, state_machine_event.get_log_extra()
    )


def get_approver_query(
    db_session: db.Session, workflow: Workflow, approval_config: ApprovalConfig
) -> Select:
    """Build the query for the users who can do a given approval on a workflow.

    Uses our authorization logic against the workflow's resource. Both the check on
    whether a user may approve and the approval emails run off this, so the two can't
    disagree on who an approver is.
    """
    enforcer = AuthorizationEnforcer(db_session)
    resources = enforcer.get_resources_for_user_lookup(
        workflow.resource.concrete_resource, ResourceInheritance.FULL
    )

    return enforcer.get_users_for_resource_query(
        resources, required_privileges=set(approval_config.required_privileges)
    )


def can_user_do_approval(
    db_session: db.Session,
    user: User,
    workflow: Workflow,
    config: WorkflowConfig,
    event_to_send: str,
) -> bool:
    """Check if a user can do an approval for a given workflow."""
    log_extra = workflow.get_log_extra() | {
        "user_id": user.user_id,
        "event_to_send": event_to_send,
    }

    approval_config = config.approval_mapping.get(event_to_send)

    if approval_config is None:
        logger.info("No approval mapping found for event", extra=log_extra)
        return False

    logger.info("Checking if user can do approval for workflow resource", extra=log_extra)

    stmt = get_approver_query(db_session, workflow, approval_config).where(
        User.user_id == user.user_id
    )
    can_approve = db_session.execute(stmt).scalar() is not None

    logger.info(
        "Finished checking if user can do approval for workflow resource",
        extra=log_extra | {"can_approve": can_approve},
    )
    return can_approve
