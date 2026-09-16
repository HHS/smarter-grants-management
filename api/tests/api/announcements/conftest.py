import uuid

import pytest

from src.constants.lookup_constants import AnnouncementCategory
from tests.db.models.factories import AssistanceListingFactory, UserApiKeyFactory


@pytest.fixture
def api_key_headers(enable_factory_create):
    api_key = UserApiKeyFactory.create()
    return {"X-API-Key": api_key.key_id}


@pytest.fixture
def assistance_listing(db_session, enable_factory_create):
    return AssistanceListingFactory.create()


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
