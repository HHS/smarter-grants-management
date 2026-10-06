import pytest
from sqlalchemy.exc import IntegrityError

from tests.db.models.factories import (
    AnnouncementFactory,
    AnnouncementSummaryFactory,
    OpportunityFactory,
)


def test_opportunity_factory_create(db_session, enable_factory_create):
    opportunity = OpportunityFactory.create()

    assert opportunity.opportunity_id is not None
    assert opportunity.partner_code


def test_opportunity_has_many_announcements(db_session, enable_factory_create):
    opportunity = OpportunityFactory.create()
    announcements = AnnouncementFactory.create_batch(size=2, opportunity=opportunity)

    db_session.refresh(opportunity)
    assert {a.announcement_id for a in opportunity.announcements} == {
        a.announcement_id for a in announcements
    }
    assert announcements[0].partner_code == opportunity.partner_code


def test_opportunity_partner_code_required(db_session, enable_factory_create):
    with pytest.raises(IntegrityError, match="not-null constraint"):
        OpportunityFactory.create(partner_code=None)
from src.constants.lookup_constants import (
    AnnouncementType,
    ApplicationPackageOpenToApplicant,
    PerformancePeriodType,
    SourceSelectionMethod,
)
from tests.db.models.factories import (
    AnnouncementFactory,
    AnnouncementSummaryFactory,
    ApplicationPackageFactory,
    ApplicationPackageRecipientFactory,
)


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


def test_announcement_non_competitive_defaults(db_session, enable_factory_create):
    announcement = AnnouncementFactory.create()
    db_session.refresh(announcement)

    assert announcement.announcement_type == AnnouncementType.DISCRETIONARY
    assert announcement.is_budget_period_renewal is False
    assert announcement.allows_cash_contributions is False
    assert announcement.allows_in_kind_contributions is False
    assert announcement.budget_period_months == 12
    assert announcement.source_announcement is None
    assert announcement.source_selection_method is None
    assert announcement.performance_period_type is None


def test_special_instance_budget_period_renewal(db_session, enable_factory_create):
    source = AnnouncementFactory.create()
    announcement = AnnouncementFactory.create(
        announcement_type=AnnouncementType.SPECIAL_INSTANCE,
        is_budget_period_renewal=True,
        source_announcement=source,
        original_announcement_number=source.announcement_number,
        source_selection_method=SourceSelectionMethod.SOLE_SOURCE,
        performance_period_type=PerformancePeriodType.MULTIPLE_YEARS,
        performance_period_years=3,
        cost_sharing_percentage=25,
        agency_contact_name="Jane Doe",
    )
    application_package = ApplicationPackageFactory.create(announcement=announcement)
    ApplicationPackageRecipientFactory.create_batch(
        size=2,
        application_package=application_package,
        recipient_type=ApplicationPackageOpenToApplicant.INDIVIDUAL,
        email_address="shared@example.com",
    )

    db_session.expire_all()

    assert announcement.announcement_type == AnnouncementType.SPECIAL_INSTANCE
    assert announcement.source_announcement_id == source.announcement_id
    assert announcement.source_selection_method == SourceSelectionMethod.SOLE_SOURCE
    assert announcement.performance_period_type == PerformancePeriodType.MULTIPLE_YEARS

    recipients = announcement.application_packages[0].application_package_recipients
    assert len(recipients) == 2
    assert {r.recipient_type for r in recipients} == {ApplicationPackageOpenToApplicant.INDIVIDUAL}
    assert {r.email_address for r in recipients} == {"shared@example.com"}
