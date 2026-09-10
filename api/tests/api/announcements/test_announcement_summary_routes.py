import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from src.constants.lookup_constants import ApplicantType, FundingCategory, FundingInstrument
from src.db.models.announcement_models import AnnouncementSummary


def build_summary_request(is_forecast: bool = False) -> dict:
    now = datetime.now(UTC)
    return {
        "summary_description": "A summary for testing the Announcement API.",
        "is_cost_sharing": False,
        "post_timestamp": now.isoformat(),
        "close_timestamp": (now + timedelta(days=30)).isoformat(),
        "award_floor": 10_000,
        "award_ceiling": 100_000,
        "funding_categories": [next(iter(FundingCategory)).value],
        "funding_instruments": [next(iter(FundingInstrument)).value],
        "applicant_types": [next(iter(ApplicantType)).value],
        "agency_contact_description": None,
        "agency_email_address": None,
        "agency_email_address_description": None,
        "is_forecast": is_forecast,
    }


def build_summary_update_request(summary: AnnouncementSummary) -> dict:
    request = build_summary_request()
    request.pop("is_forecast")
    request["summary_description"] = summary.summary_description
    request["is_cost_sharing"] = summary.is_cost_sharing
    request["post_timestamp"] = summary.post_timestamp.isoformat()
    return request


def create_summary(db_session, announcement, is_forecast: bool = False) -> AnnouncementSummary:
    summary = AnnouncementSummary(
        announcement=announcement,
        summary_description="Existing summary",
        is_cost_sharing=False,
        is_forecast=is_forecast,
        post_timestamp=datetime.now(UTC),
        award_floor=10_000,
        award_ceiling=100_000,
    )
    summary.funding_categories = {next(iter(FundingCategory))}
    summary.funding_instruments = {next(iter(FundingInstrument))}
    summary.applicant_types = {next(iter(ApplicantType))}
    db_session.add(summary)
    db_session.commit()
    return summary


def test_announcement_summary_create_200(
    client,
    db_session,
    api_key_headers,
    announcement,
):
    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=build_summary_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["summary_description"] == "A summary for testing the Announcement API."
    assert data["is_forecast"] is False

    summary = db_session.execute(
        select(AnnouncementSummary).where(
            AnnouncementSummary.announcement_summary_id
            == uuid.UUID(data["announcement_summary_id"])
        )
    ).scalar_one()
    assert summary.announcement_id == announcement.announcement_id


def test_announcement_summary_create_sets_archive_timestamp_200(
    client,
    api_key_headers,
    announcement,
):
    request = build_summary_request()
    close_timestamp = datetime.fromisoformat(request["close_timestamp"])

    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 200
    archive_timestamp = datetime.fromisoformat(response.get_json()["data"]["archive_timestamp"])
    assert archive_timestamp == close_timestamp + timedelta(days=30)


def test_announcement_summary_create_forecast_200(
    client,
    api_key_headers,
    announcement,
):
    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=build_summary_request(is_forecast=True),
        headers=api_key_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["is_forecast"] is True


def test_announcement_summary_create_duplicate_type_422(
    client,
    db_session,
    api_key_headers,
    announcement,
):
    create_summary(db_session, announcement, is_forecast=False)

    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=build_summary_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 422
    assert "already exists" in response.get_json()["message"]


def test_announcement_summary_create_unknown_announcement_404(
    client,
    api_key_headers,
):
    response = client.post(
        f"/v1/announcements/{uuid.uuid4()}/summaries",
        json=build_summary_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_announcement_summary_create_invalid_award_values_422(
    client,
    api_key_headers,
    announcement,
):
    request = build_summary_request()
    request["award_floor"] = 200_000
    request["award_ceiling"] = 100_000

    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 422


def test_announcement_summary_create_invalid_timestamps_422(
    client,
    api_key_headers,
    announcement,
):
    request = build_summary_request()
    request["post_timestamp"], request["close_timestamp"] = (
        request["close_timestamp"],
        request["post_timestamp"],
    )

    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 422


def test_announcement_summary_create_no_auth_401(client, announcement):
    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=build_summary_request(),
    )

    assert response.status_code == 401


def test_announcement_summary_update_200(
    client,
    db_session,
    api_key_headers,
    announcement,
):
    summary = create_summary(db_session, announcement)
    request = build_summary_update_request(summary)
    request["summary_description"] = "Updated summary description"

    response = client.put(
        f"/v1/announcements/{announcement.announcement_id}/summaries/"
        f"{summary.announcement_summary_id}",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["summary_description"] == "Updated summary description"

    db_session.refresh(summary)
    assert summary.summary_description == "Updated summary description"


def test_announcement_summary_update_wrong_announcement_404(
    client,
    db_session,
    api_key_headers,
    announcement,
):
    from src.constants.lookup_constants import AnnouncementCategory
    from src.db.models.announcement_models import Announcement

    other_announcement = Announcement(
        announcement_number=f"TEST-{uuid.uuid4().hex[:8]}",
        announcement_title="Other Announcement",
        tagline="Another announcement",
        purpose_statement="Test summary ownership.",
        category=AnnouncementCategory.DISCRETIONARY,
        category_explanation=None,
    )
    db_session.add(other_announcement)
    db_session.commit()

    summary = create_summary(db_session, other_announcement)

    response = client.put(
        f"/v1/announcements/{announcement.announcement_id}/summaries/"
        f"{summary.announcement_summary_id}",
        json=build_summary_update_request(summary),
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_announcement_summary_update_unknown_summary_404(
    client,
    api_key_headers,
    announcement,
):
    request = build_summary_request()
    request.pop("is_forecast")

    response = client.put(
        f"/v1/announcements/{announcement.announcement_id}/summaries/{uuid.uuid4()}",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_announcement_summary_update_no_auth_401(
    client,
    db_session,
    announcement,
):
    summary = create_summary(db_session, announcement)

    response = client.put(
        f"/v1/announcements/{announcement.announcement_id}/summaries/"
        f"{summary.announcement_summary_id}",
        json=build_summary_update_request(summary),
    )

    assert response.status_code == 401
