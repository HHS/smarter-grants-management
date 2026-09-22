import pytest
from sqlalchemy.exc import IntegrityError

from tests.db.models.factories import AnnouncementFactory, AnnouncementSummaryFactory


def test_announcement_summary_unique_constraint(db_session, enable_factory_create):
    """
    Test that a given announcement can have at most one non-deleted summary
    that isn't a forecast, and one that is.

    It can have as many deleted summaries as it wants.
    """
    announcement = AnnouncementFactory.create()

    # We can add deleted announcements just fine
    AnnouncementSummaryFactory.create_batch(
        size=3, is_forecast=True, is_deleted=True, announcement=announcement
    )
    AnnouncementSummaryFactory.create_batch(
        size=2, is_forecast=False, is_deleted=True, announcement=announcement
    )

    forecast = AnnouncementSummaryFactory.create(
        is_forecast=True, is_deleted=False, announcement=announcement
    )
    non_forecast = AnnouncementSummaryFactory.create(
        is_forecast=False, is_deleted=False, announcement=announcement
    )

    # Verify the forecast/non_forecast are fetched right
    # It won't pickup the deleted ones via this
    db_session.refresh(announcement)
    assert announcement.forecast_summary.announcement_summary_id == forecast.announcement_summary_id
    assert (
        announcement.non_forecast_summary.announcement_summary_id
        == non_forecast.announcement_summary_id
    )

    with pytest.raises(IntegrityError, match="duplicate key value violates unique constraint"):
        AnnouncementSummaryFactory.create(
            is_forecast=True, is_deleted=False, announcement=announcement
        )
