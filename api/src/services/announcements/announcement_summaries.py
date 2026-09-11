import logging
import uuid

from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.announcement_models import Announcement, AnnouncementSummary
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import get_announcement

logger = logging.getLogger(__name__)


def _check_existing_summary(
    db_session: db.Session,
    announcement_id: uuid.UUID,
    is_forecast: bool,
) -> None:
    existing_summary = db_session.execute(
        select(AnnouncementSummary).where(
            AnnouncementSummary.announcement_id == announcement_id,
            AnnouncementSummary.is_forecast == is_forecast,
        )
    ).scalar_one_or_none()

    if existing_summary is not None:
        summary_type = "forecast" if is_forecast else "non-forecast"
        raise_flask_error(
            422,
            f"An announcement summary of type {summary_type} already exists",
        )


def _get_announcement_summary(
    db_session: db.Session,
    announcement_id: uuid.UUID,
    announcement_summary_id: uuid.UUID,
) -> AnnouncementSummary:
    summary = db_session.execute(
        select(AnnouncementSummary).where(
            AnnouncementSummary.announcement_summary_id == announcement_summary_id,
            AnnouncementSummary.announcement_id == announcement_id,
        )
    ).scalar_one_or_none()

    if summary is None:
        raise_flask_error(
            404,
            f"Could not find Announcement Summary with ID {announcement_summary_id}",
        )

    return summary


def create_announcement_summary(
    db_session: db.Session,
    announcement_id: uuid.UUID,
    summary_data: dict,
    user: User,
) -> AnnouncementSummary:
    announcement: Announcement = get_announcement(db_session, announcement_id)

    if not has_access(user, announcement, "update"):
        raise_flask_error(403, "User does not have access to update this announcement")

    _check_existing_summary(db_session, announcement_id, summary_data["is_forecast"])

    summary = AnnouncementSummary(
        announcement=announcement,
        **summary_data,
    )

    db_session.add(summary)
    db_session.flush()

    logger.info(
        "Created announcement summary",
        extra={
            "announcement_id": announcement_id,
            "announcement_summary_id": summary.announcement_summary_id,
            "is_forecast": summary.is_forecast,
        },
    )

    return summary


def update_announcement_summary(
    db_session: db.Session,
    announcement_id: uuid.UUID,
    announcement_summary_id: uuid.UUID,
    summary_data: dict,
    user: User,
) -> AnnouncementSummary:
    announcement: Announcement = get_announcement(db_session, announcement_id)

    if not has_access(user, announcement, "update"):
        raise_flask_error(403, "User does not have access to update this announcement")

    summary = _get_announcement_summary(
        db_session,
        announcement_id,
        announcement_summary_id,
    )

    for field_name, new_value in summary_data.items():
        setattr(summary, field_name, new_value)

    return summary
