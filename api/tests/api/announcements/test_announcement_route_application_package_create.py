import uuid
from datetime import datetime

from sqlalchemy import select

from src.constants.lookup_constants import AnnouncementAuditEvent
from src.db.models.announcement_models import AnnouncementAudit
from tests.api.announcements.conftest import create_application_package_request
from tests.db.models.factories import AnnouncementFactory


def test_application_package_create_200(client, api_key_headers, db_session):

    announcement = AnnouncementFactory.create()

    request = create_application_package_request()

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    resp_package = resp.get_json()["data"]

    db_session.refresh(announcement)
    assert len(announcement.application_packages) == 1

    db_package = announcement.application_packages[0]

    assert (
        request["application_package_title"]
        == resp_package["application_package_title"]
        == db_package.application_package_title
    )
    assert (
        request["public_application_package_id"]
        == resp_package["public_application_package_id"]
        == db_package.public_application_package_id
    )
    assert request["grace_period"] == resp_package["grace_period"] == db_package.grace_period
    assert (
        request["opening_timestamp"]
        == resp_package["opening_timestamp"]
        == db_package.opening_timestamp.isoformat()
    )
    assert (
        request["closing_timestamp"]
        == resp_package["closing_timestamp"]
        == db_package.closing_timestamp.isoformat()
    )
    assert request["contact_info"] == resp_package["contact_info"] == db_package.contact_info
    assert (
        request["open_to_applicants"]
        == resp_package["open_to_applicants"]
        == db_package.open_to_applicants
    )

    assert db_package.announcement_assistance_listing is not None
    assert db_package.announcement_assistance_listing_id in [
        al.announcement_assistance_listing_id
        for al in announcement.announcement_assistance_listings
    ]


def test_application_package_create_without_optional_fields_200(
    client, api_key_headers, db_session
):

    announcement = AnnouncementFactory.create()

    request = create_application_package_request()
    del request["public_application_package_id"]
    del request["grace_period"]

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    resp_package = resp.get_json()["data"]

    db_session.refresh(announcement)
    assert len(announcement.application_packages) == 1

    db_package = announcement.application_packages[0]

    assert (
        request["application_package_title"]
        == resp_package["application_package_title"]
        == db_package.application_package_title
    )
    assert (
        resp_package["public_application_package_id"] is None
        and db_package.public_application_package_id is None
    )
    assert resp_package["grace_period"] is None and db_package.grace_period is None
    assert (
        request["opening_timestamp"]
        == resp_package["opening_timestamp"]
        == db_package.opening_timestamp.isoformat()
    )
    assert (
        request["closing_timestamp"]
        == resp_package["closing_timestamp"]
        == db_package.closing_timestamp.isoformat()
    )
    assert request["contact_info"] == resp_package["contact_info"] == db_package.contact_info
    assert (
        request["open_to_applicants"]
        == resp_package["open_to_applicants"]
        == db_package.open_to_applicants
    )


def test_application_package_create_without_aln_200(client, api_key_headers, db_session):
    announcement = AnnouncementFactory.create(announcement_assistance_listings=[])

    request = create_application_package_request()

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    db_session.refresh(announcement)
    assert len(announcement.application_packages) == 1

    db_package = announcement.application_packages[0]

    assert db_package.announcement_assistance_listing is None


def test_application_package_create_null_dates_200(client, api_key_headers, db_session):
    announcement = AnnouncementFactory.create()

    request = create_application_package_request()
    request["opening_timestamp"] = None
    request["closing_timestamp"] = None

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    db_session.refresh(announcement)
    assert len(announcement.application_packages) == 1

    db_package = announcement.application_packages[0]

    assert db_package.opening_timestamp is None
    assert db_package.closing_timestamp is None


def test_application_package_create_negative_grace_period_422(client, api_key_headers):
    announcement = AnnouncementFactory.create()

    request = create_application_package_request(grace_period=-1)

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 422

    errors = resp.get_json()["errors"]
    assert len(errors) == 1

    assert errors[0]["field"] == "grace_period"
    assert errors[0]["type"] == "min_value"
    assert errors[0]["message"] == "Must be greater than or equal to 0."


