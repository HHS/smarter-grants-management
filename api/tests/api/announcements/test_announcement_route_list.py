import uuid

from src.constants.lookup_constants import AnnouncementCategory
from src.db.models.announcement_models import Announcement


def list_request(**filters):
    payload = {
        "pagination": {
            "page_offset": 1,
            "page_size": 25,
        }
    }
    if filters:
        payload["filters"] = filters
    return payload


def create_announcement(db_session, *, number=None, title=None):
    announcement = Announcement(
        announcement_number=number or f"TEST-{uuid.uuid4().hex[:8]}",
        announcement_title=title or "Test Announcement",
        tagline="A test announcement",
        purpose_statement="Test the Announcement API.",
        category=AnnouncementCategory.DISCRETIONARY,
        category_explanation=None,
    )
    db_session.add(announcement)
    db_session.commit()
    return announcement


def test_announcement_list_returns_announcements(
    client,
    db_session,
    api_key_headers,
):
    announcements = [create_announcement(db_session) for _ in range(3)]

    response = client.post(
        "/v1/announcements/list",
        json=list_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    response_json = response.get_json()
    returned_ids = {item["announcement_id"] for item in response_json["data"]}

    for announcement in announcements:
        assert str(announcement.announcement_id) in returned_ids

    assert response_json["pagination_info"]["total_records"] >= 3


def test_announcement_list_query_matches_number(
    client,
    db_session,
    api_key_headers,
):
    target = create_announcement(db_session, number="SPECIAL-SEARCH-123")
    create_announcement(db_session, number="NOT-A-MATCH")

    response = client.post(
        "/v1/announcements/list",
        json=list_request(query="SEARCH-123"),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    ids = [item["announcement_id"] for item in response.get_json()["data"]]
    assert ids == [str(target.announcement_id)]


def test_announcement_list_query_matches_title(
    client,
    db_session,
    api_key_headers,
):
    target = create_announcement(
        db_session,
        title="Distinctive Marmot Research Program",
    )
    create_announcement(db_session, title="Entirely Different Announcement")

    response = client.post(
        "/v1/announcements/list",
        json=list_request(query="marmot research"),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    ids = [item["announcement_id"] for item in response.get_json()["data"]]
    assert ids == [str(target.announcement_id)]


def test_announcement_list_paginates(
    client,
    db_session,
    api_key_headers,
):
    for _ in range(3):
        create_announcement(db_session)

    response = client.post(
        "/v1/announcements/list",
        json={
            "pagination": {
                "page_offset": 1,
                "page_size": 2,
            }
        },
        headers=api_key_headers,
    )

    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 2
    assert response.get_json()["pagination_info"]["page_size"] == 2


def test_announcement_list_no_auth_401(client):
    response = client.post(
        "/v1/announcements/list",
        json=list_request(),
    )

    assert response.status_code == 401
