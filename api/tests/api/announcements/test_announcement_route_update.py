from src.constants.lookup_constants import AnnouncementCategory
from tests.db.models.factories import AnnouncementFactory


def build_update_request(announcement):
    category_explanation = announcement.category_explanation
    if announcement.category == AnnouncementCategory.OTHER and not category_explanation:
        category_explanation = "Other category explanation"

    return {
        "announcement_title": announcement.announcement_title,
        "tagline": announcement.tagline,
        "purpose_statement": announcement.purpose_statement,
        "category": announcement.category.value,
        "category_explanation": category_explanation,
    }


def test_announcement_update_200(
    client,
    db_session,
    api_key_headers,
):
    announcement = AnnouncementFactory.create()

    request = build_update_request(announcement)
    request["announcement_title"] = "Updated Announcement Title"
    request["tagline"] = "Updated tagline"
    request["purpose_statement"] = "Updated purpose statement"

    response = client.put(
        f"/v1/announcements/{announcement.announcement_id}",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["announcement_title"] == request["announcement_title"]
    assert data["tagline"] == request["tagline"]
    assert data["purpose_statement"] == request["purpose_statement"]

    db_session.refresh(announcement)
    assert announcement.announcement_title == request["announcement_title"]
    assert announcement.tagline == request["tagline"]
    assert announcement.purpose_statement == request["purpose_statement"]


def test_announcement_update_other_requires_category_explanation_422(
    client,
    api_key_headers,
):
    announcement = AnnouncementFactory.create()
    request = build_update_request(announcement)
    request["category"] = AnnouncementCategory.OTHER.value
    request["category_explanation"] = ""

    response = client.put(
        f"/v1/announcements/{announcement.announcement_id}",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 422


def test_announcement_update_no_auth_401(client, enable_factory_create):
    announcement = AnnouncementFactory.create()
    response = client.put(
        f"/v1/announcements/{announcement.announcement_id}",
        json=build_update_request(announcement),
    )

    assert response.status_code == 401
