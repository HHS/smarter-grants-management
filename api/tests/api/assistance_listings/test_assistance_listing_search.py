import pytest
from sqlalchemy import update

from src.db.models.assistance_listing_models import AssistanceListing
from tests.conftest import BaseTestClass
from tests.db.models.factories import AssistanceListingFactory, UserApiKeyFactory


@pytest.fixture
def user_api_key(enable_factory_create):
    return UserApiKeyFactory.create()


@pytest.fixture
def user_api_key_id(user_api_key):
    return user_api_key.key_id


class TestAssistanceListingSearch(BaseTestClass):

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup_assistance_listing(cls, db_session, enable_factory_create):
        # Set all assistance listings to not be active
        # so that any data from other tests won't be picked up
        db_session.execute(update(AssistanceListing).values(is_active=False))
        db_session.commit()

        AssistanceListingFactory.create(
            assistance_listing_number="XA.001", program_title="chemical processing"
        )
        AssistanceListingFactory.create(
            assistance_listing_number="XA.002", program_title="chemistry research"
        )
        AssistanceListingFactory.create(
            assistance_listing_number="XA.003", program_title="secret project"
        )
        AssistanceListingFactory.create(assistance_listing_number="YB.100", program_title="pizza")
        AssistanceListingFactory.create(
            assistance_listing_number="YB.101", program_title="advanced pizza"
        )
        AssistanceListingFactory.create(
            assistance_listing_number="YB.102", program_title="pizza party productivity"
        )

    @pytest.mark.parametrize(
        "query,expected_alns",
        [
            # No query gives everything
            (None, ["XA.001", "XA.002", "XA.003", "YB.100", "YB.101", "YB.102"]),
            # Querying by ALN
            ("XA.", ["XA.001", "XA.002", "XA.003"]),
            ("XA.001", ["XA.001"]),
            ("YB.1", ["YB.100", "YB.101", "YB.102"]),
            ("ZC", []),
            # Querying by program title
            ("chemistry", ["XA.002"]),
            ("chem*", ["XA.001", "XA.002"]),
            ("pro*", ["XA.001", "XA.003", "YB.102"]),
            ("pizza OR secret", ["XA.003", "YB.100", "YB.101", "YB.102"]),
            ("dog", []),
        ],
    )
    def test_assistance_listing_search_query_200(
        self, client, user_api_key_id, query, expected_alns
    ):

        request = {"pagination": {"page_offset": 1, "page_size": 25}}
        if query is not None:
            request["query"] = query

        response = client.post(
            "/v1/assistance-listings/search", json=request, headers={"X-API-Key": user_api_key_id}
        )

        assert response.status_code == 200
        json = response.get_json()

        fetched_alns = [aln["assistance_listing_number"] for aln in json["data"]]
        assert fetched_alns == expected_alns

    @pytest.mark.parametrize(
        "pagination,expected_alns",
        [
            # Paging
            ({"page_offset": 1, "page_size": 3}, ["XA.001", "XA.002", "XA.003"]),
            ({"page_offset": 2, "page_size": 2}, ["XA.003", "YB.100"]),
            ({"page_offset": 12, "page_size": 5}, []),
            # Sort order
            (
                {
                    "page_offset": 1,
                    "page_size": 2,
                    "sort_order": [{"order_by": "program_title", "sort_direction": "descending"}],
                },
                ["XA.003", "YB.102"],
            ),
            (
                {
                    "page_offset": 1,
                    "page_size": 3,
                    "sort_order": [{"order_by": "program_title", "sort_direction": "ascending"}],
                },
                ["YB.101", "XA.001", "XA.002"],
            ),
        ],
    )
    def test_assistance_listing_pagination_200(
        self, client, user_api_key_id, pagination, expected_alns
    ):
        request = {"pagination": pagination}
        response = client.post(
            "/v1/assistance-listings/search", json=request, headers={"X-API-Key": user_api_key_id}
        )

        assert response.status_code == 200
        json = response.get_json()

        fetched_alns = [aln["assistance_listing_number"] for aln in json["data"]]
        assert fetched_alns == expected_alns

    def test_assistance_listing_search_bad_api_key_401(self, client):
        request = {"pagination": {"page_offset": 1, "page_size": 25}}
        response = client.post(
            "/v1/assistance-listings/search", json=request, headers={"X-API-Key": "Bad key"}
        )
        assert response.status_code == 401

    def test_assistance_listing_search_bad_jwt_401(self, client):
        request = {"pagination": {"page_offset": 1, "page_size": 25}}
        response = client.post(
            "/v1/assistance-listings/search", json=request, headers={"X-MGMT-Token": "Bad id"}
        )
        assert response.status_code == 401

    def test_assistance_listing_search_no_auth_401(self, client):
        request = {"pagination": {"page_offset": 1, "page_size": 25}}
        response = client.post("/v1/assistance-listings/search", json=request)
        assert response.status_code == 401

    def test_assistance_listing_search_no_pagination_422(self, client, user_api_key_id):
        response = client.post(
            "/v1/assistance-listings/search", json={}, headers={"X-API-Key": user_api_key_id}
        )
        assert response.status_code == 422

        assert response.get_json()["errors"][0] == {
            "field": "pagination",
            "type": "required",
            "message": "Missing data for required field.",
            "value": None,
        }
