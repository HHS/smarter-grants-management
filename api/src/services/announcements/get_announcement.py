import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.announcement_models import (
    Announcement,
    AnnouncementAssistanceListing,
    AnnouncementSummary,
)
from src.db.models.application_package_models import ApplicationPackage
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access


def announcement_response_options() -> tuple[ORMOption, ...]:
    return (
        selectinload(Announcement.announcement_assistance_listings).selectinload(
            AnnouncementAssistanceListing.assistance_listing
        ),
        selectinload(Announcement.announcement_summaries).options(
            selectinload(AnnouncementSummary.link_applicant_types),
            selectinload(AnnouncementSummary.link_funding_categories),
            selectinload(AnnouncementSummary.link_funding_instruments),
        ),
        selectinload(Announcement.application_packages).options(
            selectinload(ApplicationPackage.application_package_forms),
            selectinload(ApplicationPackage.announcement_assistance_listing),
            selectinload(ApplicationPackage.link_application_package_open_to_applicant),
        ),
    )


def get_announcement(db_session: db.Session, announcement_id: uuid.UUID) -> Announcement:
    announcement = db_session.execute(
        select(Announcement)
        .where(Announcement.announcement_id == announcement_id)
        .options(*announcement_response_options())
    ).scalar_one_or_none()

    if announcement is None:
        raise_flask_error(404, f"Could not find announcement with ID {announcement_id}")

    return announcement


def get_announcement_and_verify_access(
    db_session: db.Session, announcement_id: uuid.UUID, user: User
) -> Announcement:
    announcement = get_announcement(db_session, announcement_id)

    if not has_access(user, announcement, "view"):
        raise_flask_error(403, "User does not have access to this announcement")

    return announcement
