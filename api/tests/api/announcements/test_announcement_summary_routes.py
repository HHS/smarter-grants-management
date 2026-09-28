import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from src.constants.lookup_constants import (
    AnnouncementAuditEvent,
    ApplicantType,
    FundingCategory,
    FundingInstrument,
)
from src.db.models.announcement_models import AnnouncementAudit, AnnouncementSummary
from src.util import datetime_util
from tests.db.models.factories import AnnouncementFactory, AnnouncementSummaryFactory


def build_summary_request(is_forecast: bool = False) -> dict:

    return {
        "summary_description": "A summary for testing the Announcement API.",
        "is_cost_sharing": False,
        "post_timestamp": datetime_util.utcnow().isoformat(),
        "close_timestamp": (datetime_util.utcnow() + timedelta(days=30)).isoformat(),
        "award_floor": 10_000,
        "award_ceiling": 100_000,
        "funding_categories": random.choices(list(FundingCategory)),
        "funding_instruments": random.choices(list(FundingInstrument)),
        "applicant_types": random.choices(list(ApplicantType)),
        "agency_contact_description": None,
        "agency_email_address": None,
        "agency_email_address_description": None,
        "is_forecast": is_forecast,
    }


def build_summary_update_request() -> dict:
    request = build_summary_request()
    request.pop("is_forecast")
    return request


def build_update_request_from_summary(summary: AnnouncementSummary) -> dict:
    def _iso(value):
        return value.isoformat() if value is not None else None

    return {
        "summary_description": summary.summary_description,
        "is_cost_sharing": summary.is_cost_sharing,
        "post_timestamp": _iso(summary.post_timestamp),
        "close_timestamp": _iso(summary.close_timestamp),
        "close_timestamp_description": summary.close_timestamp_description,
        "archive_timestamp": _iso(summary.archive_timestamp),
        "expected_number_of_awards": summary.expected_number_of_awards,
        "estimated_total_program_funding": summary.estimated_total_program_funding,
        "award_floor": summary.award_floor,
        "award_ceiling": summary.award_ceiling,
        "additional_info_url": summary.additional_info_url,
        "additional_info_url_description": summary.additional_info_url_description,
        "forecasted_post_timestamp": _iso(summary.forecasted_post_timestamp),
        "forecasted_close_timestamp": _iso(summary.forecasted_close_timestamp),
        "forecasted_close_timestamp_description": summary.forecasted_close_timestamp_description,
        "estimated_award_date": _iso(summary.estimated_award_date),
        "estimated_project_start_date": _iso(summary.estimated_project_start_date),
        "fiscal_year": summary.fiscal_year,
        "funding_categories": list(summary.funding_categories),
        "funding_category_description": summary.funding_category_description,
        "funding_instruments": list(summary.funding_instruments),
        "applicant_types": list(summary.applicant_types),
        "applicant_eligibility_description": summary.applicant_eligibility_description,
        "agency_contact_description": summary.agency_contact_description,
        "agency_email_address": summary.agency_email_address,
        "agency_email_address_description": summary.agency_email_address_description,
    }


def test_announcement_summary_create_200(
    client,
    db_session,
    api_key_headers,
):
    announcement = AnnouncementFactory.create()

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
):
    announcement = AnnouncementFactory.create()
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
):
    announcement = AnnouncementFactory.create()

    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=build_summary_request(is_forecast=True),
        headers=api_key_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["is_forecast"] is True


def test_announcement_summary_create_duplicate_type_is_deleted_200(
    client,
    api_key_headers,
):
    announcement = AnnouncementFactory.create()
    # Add a deleted summary, this won't get seen and a new summary can be created.
    AnnouncementSummaryFactory.create(announcement=announcement, is_forecast=True, is_deleted=True)

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
):
    summary = AnnouncementSummaryFactory.create(is_forecast=False)

    response = client.post(
        f"/v1/announcements/{summary.announcement_id}/summaries",
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


def test_announcement_summary_create_deleted_announcement_404(
    client,
    api_key_headers,
):
    announcement = AnnouncementFactory.create(is_deleted=True)

    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=build_summary_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_announcement_summary_create_invalid_award_values_422(
    client,
    api_key_headers,
):
    announcement = AnnouncementFactory.create()
    request = build_summary_request()
    request["award_floor"] = 200_000
    request["award_ceiling"] = 100_000

    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 422


def test_announcement_summary_create_null_cost_sharing_422(
    client,
    api_key_headers,
):
    announcement = AnnouncementFactory.create()
    request = build_summary_request()
    request["is_cost_sharing"] = None

    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 422


def test_announcement_summary_create_invalid_timestamps_422(
    client,
    api_key_headers,
):
    announcement = AnnouncementFactory.create()
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


def test_announcement_summary_create_no_auth_401(client, enable_factory_create):
    announcement = AnnouncementFactory.create()
    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=build_summary_request(),
    )

    assert response.status_code == 401


