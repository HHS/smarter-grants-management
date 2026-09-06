import uuid

from src.db.models.opportunity_models import OpportunityAssistanceListing


def test_opportunity_get_200(
    client,
    db_session,
    api_key_headers,
    opportunity,
    assistance_listing,
):
    db_session.add(
        OpportunityAssistanceListing(
            opportunity=opportunity,
            assistance_listing=assistance_listing,
        )
    )
    db_session.commit()

    response = client.get(
        f"/v1/opportunities/{opportunity.opportunity_id}",
        headers=api_key_headers,
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["opportunity_id"] == str(opportunity.opportunity_id)
    assert data["opportunity_group_id"] == str(opportunity.opportunity_group_id)
    assert data["opportunity_number"] == opportunity.opportunity_number
    assert data["opportunity_title"] == opportunity.opportunity_title
    assert data["tagline"] == opportunity.tagline
    assert data["purpose_statement"] == opportunity.purpose_statement
    assert data["category"] == opportunity.category.value

    assistance_listings = data["opportunity_assistance_listings"]
    assert len(assistance_listings) == 1
    assert (
        assistance_listings[0]["assistance_listing"]["assistance_listing_number"]
        == assistance_listing.assistance_listing_number
    )


def test_opportunity_get_404(
    client,
    api_key_headers,
):
    response = client.get(
        f"/v1/opportunities/{uuid.uuid4()}",
        headers=api_key_headers,
    )

    assert response.status_code == 404
    assert "Could not find opportunity with ID" in response.get_json()["message"]


def test_opportunity_get_no_auth_401(client, opportunity):
    response = client.get(f"/v1/opportunities/{opportunity.opportunity_id}")

    assert response.status_code == 401
