import logging
import uuid

from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import AnnouncementAuditEvent
from src.db.models.announcement_models import Announcement, AnnouncementSummary
from src.db.models.user_models import User
from src.services.announcements.announcement_audit import record_announcement_audit, snapshot_fields
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import get_announcement

logger = logging.getLogger(__name__)

ANNOUNCEMENT_SUMMARY_UPDATE_FIELDS = (
    "summary_description",
    "is_cost_sharing",
    "post_timestamp",
    "close_timestamp",
    "close_timestamp_description",
    "archive_timestamp",
    "expected_number_of_awards",
    "estimated_total_program_funding",
    "award_floor",
    "award_ceiling",
    "additional_info_url",
    "additional_info_url_description",
    "forecasted_post_timestamp",
    "forecasted_close_timestamp",
    "forecasted_close_timestamp_description",
    "estimated_award_date",
    "estimated_project_start_date",
    "fiscal_year",
    "funding_categories",
    "funding_category_description",
    "funding_instruments",
    "applicant_types",
    "applicant_eligibility_description",
    "agency_contact_description",
    "agency_email_address",
    "agency_email_address_description",
)
ANNOUNCEMENT_SUMMARY_CREATE_FIELDS = ANNOUNCEMENT_SUMMARY_UPDATE_FIELDS + ("is_forecast",)


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

    before = snapshot_fields(None, ANNOUNCEMENT_SUMMARY_CREATE_FIELDS)

    summary = AnnouncementSummary(
        announcement=announcement,
        **summary_data,
    )

    db_session.add(summary)
    db_session.flush()

    after = snapshot_fields(summary, ANNOUNCEMENT_SUMMARY_CREATE_FIELDS)

    logger.info(
        "Created announcement summary",
        extra={
            "announcement_id": announcement_id,
            "announcement_summary_id": summary.announcement_summary_id,
            "is_forecast": summary.is_forecast,
        },
    )

    record_announcement_audit(
        db_session,
        user,
        announcement_id,
        AnnouncementAuditEvent.ANNOUNCEMENT_SUMMARY_CREATED,
        before,
        after,
        announcement_summary_id=summary.announcement_summary_id,
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

    before = snapshot_fields(summary, ANNOUNCEMENT_SUMMARY_UPDATE_FIELDS)

    for field_name, new_value in summary_data.items():
        setattr(summary, field_name, new_value)

    after = snapshot_fields(summary, ANNOUNCEMENT_SUMMARY_UPDATE_FIELDS)

    logger.info(
        "Updated announcement summary",
        extra={
            "announcement_id": announcement_id,
            "announcement_summary_id": announcement_summary_id,
        },
    )

    record_announcement_audit(
        db_session,
        user,
        announcement_id,
        AnnouncementAuditEvent.ANNOUNCEMENT_SUMMARY_UPDATED,
        before,
        after,
        announcement_summary_id=announcement_summary_id,
    )

    return summary
