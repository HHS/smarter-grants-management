from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import select

from src.adapters import db
from src.db.models.announcement_models import Announcement
from src.db.models.user_models import User
from src.pagination.pagination_models import PaginationInfo, PaginationParams
from src.pagination.paginator import Paginator
from src.pagination.sorting_util import apply_sorting
from src.services.announcements.get_announcement import announcement_response_options


class AnnouncementListRequest(BaseModel):
    pagination: PaginationParams


def list_announcements(
    db_session: db.Session, user: User, json_data: dict
) -> tuple[Sequence[Announcement], PaginationInfo]:
    params = AnnouncementListRequest.model_validate(json_data)

    stmt = select(Announcement).options(*announcement_response_options())

    stmt = apply_sorting(stmt, params.pagination.sort_order, Announcement)

    # TODO - when we add back authZ, add a filter to only return announcements
    # that the user can actually access.

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

    return results, pagination_info
