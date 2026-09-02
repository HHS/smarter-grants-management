import dataclasses
import uuid
from collections.abc import Sequence
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.adapters import db
from src.db.models.user_models import User
from src.db.models.workflow_models import WorkflowAudit
from src.pagination.pagination_models import PaginationInfo, PaginationParams
from src.pagination.paginator import Paginator
from src.pagination.sorting_util import apply_sorting
from src.services.workflows.get_workflow import UserRef, get_workflow_and_verify_access, to_user_ref


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


def _to_audit_event_ref(audit: WorkflowAudit) -> AuditEventRef:
    return AuditEventRef(
        workflow_audit_id=audit.workflow_audit_id,
        acting_user=to_user_ref(audit.acting_user),
        transition_event=audit.transition_event,
        source_state=audit.source_state,
        target_state=audit.target_state,
        event=WorkflowEventRef(
            event_id=audit.event.workflow_event_history_id, sent_at=audit.event.sent_at
        ),
        audit_metadata=audit.audit_metadata,
        created_at=audit.created_at,
    )


class WorkflowAuditRequest(BaseModel):
    pagination: PaginationParams


def get_workflow_audits(
    db_session: db.Session, user: User, workflow_id: uuid.UUID, json_data: dict
) -> tuple[Sequence[AuditEventRef], PaginationInfo]:
    """List a workflow's audit history, paginated.

    Raises:
        404: If no workflow with that ID exists
        403: If the user lacks the privilege to view it
    """
    params = WorkflowAuditRequest.model_validate(json_data)

    # 404/403 handling is reused from the detail endpoint rather than duplicated here.
    get_workflow_and_verify_access(db_session, user, workflow_id)

    stmt = (
        select(WorkflowAudit)
        .where(WorkflowAudit.workflow_id == workflow_id)
        .options(selectinload(WorkflowAudit.acting_user), selectinload(WorkflowAudit.event))
    )
    stmt = apply_sorting(stmt, params.pagination.sort_order, WorkflowAudit)

    paginator: Paginator[WorkflowAudit] = Paginator(
        WorkflowAudit, stmt, db_session, page_size=params.pagination.page_size
    )
    results = paginator.page_at(page_offset=params.pagination.page_offset)
    pagination_info = PaginationInfo.from_pagination_params(params.pagination, paginator)

    return [_to_audit_event_ref(audit) for audit in results], pagination_info
