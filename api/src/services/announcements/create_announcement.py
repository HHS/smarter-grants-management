import uuid

from pydantic import BaseModel
from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import AnnouncementCategory
from src.db.models.announcement_models import Announcement, AnnouncementAssistanceListing
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import get_announcement
from src.services.announcements.get_assistance_listing import get_assistance_listing


class AnnouncementCreateRequest(BaseModel):
    announcement_number: str
    announcement_title: str
    tagline: str
    purpose_statement: str
    category: AnnouncementCategory
    category_explanation: str | None = None
    assistance_listing_number: str


def check_announcement_number_exists(db_session: db.Session, announcement_number: str) -> None:
    stmt = select(Announcement).where(Announcement.announcement_number == announcement_number)
    existing_opportunity = db_session.execute(stmt).scalar_one_or_none()

    if existing_opportunity is not None:
        raise_flask_error(
            422, message=f"Announcement with number '{announcement_number}' already exists"
        )


def create_announcement(db_session: db.Session, user: User, json_data: dict) -> Announcement:
    request = AnnouncementCreateRequest(**json_data)

    if not has_access(user, None, "create"):
        raise_flask_error(403, "User does not have access to create an announcement")

    check_announcement_number_exists(db_session, request.announcement_number)

    assistance_listing = get_assistance_listing(db_session, request.assistance_listing_number)

    announcement = Announcement(
        announcement_id=uuid.uuid4(),
        announcement_number=request.announcement_number,
        announcement_title=request.announcement_title,
        tagline=request.tagline,
        purpose_statement=request.purpose_statement,
        category=request.category,
        category_explanation=request.category_explanation,
    )
    db_session.add(announcement)

    announcement_assistance_listing = AnnouncementAssistanceListing(
        announcement_assistance_listing_id=uuid.uuid4(),
        announcement=announcement,
        assistance_listing=assistance_listing,
    )
    db_session.add(announcement_assistance_listing)

    return get_announcement(db_session, announcement.announcement_id)
