from tests.db.models.factories import AnnouncementFactory, AnnouncementSummaryFactory


def list_request(**filters):
    payload = {
        "pagination": {
            "page_offset": 1,
            "page_size": 100,
        }
    }
    if filters:
        payload["filters"] = filters
    return payload


def test_announcement_list_returns_announcements(
    client,
    db_session,
    api_key_headers,
):
    announcement_summaries = AnnouncementSummaryFactory.create_batch(size=3)
    announcement_ids = {str(a.announcement_id) for a in announcement_summaries}

    response = client.post(
        "/v1/announcements/list",
        json=list_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    response_json = response.get_json()
    returned_ids = {item["announcement_id"] for item in response_json["data"]}
    assert announcement_ids.issubset(returned_ids)

    assert response_json["pagination_info"]["total_records"] >= 3


def test_announcement_list_paginates(
    client,
    db_session,
    api_key_headers,
):
    AnnouncementFactory.create_batch(size=3)

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
