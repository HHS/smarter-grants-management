from collections.abc import Sequence

from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select

from src.adapters import db
from src.db.models.assistance_listing_models import AssistanceListing
from src.pagination.pagination_models import PaginationInfo, PaginationParams
from src.pagination.paginator import Paginator
from src.pagination.sorting_util import apply_sorting
from src.services.search.query_to_tsquery import query_to_tsquery


class SearchAssistanceListingParams(BaseModel):
    pagination: PaginationParams
    query: str | None = Field(default=None)


def search_assistance_listings(
    db_session: db.Session, json_data: dict
) -> tuple[Sequence[AssistanceListing], PaginationInfo]:
    """Search for assistance listings"""

    search_params = SearchAssistanceListingParams.model_validate(json_data)

    # Only return active assistance listings
    stmt = select(AssistanceListing).where(AssistanceListing.is_active.is_(True))

    # If a query is provided, we filter on both the assistance listing number and program title like:
    #
    #   where assistance_listing_number ILIKE 'query%' OR
    #         to_tsvector('english', program_title) @@ to_tsquery('query')
    if search_params.query:
        stmt = stmt.where(
            or_(
                AssistanceListing.assistance_listing_number.istartswith(search_params.query),
                # NOTE - we have to include to_tsvector around program_title otherwise it won't
                # hit the index we added on that column.
                func.to_tsvector("english", AssistanceListing.program_title).op("@@")(
                    func.to_tsquery(query_to_tsquery(search_params.query))
                ),
            )
        )

    # Apply sorting
    stmt = apply_sorting(stmt, search_params.pagination.sort_order, AssistanceListing)

    # Paginate and fetch results
    paginator: Paginator[AssistanceListing] = Paginator(
        AssistanceListing, stmt, db_session, page_size=search_params.pagination.page_size
    )
    assistance_listings = paginator.page_at(page_offset=search_params.pagination.page_offset)
    pagination_info = PaginationInfo.from_pagination_params(search_params.pagination, paginator)

    return assistance_listings, pagination_info
