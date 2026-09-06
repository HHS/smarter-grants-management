import uuid
from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import or_, select

from src.adapters import db
from src.db.models.opportunity_models import Opportunity
from src.db.models.user_models import User
from src.pagination.pagination_models import PaginationInfo, PaginationParams
from src.pagination.paginator import Paginator
from src.pagination.sorting_util import apply_sorting
from src.services.opportunities.authorization import has_access
from src.services.opportunities.get_opportunity import opportunity_response_options


class OpportunityListFilters(BaseModel):
    opportunity_group_id: uuid.UUID | None = None
    query: str | None = None


class OpportunityListRequest(BaseModel):
    pagination: PaginationParams
    filters: OpportunityListFilters | None = None


def list_opportunities(
    db_session: db.Session, user: User, json_data: dict
) -> tuple[Sequence[Opportunity], PaginationInfo]:
    params = OpportunityListRequest.model_validate(json_data)

    stmt = select(Opportunity).options(*opportunity_response_options())

    if params.filters is not None:
        if params.filters.opportunity_group_id is not None:
            stmt = stmt.where(
                Opportunity.opportunity_group_id == params.filters.opportunity_group_id
            )

        if params.filters.query:
            search_term = f"%{params.filters.query}%"
            stmt = stmt.where(
                or_(
                    Opportunity.opportunity_number.ilike(search_term),
                    Opportunity.opportunity_title.ilike(search_term),
                )
            )

    stmt = apply_sorting(stmt, params.pagination.sort_order, Opportunity)

    paginator: Paginator[Opportunity] = Paginator(
        Opportunity,
        stmt,
        db_session,
        page_size=params.pagination.page_size,
    )
    results = paginator.page_at(page_offset=params.pagination.page_offset)
    pagination_info = PaginationInfo.from_pagination_params(
        params.pagination,
        paginator,
    )

    # has_access is currently a dummy seam. Once authorization is finalized,
    # replace this with query-level authorization so pagination remains exact.
    accessible_results = [
        opportunity for opportunity in results if has_access(user, opportunity, "view")
    ]

    return accessible_results, pagination_info
