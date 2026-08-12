import uuid
from datetime import date

import pytest

from src.adapters.simpler_grants.client import SimplerResponseError, SimplerResponseException
from src.adapters.simpler_grants.models import (
    SimplerOpportunity,
    SimplerOpportunityGetResponse,
    SimplerOpportunityStatus,
    SimplerOpportunitySummary,
)
from src.auth.api_jwt_auth import create_jwt_for_user
from tests.db.models.factories import MgmtUserApiKeyFactory, MgmtUserFactory


@pytest.fixture
def user_with_jwt(enable_factory_create, db_session):
    user = MgmtUserFactory.create()
    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()
    return user, token


@pytest.fixture
def user_with_api_key(enable_factory_create, db_session):
    user = MgmtUserFactory.create()
    api_key = MgmtUserApiKeyFactory.create(mgmt_user=user, key_id="test-api-key")
    db_session.commit()
    return user, api_key.key_id


class TestGetOpportunity:
    def test_get_opportunity_with_jwt_auth_success(
        self, client, user_with_jwt, mock_simpler_grants_client
    ):
        user, token = user_with_jwt
        opportunity_id = uuid.uuid4()

        mock_simpler_grants_client.add_opportunity_response(
            opportunity_id,
            SimplerOpportunityGetResponse(
                message="Success",
                data=SimplerOpportunity(
                    opportunity_id=opportunity_id,
                    opportunity_title="Test Opportunity",
                    opportunity_status=SimplerOpportunityStatus.POSTED,
                    summary=SimplerOpportunitySummary(post_date=date(2010, 1, 1)),
                ),
            ),
        )

        response = client.get(
            f"/alpha/proof_of_concept/opportunities/{opportunity_id}",
            headers={"X-MGMT-Token": token},
        )

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["opportunity_id"] == str(opportunity_id)
        assert data["opportunity_title"] == "Test Opportunity"
        assert data["opportunity_status"] == "posted"
        assert data["summary"]["post_date"] == "2010-01-01"

    def test_get_opportunity_with_api_key_auth_success(
        self, client, user_with_api_key, mock_simpler_grants_client
    ):
        user, api_key = user_with_api_key
        opportunity_id = uuid.uuid4()

        mock_simpler_grants_client.add_opportunity_response(
            opportunity_id,
            SimplerOpportunityGetResponse(
                message="Success",
                data=SimplerOpportunity(
                    opportunity_id=opportunity_id,
                    opportunity_title="Another Test Opportunity",
                    opportunity_status=SimplerOpportunityStatus.CLOSED,
                    summary=SimplerOpportunitySummary(post_date=date(2020, 5, 15)),
                ),
            ),
        )

        response = client.get(
            f"/alpha/proof_of_concept/opportunities/{opportunity_id}",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["opportunity_id"] == str(opportunity_id)
        assert data["opportunity_title"] == "Another Test Opportunity"
        assert data["opportunity_status"] == "closed"
        assert data["summary"]["post_date"] == "2020-05-15"

    def test_get_opportunity_with_null_fields(
        self, client, user_with_jwt, mock_simpler_grants_client
    ):
        user, token = user_with_jwt
        opportunity_id = uuid.uuid4()

        mock_simpler_grants_client.add_opportunity_response(
            opportunity_id,
            SimplerOpportunityGetResponse(
                message="Success",
                data=SimplerOpportunity(
                    opportunity_id=opportunity_id,
                    opportunity_title=None,
                    opportunity_status=None,
                    summary=None,
                ),
            ),
        )

        response = client.get(
            f"/alpha/proof_of_concept/opportunities/{opportunity_id}",
            headers={"X-MGMT-Token": token},
        )

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["opportunity_id"] == str(opportunity_id)
        assert data["opportunity_title"] is None
        assert data["opportunity_status"] is None
        assert data["summary"] is None

    def test_get_opportunity_not_found(self, client, user_with_jwt, mock_simpler_grants_client):
        user, token = user_with_jwt
        opportunity_id = uuid.uuid4()

        mock_simpler_grants_client.add_error_response(
            opportunity_id,
            SimplerResponseException(
                SimplerResponseError(
                    message="Opportunity not found",
                    status_code=404,
                )
            ),
        )

        response = client.get(
            f"/alpha/proof_of_concept/opportunities/{opportunity_id}",
            headers={"X-MGMT-Token": token},
        )

        assert response.status_code == 404
        assert response.get_json()["message"] == "Opportunity not found"

    def test_get_opportunity_simpler_grants_error(
        self, client, user_with_jwt, mock_simpler_grants_client
    ):
        user, token = user_with_jwt
        opportunity_id = uuid.uuid4()

        mock_simpler_grants_client.add_error_response(
            opportunity_id,
            SimplerResponseException(
                SimplerResponseError(
                    message="Internal server error",
                    status_code=500,
                )
            ),
        )

        response = client.get(
            f"/alpha/proof_of_concept/opportunities/{opportunity_id}",
            headers={"X-MGMT-Token": token},
        )

        assert response.status_code == 500
        assert response.get_json()["message"] == "Internal server error"

    def test_get_opportunity_no_auth_401(self, client):
        opportunity_id = uuid.uuid4()

        response = client.get(
            f"/alpha/proof_of_concept/opportunities/{opportunity_id}",
        )

        assert response.status_code == 401

    def test_get_opportunity_invalid_jwt_401(self, client):
        opportunity_id = uuid.uuid4()

        response = client.get(
            f"/alpha/proof_of_concept/opportunities/{opportunity_id}",
            headers={"X-MGMT-Token": "invalid-token"},
        )

        assert response.status_code == 401

    def test_get_opportunity_invalid_api_key_401(self, client):
        opportunity_id = uuid.uuid4()

        response = client.get(
            f"/alpha/proof_of_concept/opportunities/{opportunity_id}",
            headers={"X-API-Key": "invalid-api-key"},
        )

        assert response.status_code == 401
