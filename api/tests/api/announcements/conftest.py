import uuid

import pytest

from src.constants.lookup_constants import AnnouncementCategory
from src.db.models.announcement_models import Announcement
from src.db.models.assistance_listing_models import AssistanceListing
from tests.db.models.factories import UserApiKeyFactory


@pytest.fixture
def api_key_headers(enable_factory_create):
    api_key = UserApiKeyFactory.create()
    return {"X-API-Key": api_key.key_id}


@pytest.fixture
def assistance_listing(db_session):
    number = uuid.uuid4().int % 1000

    assistance_listing = AssistanceListing(
        assistance_listing_id=uuid.uuid4(),
        assistance_listing_number=f"12.{number:03}",
        is_active=True,
        published_date=None,
        program_title="Test Assistance Listing",
    )
    db_session.add(assistance_listing)
    db_session.commit()

    return assistance_listing


@pytest.fixture
def announcement_request(assistance_listing):
    return {
        "announcement_number": f"TEST-{uuid.uuid4().hex[:8]}",
        "announcement_title": "Test Announcement",
        "tagline": "A test announcement",
        "purpose_statement": "Test the Announcement API.",
        "category": AnnouncementCategory.DISCRETIONARY.value,
        "category_explanation": None,
        "assistance_listing_number": assistance_listing.assistance_listing_number,
    }


@pytest.fixture
def announcement(db_session):
    announcement = Announcement(
        announcement_number=f"TEST-{uuid.uuid4().hex[:8]}",
        announcement_title="Test Announcement",
        tagline="A test announcement",
        purpose_statement="Test the Announcement API.",
        category=AnnouncementCategory.DISCRETIONARY,
        category_explanation=None,
    )
    db_session.add(announcement)
    db_session.commit()
    return announcement
