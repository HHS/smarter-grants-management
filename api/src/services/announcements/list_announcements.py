from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import or_, select

from src.adapters import db
from src.db.models.announcement_models import Announcement
from src.db.models.user_models import User
from src.pagination.pagination_models import PaginationInfo, PaginationParams
from src.pagination.paginator import Paginator
from src.pagination.sorting_util import apply_sorting
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import announcement_response_options


class AnnouncementListFilters(BaseModel):
    query: str | None = None


class AnnouncementListRequest(BaseModel):
    pagination: PaginationParams
    filters: AnnouncementListFilters | None = None


def list_announcements(
    db_session: db.Session, user: User, json_data: dict
) -> tuple[Sequence[Announcement], PaginationInfo]:
    params = AnnouncementListRequest.model_validate(json_data)

    stmt = select(Announcement).options(*announcement_response_options())

    if params.filters is not None and params.filters.query:
        search_term = f"%{params.filters.query}%"
        stmt = stmt.where(
            or_(
                Announcement.announcement_number.ilike(search_term),
                Announcement.announcement_title.ilike(search_term),
            )
        )

    stmt = apply_sorting(stmt, params.pagination.sort_order, Announcement)

    paginator: Paginator[Announcement] = Paginator(
        Announcement,
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
        announcement for announcement in results if has_access(user, announcement, "view")
    ]

    return accessible_results, pagination_info
