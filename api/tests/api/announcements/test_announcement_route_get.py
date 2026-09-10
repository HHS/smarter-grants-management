import uuid

from src.db.models.announcement_models import AnnouncementAssistanceListing


def test_announcement_get_200(
    client,
    db_session,
    api_key_headers,
    announcement,
    assistance_listing,
):
    db_session.add(
        AnnouncementAssistanceListing(
            announcement=announcement,
            assistance_listing=assistance_listing,
        )
    )
    db_session.commit()

    response = client.get(
        f"/v1/announcements/{announcement.announcement_id}",
        headers=api_key_headers,
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["announcement_id"] == str(announcement.announcement_id)
    assert data["announcement_number"] == announcement.announcement_number
    assert data["announcement_title"] == announcement.announcement_title
    assert data["tagline"] == announcement.tagline
    assert data["purpose_statement"] == announcement.purpose_statement
    assert data["category"] == announcement.category.value

    assistance_listings = data["announcement_assistance_listings"]
    assert len(assistance_listings) == 1
    assert (
        assistance_listings[0]["assistance_listing"]["assistance_listing_number"]
        == assistance_listing.assistance_listing_number
    )


def test_announcement_get_404(
    client,
    api_key_headers,
):
    response = client.get(
        f"/v1/announcements/{uuid.uuid4()}",
        headers=api_key_headers,
    )

    assert response.status_code == 404
    assert "Could not find announcement with ID" in response.get_json()["message"]


def test_announcement_get_no_auth_401(client, announcement):
    response = client.get(f"/v1/announcements/{announcement.announcement_id}")

    assert response.status_code == 401
