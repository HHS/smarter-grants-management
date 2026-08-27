import uuid
from collections.abc import Sequence

from grants_shared.adapters import db
from grants_shared.pagination.pagination_models import PaginationInfo, PaginationParams
from grants_shared.pagination.paginator import Paginator
from grants_shared.pagination.sorting_util import apply_sorting
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.models.user_models import User
from src.db.models.workflow_models import WorkflowAudit
from src.services.workflows.get_workflow import (
    AuditEventRef,
    _to_audit_event_ref,
    get_workflow_and_verify_access,
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
