import uuid

from sqlalchemy import select

from src.constants.lookup_constants import AnnouncementCategory
from src.db.models.announcement_models import Announcement, AnnouncementAssistanceListing


def test_announcement_create_200(
    client,
    db_session,
    api_key_headers,
    assistance_listing,
    announcement_request,
):
    response = client.post(
        "/v1/announcements",
        json=announcement_request,
        headers=api_key_headers,
    )

    assert response.status_code == 200

    response_json = response.get_json()
    assert response_json["message"] == "Success"

    data = response_json["data"]
    assert data["announcement_number"] == announcement_request["announcement_number"]
    assert data["announcement_title"] == announcement_request["announcement_title"]
    assert data["tagline"] == announcement_request["tagline"]
    assert data["purpose_statement"] == announcement_request["purpose_statement"]
    assert data["category"] == announcement_request["category"]
    assert data["category_explanation"] is None

    announcement = db_session.execute(
        select(Announcement).where(
            Announcement.announcement_id == uuid.UUID(data["announcement_id"])
        )
    ).scalar_one()

    link = db_session.execute(
        select(AnnouncementAssistanceListing).where(
            AnnouncementAssistanceListing.announcement_id == announcement.announcement_id
        )
    ).scalar_one()
    assert link.assistance_listing_id == assistance_listing.assistance_listing_id


def test_announcement_create_duplicate_number_422(
    client,
    api_key_headers,
    announcement_request,
):
    first_response = client.post(
        "/v1/announcements",
        json=announcement_request,
        headers=api_key_headers,
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/v1/announcements",
        json=announcement_request,
        headers=api_key_headers,
    )

    assert second_response.status_code == 422
    assert "already exists" in second_response.get_json()["message"]


def test_announcement_create_missing_required_fields_422(
    client,
    api_key_headers,
):
    response = client.post(
        "/v1/announcements",
        json={"announcement_title": "Missing almost everything"},
        headers=api_key_headers,
    )

    assert response.status_code == 422
    assert response.get_json()["errors"]


def test_announcement_create_other_requires_category_explanation_422(
    client,
    api_key_headers,
    announcement_request,
):
    announcement_request["category"] = AnnouncementCategory.OTHER.value
    announcement_request["category_explanation"] = ""

    response = client.post(
        "/v1/announcements",
        json=announcement_request,
        headers=api_key_headers,
    )

    assert response.status_code == 422
    assert any(
        "explanation of the category is required" in error["message"].lower()
        for error in response.get_json()["errors"]
    )


def test_announcement_create_unknown_assistance_listing_404(
    client,
    api_key_headers,
    announcement_request,
):
    announcement_request["assistance_listing_number"] = "99.999"

    response = client.post(
        "/v1/announcements",
        json=announcement_request,
        headers=api_key_headers,
    )

    assert response.status_code == 404
    assert "Could not find assistance listing" in response.get_json()["message"]


def test_announcement_create_no_auth_401(client, announcement_request):
    response = client.post("/v1/announcements", json=announcement_request)

    assert response.status_code == 401