def test_application_package_create_missing_announcement_404(client, api_key_headers):
    request = create_application_package_request()

    resp = client.post(
        f"/v1/announcements/{uuid.uuid4()}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_application_package_create_missing_required_fields_422(client, api_key_headers):
    announcement = AnnouncementFactory.create()

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json={},
        headers=api_key_headers,
    )
    assert resp.status_code == 422

    errors = resp.get_json()["errors"]
    assert len(errors) == 5

    fields = set()
    for error in errors:
        fields.add(error["field"])
        assert error["type"] == "required"

    assert fields == {
        "application_package_title",
        "open_to_applicants",
        "opening_timestamp",
        "closing_timestamp",
        "contact_info",
    }


def test_application_package_create_invalid_data_types_422(client, api_key_headers):
    announcement = AnnouncementFactory.create()

    request = create_application_package_request()
    request["opening_timestamp"] = "hello"

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 422

    errors = resp.get_json()["errors"]
    assert len(errors) == 1

    assert errors[0]["field"] == "opening_timestamp"
    assert errors[0]["type"] == "invalid"
    assert errors[0]["message"] == "Not a valid datetime."


def test_application_package_create_empty_open_to_applicants_422(client, api_key_headers):
    announcement = AnnouncementFactory.create()

    request = create_application_package_request(open_to_applicants=[])

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 422

    errors = resp.get_json()["errors"]
    assert len(errors) == 1

    assert errors[0]["field"] == "open_to_applicants"
    assert errors[0]["type"] == "min_length"
    assert errors[0]["message"] == "Shorter than minimum length 1."


def test_application_package_closing_before_opening_422(client, api_key_headers):
    announcement = AnnouncementFactory.create()

    request = create_application_package_request(
        opening_timestamp=datetime(2026, 1, 1, 12, 30, 0),
        closing_timestamp=datetime(2023, 1, 1, 12, 30, 0),
    )

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 422

    errors = resp.get_json()["errors"]
    assert len(errors) == 1

    assert errors[0]["field"] == "_schema"
    assert errors[0]["type"] == "invalid_date_order"
    assert errors[0]["message"] == "Closing timestamp must be on or after opening timestamp."


def test_application_package_bad_api_key_401(client):

    request = create_application_package_request()
    resp = client.post(
        f"/v1/announcements/{uuid.uuid4()}/application-packages",
        json=request,
        headers={"X-API-Key": "not a real key"},
    )
    assert resp.status_code == 401


def test_application_package_no_api_key_401(client):
    request = create_application_package_request()
    resp = client.post(f"/v1/announcements/{uuid.uuid4()}/application-packages", json=request)
    assert resp.status_code == 401


def test_application_package_create_records_audit(client, db_session, api_key_headers):
    announcement = AnnouncementFactory.create()
    request = create_application_package_request()

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/application-packages",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    application_package_id = uuid.UUID(resp.get_json()["data"]["application_package_id"])

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
    assert audit.announcement_audit_event == AnnouncementAuditEvent.APPLICATION_PACKAGE_CREATED
    assert audit.application_package_id == application_package_id
    assert audit.announcement_summary_id is None

    changed_fields = audit.audit_metadata["changed_fields"]
    assert changed_fields["application_package_title"] == {
        "before": None,
        "after": request["application_package_title"],
    }
    assert changed_fields["public_application_package_id"] == {
        "before": None,
        "after": request["public_application_package_id"],
    }
    assert changed_fields["grace_period"] == {"before": None, "after": request["grace_period"]}
    assert changed_fields["contact_info"] == {
        "before": None,
        "after": request["contact_info"],
    }
    assert changed_fields["opening_timestamp"]["before"] is None
    assert changed_fields["closing_timestamp"]["before"] is None
    assert set(changed_fields["open_to_applicants"]["after"]) == set(request["open_to_applicants"])
    assert changed_fields["announcement_assistance_listing_id"]["before"] is None
    assert changed_fields["announcement_assistance_listing_id"]["after"] in [
        str(al.announcement_assistance_listing_id)
        for al in announcement.announcement_assistance_listings
    ]
