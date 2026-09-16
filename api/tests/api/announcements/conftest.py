import uuid
from datetime import datetime
from typing import Any

import pytest

from src.constants.lookup_constants import AnnouncementCategory, ApplicationPackageOpenToApplicant
from src.util import datetime_util
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


def create_application_package_request(
    application_package_title: str = "Proposal for Advanced Research",
    public_application_package_id: str = "ABC-123-456",
    grace_period: int = 5,
    opening_timestamp: datetime | None = None,
    closing_timestamp: datetime | None = None,
    contact_info: str | None = "Bob Smith\nFakeMail@fake.com",
    open_to_applicants: list[ApplicationPackageOpenToApplicant] | None = None,
) -> dict[str, Any]:

    if opening_timestamp is None:
        opening_timestamp = datetime_util.utcnow()
    if closing_timestamp is None:
        closing_timestamp = datetime_util.utcnow()

    if open_to_applicants is None:
        open_to_applicants = [
            ApplicationPackageOpenToApplicant.INDIVIDUAL,
            ApplicationPackageOpenToApplicant.ORGANIZATION,
        ]

    request = {
        "application_package_title": application_package_title,
        "public_application_package_id": public_application_package_id,
        "grace_period": grace_period,
        "opening_timestamp": opening_timestamp.isoformat(),
        "closing_timestamp": closing_timestamp.isoformat(),
        "contact_info": contact_info,
        "open_to_applicants": open_to_applicants,
    }

    return request