def test_announcement_summary_update_200(
    client,
    db_session,
    api_key_headers,
):
    summary = AnnouncementSummaryFactory.create(is_forecast=False)
    request = build_summary_update_request()
    request["summary_description"] = "Updated summary description"

    response = client.put(
        f"/v1/announcements/{summary.announcement_id}/summaries/"
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
):
    announcement = AnnouncementFactory.create()

    summary = AnnouncementSummaryFactory.create()

    response = client.put(
        f"/v1/announcements/{announcement.announcement_id}/summaries/"
        f"{summary.announcement_summary_id}",
        json=build_summary_update_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_announcement_summary_update_unknown_summary_404(
    client,
    api_key_headers,
):
    announcement = AnnouncementFactory.create()
    request = build_summary_update_request()

    response = client.put(
        f"/v1/announcements/{announcement.announcement_id}/summaries/{uuid.uuid4()}",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_announcement_summary_update_no_auth_401(client, db_session, enable_factory_create):
    summary = AnnouncementSummaryFactory.create()

    response = client.put(
        f"/v1/announcements/{summary.announcement_id}/summaries/"
        f"{summary.announcement_summary_id}",
        json=build_summary_update_request(),
    )

    assert response.status_code == 401


def test_announcement_summary_create_records_audit(
    client,
    db_session,
    api_key_headers,
):
    announcement = AnnouncementFactory.create()
    request = build_summary_request()

    response = client.post(
        f"/v1/announcements/{announcement.announcement_id}/summaries",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 200
    summary_id = uuid.UUID(response.get_json()["data"]["announcement_summary_id"])

    audit_rows = (
        db_session.execute(
            select(AnnouncementAudit).where(
                AnnouncementAudit.announcement_id == announcement.announcement_id
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    audit = audit_rows[0]
    assert audit.announcement_audit_event == AnnouncementAuditEvent.ANNOUNCEMENT_SUMMARY_CREATED
    assert audit.announcement_summary_id == summary_id
    assert audit.application_package_id is None

    changed_fields = audit.audit_metadata["changed_fields"]
    assert changed_fields["summary_description"] == {
        "before": None,
        "after": request["summary_description"],
    }
    assert changed_fields["is_cost_sharing"] == {"before": None, "after": False}
    assert changed_fields["is_forecast"] == {"before": None, "after": False}
    assert changed_fields["award_floor"] == {"before": None, "after": request["award_floor"]}
    assert changed_fields["award_ceiling"] == {
        "before": None,
        "after": request["award_ceiling"],
    }
    assert "agency_contact_description" not in changed_fields


def test_announcement_summary_update_records_audit_single_field(
    client,
    db_session,
    api_key_headers,
):
    summary = AnnouncementSummaryFactory.create(is_forecast=False)
    original_description = summary.summary_description

    request = build_update_request_from_summary(summary)
    request["summary_description"] = "Updated summary description (Revised)"

    response = client.put(
        f"/v1/announcements/{summary.announcement_id}/summaries/"
        f"{summary.announcement_summary_id}",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 200

    audit_rows = (
        db_session.execute(
            select(AnnouncementAudit).where(
                AnnouncementAudit.announcement_id == summary.announcement_id
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    audit = audit_rows[0]
    assert audit.announcement_audit_event == AnnouncementAuditEvent.ANNOUNCEMENT_SUMMARY_UPDATED
    assert audit.announcement_summary_id == summary.announcement_summary_id
    assert audit.application_package_id is None
    assert audit.audit_metadata["changed_fields"] == {
        "summary_description": {
            "before": original_description,
            "after": "Updated summary description (Revised)",
        },
    }


def test_announcement_summary_update_records_audit_multiple_fields(
    client,
    db_session,
    api_key_headers,
):
    summary = AnnouncementSummaryFactory.create(is_forecast=False)
    original_description = summary.summary_description
    original_award_ceiling = summary.award_ceiling

    request = build_update_request_from_summary(summary)
    request["summary_description"] = "Updated summary description (Revised)"
    request["award_ceiling"] = original_award_ceiling + 50_000

    response = client.put(
        f"/v1/announcements/{summary.announcement_id}/summaries/"
        f"{summary.announcement_summary_id}",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 200

    audit_rows = (
        db_session.execute(
            select(AnnouncementAudit).where(
                AnnouncementAudit.announcement_id == summary.announcement_id
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    audit = audit_rows[0]
    assert audit.announcement_audit_event == AnnouncementAuditEvent.ANNOUNCEMENT_SUMMARY_UPDATED
    assert audit.audit_metadata["changed_fields"] == {
        "summary_description": {
            "before": original_description,
            "after": "Updated summary description (Revised)",
        },
        "award_ceiling": {
            "before": original_award_ceiling,
            "after": original_award_ceiling + 50_000,
        },
    }
