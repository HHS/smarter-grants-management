import uuid

from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.announcement_models import (
    Announcement,
    AnnouncementSummary,
    LinkAnnouncementSummaryApplicantType,
    LinkAnnouncementSummaryFundingCategory,
    LinkAnnouncementSummaryFundingInstrument,
)
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import get_announcement


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


def _replace_summary_lookups(
    summary: AnnouncementSummary,
    funding_instruments: list,
    funding_categories: list,
    applicant_types: list,
) -> None:
    summary.link_funding_instruments = [
        LinkAnnouncementSummaryFundingInstrument(funding_instrument=value)
        for value in funding_instruments
    ]
    summary.link_funding_categories = [
        LinkAnnouncementSummaryFundingCategory(funding_category=value)
        for value in funding_categories
    ]
    summary.link_applicant_types = [
        LinkAnnouncementSummaryApplicantType(applicant_type=value) for value in applicant_types
    ]


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

    funding_instruments = summary_data.pop("funding_instruments")
    funding_categories = summary_data.pop("funding_categories")
    applicant_types = summary_data.pop("applicant_types")

    summary = AnnouncementSummary(
        announcement=announcement,
        **summary_data,
    )
    _replace_summary_lookups(
        summary,
        funding_instruments,
        funding_categories,
        applicant_types,
    )

    db_session.add(summary)
    db_session.flush()

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

    funding_instruments = summary_data.pop("funding_instruments")
    funding_categories = summary_data.pop("funding_categories")
    applicant_types = summary_data.pop("applicant_types")

    for field_name, new_value in summary_data.items():
        setattr(summary, field_name, new_value)

    old_funding_instruments = set(summary.funding_instruments)
    new_funding_instruments = set(funding_instruments)

    old_funding_categories = set(summary.funding_categories)
    new_funding_categories = set(funding_categories)

    old_applicant_types = set(summary.applicant_types)
    new_applicant_types = set(applicant_types)

    if (
        old_funding_instruments != new_funding_instruments
        or old_funding_categories != new_funding_categories
        or old_applicant_types != new_applicant_types
    ):
        _replace_summary_lookups(
            summary,
            funding_instruments,
            funding_categories,
            applicant_types,
        )

    db_session.flush()
    return summary
