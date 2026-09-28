import uuid
from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from src.adapters import db
from src.db.models.announcement_models import AnnouncementAttachment, AnnouncementAudit
from src.db.models.application_package_models import ApplicationPackageInstruction
from src.db.models.user_models import User
from src.pagination.pagination_models import PaginationInfo, PaginationParams
from src.pagination.paginator import Paginator
from src.pagination.sorting_util import apply_sorting
from src.search.search_models import StrSearchFilter
from src.services.announcements.get_announcement import get_announcement_and_verify_access


class AnnouncementAuditFilters(BaseModel):
    announcement_audit_event: StrSearchFilter | None = None


class AnnouncementAuditRequest(BaseModel):
    filters: AnnouncementAuditFilters | None = None
    pagination: PaginationParams


def apply_filters(stmt: Select, filters: AnnouncementAuditFilters | None) -> Select:
    """Apply filters from the request to the DB query for announcement audit events"""
    if filters is None:
        return stmt

    if (
        filters.announcement_audit_event is not None
        and filters.announcement_audit_event.one_of is not None
    ):
        stmt = stmt.where(
            AnnouncementAudit.announcement_audit_event.in_(filters.announcement_audit_event.one_of)
        )

    return stmt


def get_announcement_audits(
    db_session: db.Session, user: User, announcement_id: uuid.UUID, request: dict
) -> tuple[Sequence[AnnouncementAudit], PaginationInfo]:
    """List an announcement's audit history, paginated.

    Raises:
        404: If no announcement with that ID exists
        403: If the user lacks access to view it
    """
    params = AnnouncementAuditRequest.model_validate(request)

    get_announcement_and_verify_access(db_session, announcement_id, user)

    stmt = (
        select(AnnouncementAudit)
        .where(AnnouncementAudit.announcement_id == announcement_id)
        .options(
            # user.email is a computed property backed by this relationship
            selectinload(AnnouncementAudit.user).selectinload(User.linked_login_gov_external_user),
            selectinload(AnnouncementAudit.announcement_summary),
            selectinload(AnnouncementAudit.announcement_attachment).selectinload(
                AnnouncementAttachment.file_attachment
            ),
            selectinload(AnnouncementAudit.application_package),
            selectinload(AnnouncementAudit.application_package_instruction).selectinload(
                ApplicationPackageInstruction.file_attachment
            ),
        )
    )

    stmt = apply_filters(stmt, params.filters)
    stmt = apply_sorting(stmt, params.pagination.sort_order, AnnouncementAudit)

    paginator: Paginator[AnnouncementAudit] = Paginator(
        AnnouncementAudit, stmt, db_session, page_size=params.pagination.page_size
    )
    paginated_results = paginator.page_at(page_offset=params.pagination.page_offset)
    pagination_info = PaginationInfo.from_pagination_params(params.pagination, paginator)

    return paginated_results, pagination_info
