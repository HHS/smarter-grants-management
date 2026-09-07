import uuid
from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.sql import Select

from src.adapters import db
from src.constants.lookup_constants import OpportunityAuditEvent
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit
from src.db.models.user_models import User
from src.pagination.pagination_models import PaginationInfo, PaginationParams
from src.pagination.paginator import Paginator
from src.pagination.sorting_util import apply_sorting
from src.services.opportunities.get_opportunity import get_opportunity_and_verify_access


class OpportunityAuditFilters(BaseModel):
    opportunity_audit_event: list[OpportunityAuditEvent] | None = None


class OpportunityAuditRequest(BaseModel):
    filters: OpportunityAuditFilters | None = None
    pagination: PaginationParams


def apply_filters(
    stmt: Select,
    filters: OpportunityAuditFilters | None,
) -> Select:
    if filters is None:
        return stmt

    if filters.opportunity_audit_event:
        stmt = stmt.where(
            OpportunityGroupAudit.opportunity_audit_event.in_(filters.opportunity_audit_event)
        )

    return stmt


def list_opportunity_audit(
    db_session: db.Session,
    user: User,
    opportunity_id: uuid.UUID,
    request: dict,
) -> tuple[Sequence[OpportunityGroupAudit], PaginationInfo]:
    params = OpportunityAuditRequest.model_validate(request)

    get_opportunity_and_verify_access(db_session, opportunity_id, user)

    stmt = select(OpportunityGroupAudit).where(
        OpportunityGroupAudit.opportunity_id == opportunity_id
    )
    stmt = apply_filters(stmt, params.filters)
    stmt = apply_sorting(
        stmt,
        params.pagination.sort_order,
        OpportunityGroupAudit,
    )

    paginator: Paginator[OpportunityGroupAudit] = Paginator(
        OpportunityGroupAudit,
        stmt,
        db_session,
        page_size=params.pagination.page_size,
    )
    results = paginator.page_at(page_offset=params.pagination.page_offset)
    pagination_info = PaginationInfo.from_pagination_params(
        params.pagination,
        paginator,
    )

    return results, pagination_info
