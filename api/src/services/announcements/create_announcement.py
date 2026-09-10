from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.announcement_models import Announcement, AnnouncementAssistanceListing
from src.db.models.assistance_listing_models import AssistanceListing
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access


def create_announcement(db_session: db.Session, user: User, json_data: dict) -> Announcement:
    if not has_access(user, None, "create"):
        raise_flask_error(403, "User does not have access to create an announcement")

    existing_announcement = db_session.execute(
        select(Announcement).where(
            Announcement.announcement_number == json_data["announcement_number"]
        )
    ).scalar_one_or_none()
    if existing_announcement is not None:
        raise_flask_error(
            422,
            f"Announcement number {json_data['announcement_number']} already exists",
        )

    assistance_listing = db_session.execute(
        select(AssistanceListing).where(
            AssistanceListing.assistance_listing_number == json_data["assistance_listing_number"]
        )
    ).scalar_one_or_none()
    if assistance_listing is None:
        raise_flask_error(
            404,
            "Could not find assistance listing with number "
            f"{json_data['assistance_listing_number']}",
        )

    announcement = Announcement(
        announcement_number=json_data["announcement_number"],
        announcement_title=json_data["announcement_title"],
        tagline=json_data["tagline"],
        purpose_statement=json_data["purpose_statement"],
        category=json_data["category"],
        category_explanation=json_data.get("category_explanation"),
    )
    db_session.add(announcement)
    db_session.flush()

    db_session.add(
        AnnouncementAssistanceListing(
            announcement=announcement,
            assistance_listing=assistance_listing,
        )
    )
    db_session.flush()

    return announcement
