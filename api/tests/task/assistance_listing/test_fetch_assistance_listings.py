from datetime import datetime

import pytest
import pytz
from sqlalchemy import select

from src.adapters.sam_gov import MockSamGovClient
from src.adapters.sam_gov.models import SamAssistanceListingData
from src.db.models.assistance_listing_models import AssistanceListing
from src.task.assistance_listing.fetch_assistance_listings import (
    FetchAssistanceListingConfig,
    FetchAssistanceListingsTask,
)
from tests.db.models.factories import AssistanceListingFactory


def test_fetch_assistance_listings(db_session, enable_factory_create):
    """
    Test the assistance listing task - this is the expected behavior of each ALN

    * FT.111 - Already exists, being updated
    * FT.222 - Already exists, no changes
    * FT.333 - Already exists, not returned by sam.gov (no longer active)
    * FT.444 - Already exists, not returned by sam.gov (no longer active, but was already marked that way)
    * FT.555 - Does not exist yet, new
    * FT.666 - Does not exist yet, new
    * FT.777 - Does not exist yet, new but marked as inactive
    """

    fetched_assistance_listings = [
        SamAssistanceListingData(
            assistanceListingId="FT.111",
            title="1st",
            status="Active",
            publishedDate=datetime(2026, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
        ),
        SamAssistanceListingData(
            assistanceListingId="FT.222",
            title="2nd",
            status="Active",
            publishedDate=datetime(2026, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
        ),
        SamAssistanceListingData(
            assistanceListingId="FT.555",
            title="5th",
            status="Active",
            publishedDate=datetime(2026, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
        ),
        SamAssistanceListingData(
            assistanceListingId="FT.666",
            title="6th",
            status="Active",
            publishedDate=datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
        ),
        SamAssistanceListingData(
            assistanceListingId="FT.777",
            title="7th",
            status="Inactive",
            publishedDate=datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
        ),
    ]

    existing_assistance_listings = [
        AssistanceListingFactory.create(
            assistance_listing_number="FT.111", program_title="Old program title"
        ),
        AssistanceListingFactory.create(assistance_listing_number="FT.222", program_title="2nd"),
        AssistanceListingFactory.create(assistance_listing_number="FT.333", is_active=True),
        AssistanceListingFactory.create(assistance_listing_number="FT.444", is_active=False),
    ]

    client = MockSamGovClient()
    client.add_mock_assistance_listings(fetched_assistance_listings)

    task = FetchAssistanceListingsTask(db_session, client=client)

    task.run()

    # Fetch the ALNs from the DB
    db_session.expire_all()
    db_alns = (
        db_session.execute(
            select(AssistanceListing)
            .where(AssistanceListing.assistance_listing_number.ilike("FT.%"))
            .order_by(AssistanceListing.assistance_listing_number.asc())
        )
        .scalars()
        .all()
    )

    assert len(db_alns) == 7

    assert db_alns[0].assistance_listing_number == "FT.111"
    assert db_alns[0].program_title == "1st"
    assert db_alns[0].is_active is True
    assert db_alns[0].published_date == datetime(2026, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)

    assert db_alns[1].assistance_listing_number == "FT.222"
    assert db_alns[1].program_title == "2nd"
    assert db_alns[1].is_active is True
    assert db_alns[1].published_date == datetime(2026, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)

    assert db_alns[2].assistance_listing_number == "FT.333"
    assert db_alns[2].program_title == existing_assistance_listings[2].program_title
    assert db_alns[2].is_active is False
    assert db_alns[2].published_date == existing_assistance_listings[2].published_date

    assert db_alns[3].assistance_listing_number == "FT.444"
    assert db_alns[3].program_title == existing_assistance_listings[3].program_title
    assert db_alns[3].is_active is False
    assert db_alns[3].published_date == existing_assistance_listings[3].published_date

    assert db_alns[4].assistance_listing_number == "FT.555"
    assert db_alns[4].program_title == "5th"
    assert db_alns[4].is_active is True
    assert db_alns[4].published_date == datetime(2026, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)

    assert db_alns[5].assistance_listing_number == "FT.666"
    assert db_alns[5].program_title == "6th"
    assert db_alns[5].is_active is True
    assert db_alns[5].published_date == datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)

    assert db_alns[6].assistance_listing_number == "FT.777"
    assert db_alns[6].program_title == "7th"
    assert db_alns[6].is_active is False
    assert db_alns[6].published_date == datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)

    assert task.metrics[task.Metrics.FETCHED_ASSISTANCE_LISTINGS] == 5
    assert task.metrics[task.Metrics.PAGES_FETCHED] == 1
    assert task.metrics[task.Metrics.UPDATED_ASSISTANCE_LISTINGS] == 2
    assert task.metrics[task.Metrics.NEW_ASSISTANCE_LISTINGS] == 3
    assert task.metrics[task.Metrics.INACTIVE_ASSISTANCE_LISTINGS] == 2
    assert task.metrics[task.Metrics.TOTAL_ASSISTANCE_LISTINGS] == 7


def test_fetch_assistance_listing_paginates(db_session):
    """Verify pagination works properly"""

    fetched_assistance_listings = []
    for i in range(25):
        fetched_assistance_listings.append(
            SamAssistanceListingData(
                assistanceListingId=f"00.{i}",
                title=f"ALN #{i}",
                status="Active",
                publishedDate=datetime(2026, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
            )
        )

    client = MockSamGovClient()
    client.add_mock_assistance_listings(fetched_assistance_listings)

    config = FetchAssistanceListingConfig(FETCH_ASSISTANCE_LISTING_PAGE_SIZE=3)
    task = FetchAssistanceListingsTask(db_session, client=client, config=config)

    assistance_listings = task.fetch_assistance_listings()
    assert len(assistance_listings) == len(fetched_assistance_listings)
    assert task.metrics[task.Metrics.PAGES_FETCHED] == 9


def test_fetch_assistance_listing_paginates_up_to_max(db_session):
    fetched_assistance_listings = []
    for i in range(25):
        fetched_assistance_listings.append(
            SamAssistanceListingData(
                assistanceListingId=f"00.{i}",
                title=f"ALN #{i}",
                status="Active",
                publishedDate=datetime(2026, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
            )
        )

    client = MockSamGovClient()
    client.add_mock_assistance_listings(fetched_assistance_listings)

    config = FetchAssistanceListingConfig(
        FETCH_ASSISTANCE_LISTING_PAGE_SIZE=1, FETCH_ASSISTANCE_LISTING_MAX_PAGE_NUMBER=5
    )
    task = FetchAssistanceListingsTask(db_session, client=client, config=config)

    with pytest.raises(ValueError, match="Fetched more than the configured number of pages"):
        task.fetch_assistance_listings()

    assert task.metrics[task.Metrics.PAGES_FETCHED] == 5
