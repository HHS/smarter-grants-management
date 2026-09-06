import uuid

from sqlalchemy import select

from src.constants.lookup_constants import OpportunityAuditEvent, OpportunityCategory
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit
from src.db.models.opportunity_models import Opportunity, OpportunityAssistanceListing


def test_opportunity_create_200(
    client,
    db_session,
    api_key_headers,
    opportunity_group,
    assistance_listing,
    opportunity_request,
):
    response = client.post(
        "/v1/opportunities",
        json=opportunity_request,
        headers=api_key_headers,
    )

    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["message"] == "Success"

    data = response_json["data"]
    assert data["opportunity_number"] == opportunity_request["opportunity_number"]
    assert data["opportunity_title"] == opportunity_request["opportunity_title"]
    assert data["tagline"] == opportunity_request["tagline"]
    assert data["purpose_statement"] == opportunity_request["purpose_statement"]
    assert data["category"] == opportunity_request["category"]
    assert data["category_explanation"] is None
    assert data["opportunity_group_id"] == str(opportunity_group.opportunity_group_id)

    opportunity = db_session.execute(
        select(Opportunity).where(Opportunity.opportunity_id == uuid.UUID(data["opportunity_id"]))
    ).scalar_one()

    link = db_session.execute(
        select(OpportunityAssistanceListing).where(
            OpportunityAssistanceListing.opportunity_id == opportunity.opportunity_id
        )
    ).scalar_one()
    assert link.assistance_listing_id == assistance_listing.assistance_listing_id

    audit = db_session.execute(
        select(OpportunityGroupAudit).where(
            OpportunityGroupAudit.opportunity_id == opportunity.opportunity_id
        )
    ).scalar_one()
    assert audit.opportunity_group_id == opportunity_group.opportunity_group_id
    assert audit.opportunity_audit_event == OpportunityAuditEvent.OPPORTUNITY_CREATED


def test_opportunity_create_duplicate_number_422(
    client,
    api_key_headers,
    opportunity_request,
):
    first_response = client.post(
        "/v1/opportunities",
        json=opportunity_request,
        headers=api_key_headers,
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/v1/opportunities",
        json=opportunity_request,
        headers=api_key_headers,
    )

    assert second_response.status_code == 422
    assert "already exists" in second_response.get_json()["message"]


def test_opportunity_create_missing_required_fields_422(
    client,
    api_key_headers,
):
    response = client.post(
        "/v1/opportunities",
        json={"opportunity_title": "Missing almost everything"},
        headers=api_key_headers,
    )

    assert response.status_code == 422
    assert response.get_json()["errors"]


def test_opportunity_create_other_requires_category_explanation_422(
    client,
    api_key_headers,
    opportunity_request,
):
    opportunity_request["category"] = OpportunityCategory.OTHER.value
    opportunity_request["category_explanation"] = ""

    response = client.post(
        "/v1/opportunities",
        json=opportunity_request,
        headers=api_key_headers,
    )

    assert response.status_code == 422
    assert any(
        "explanation of the category is required" in error["message"].lower()
        for error in response.get_json()["errors"]
    )


def test_opportunity_create_unknown_group_404(
    client,
    api_key_headers,
    opportunity_request,
):
    opportunity_request["opportunity_group_id"] = str(uuid.uuid4())

    response = client.post(
        "/v1/opportunities",
        json=opportunity_request,
        headers=api_key_headers,
    )

    assert response.status_code == 404
    assert "Could not find opportunity group" in response.get_json()["message"]


def test_opportunity_create_unknown_assistance_listing_404(
    client,
    api_key_headers,
    opportunity_request,
):
    opportunity_request["assistance_listing_number"] = "99.999"

    response = client.post(
        "/v1/opportunities",
        json=opportunity_request,
        headers=api_key_headers,
    )

    assert response.status_code == 404
    assert "Could not find assistance listing" in response.get_json()["message"]


def test_opportunity_create_no_auth_401(client, opportunity_request):
    response = client.post("/v1/opportunities", json=opportunity_request)

    assert response.status_code == 401
