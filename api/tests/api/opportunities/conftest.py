import uuid

import pytest

from src.constants.lookup_constants import OpportunityCategory
from src.db.models.assistance_listing_models import AssistanceListing
from tests.db.models.factories import OpportunityFactory, OpportunityGroupFactory, UserApiKeyFactory


@pytest.fixture
def api_key_headers(enable_factory_create):
    api_key = UserApiKeyFactory.create()
    return {"X-API-Key": api_key.key_id}


@pytest.fixture
def opportunity_group(enable_factory_create):
    return OpportunityGroupFactory.create()


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
def opportunity_request(opportunity_group, assistance_listing):
    return {
        "opportunity_group_id": str(opportunity_group.opportunity_group_id),
        "opportunity_number": f"TEST-{uuid.uuid4().hex[:8]}",
        "opportunity_title": "Test Opportunity",
        "tagline": "A test opportunity",
        "purpose_statement": "Test the Opportunity API.",
        "category": OpportunityCategory.DISCRETIONARY.value,
        "category_explanation": None,
        "assistance_listing_number": assistance_listing.assistance_listing_number,
    }


@pytest.fixture
def opportunity(enable_factory_create):
    return OpportunityFactory.create(
        category=OpportunityCategory.DISCRETIONARY,
        category_explanation=None,
    )
