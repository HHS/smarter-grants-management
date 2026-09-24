import uuid
from datetime import datetime

from sqlalchemy import select

from src.constants.lookup_constants import AnnouncementAuditEvent, ApplicationPackageOpenToApplicant
from src.db.models.announcement_models import AnnouncementAudit
from tests.api.announcements.conftest import create_application_package_request
from tests.db.models.factories import AnnouncementFactory, ApplicationPackageFactory


def test_application_package_update_200(client, api_key_headers, db_session):
    package = ApplicationPackageFactory.create()

    request = create_application_package_request()

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    resp_package = resp.get_json()["data"]

    db_session.refresh(package)

    assert (
        request["application_package_title"]
        == resp_package["application_package_title"]
        == package.application_package_title
    )
    assert (
        request["public_application_package_id"]
        == resp_package["public_application_package_id"]
        == package.public_application_package_id
    )
    assert request["grace_period"] == resp_package["grace_period"] == package.grace_period
    assert (
        request["opening_timestamp"]
        == resp_package["opening_timestamp"]
        == package.opening_timestamp.isoformat()
    )
    assert (
        request["closing_timestamp"]
        == resp_package["closing_timestamp"]
        == package.closing_timestamp.isoformat()
    )
    assert request["contact_info"] == resp_package["contact_info"] == package.contact_info
    assert (
        request["open_to_applicants"]
        == resp_package["open_to_applicants"]
        == package.open_to_applicants
    )


def test_application_package_update_without_optional_fields_200(
    client, api_key_headers, db_session
):
    package = ApplicationPackageFactory.create()

    request = create_application_package_request()
    del request["public_application_package_id"]
    del request["grace_period"]

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    resp_package = resp.get_json()["data"]

    db_session.refresh(package)

    assert (
        request["application_package_title"]
        == resp_package["application_package_title"]
        == package.application_package_title
    )
    assert (
        resp_package["public_application_package_id"] is None
        and package.public_application_package_id is None
    )
    assert resp_package["grace_period"] is None and package.grace_period is None
    assert (
        request["opening_timestamp"]
        == resp_package["opening_timestamp"]
        == package.opening_timestamp.isoformat()
    )
    assert (
        request["closing_timestamp"]
        == resp_package["closing_timestamp"]
        == package.closing_timestamp.isoformat()
    )
    assert request["contact_info"] == resp_package["contact_info"] == package.contact_info
    assert (
        request["open_to_applicants"]
        == resp_package["open_to_applicants"]
        == package.open_to_applicants
    )


def test_application_package_update_announcement_not_found_404(client, api_key_headers):
    package = ApplicationPackageFactory.create()

    request = create_application_package_request()

    resp = client.put(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_application_package_update_package_not_found_404(client, api_key_headers):
    announcement = AnnouncementFactory.create()

    request = create_application_package_request()

    resp = client.put(
        f"/v1/announcements/{announcement.announcement_id}/application-packages/{uuid.uuid4()}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_application_package_update_wrong_announcement_404(client, api_key_headers):
    package = ApplicationPackageFactory.create()
    different_announcement = AnnouncementFactory.create()

    request = create_application_package_request()

    resp = client.put(
        f"/v1/announcements/{different_announcement.announcement_id}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_application_package_missing_required_fields_422(client, api_key_headers):
    package = ApplicationPackageFactory.create()

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
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


def test_application_package_update_invalid_data_types_422(client, api_key_headers):
    package = ApplicationPackageFactory.create()

    request = create_application_package_request()
    request["closing_timestamp"] = "hello"

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 422

    errors = resp.get_json()["errors"]
    assert len(errors) == 1

    assert errors[0]["field"] == "closing_timestamp"
    assert errors[0]["type"] == "invalid"
    assert errors[0]["message"] == "Not a valid datetime."


def test_application_package_update_empty_open_to_applicants_422(client, api_key_headers):
    package = ApplicationPackageFactory.create()

    request = create_application_package_request(open_to_applicants=[])

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 422

    errors = resp.get_json()["errors"]
    assert len(errors) == 1

    assert errors[0]["field"] == "open_to_applicants"
    assert errors[0]["type"] == "min_length"
    assert errors[0]["message"] == "Shorter than minimum length 1."


def test_application_package_update_closing_before_opening_422(client, api_key_headers):
    package = ApplicationPackageFactory.create()

    request = create_application_package_request(
        opening_timestamp=datetime(2026, 1, 1, 12, 30, 0),
        closing_timestamp=datetime(2023, 1, 1, 12, 30, 0),
    )

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 422

    errors = resp.get_json()["errors"]
    assert len(errors) == 1

    assert errors[0]["field"] == "_schema"
    assert errors[0]["type"] == "invalid_date_order"
    assert errors[0]["message"] == "Closing timestamp must be on or after opening timestamp."


def test_application_package_update_bad_api_key_401(client):
    request = create_application_package_request()
    resp = client.put(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}",
        json=request,
        headers={"X-API-Key": "not a real key"},
    )
    assert resp.status_code == 401


def test_application_package_update_no_api_key_401(client):
    request = create_application_package_request()
    resp = client.put(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}", json=request
    )
    assert resp.status_code == 401


def test_application_package_update_records_audit_single_field(client, db_session, api_key_headers):
    package = ApplicationPackageFactory.create(
        application_package_title="Proposal for Rural Health Access Expansion",
        public_application_package_id="ABC-134-56789",
        grace_period=5,
        contact_info="Bob Smith - Program Office",
        open_to_applicants=[
            ApplicationPackageOpenToApplicant.INDIVIDUAL,
            ApplicationPackageOpenToApplicant.ORGANIZATION,
        ],
    )
    original_title = package.application_package_title

    request = create_application_package_request(
        application_package_title="Proposal for Rural Health Access Expansion (Revised)",
        public_application_package_id=package.public_application_package_id,
        grace_period=package.grace_period,
        opening_timestamp=package.opening_timestamp,
        closing_timestamp=package.closing_timestamp,
        contact_info=package.contact_info,
        open_to_applicants=list(package.open_to_applicants),
    )

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    audit_rows = (
        db_session.execute(
            select(AnnouncementAudit).where(
                AnnouncementAudit.announcement_id == package.announcement_id
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    audit = audit_rows[0]
    assert audit.announcement_audit_event == AnnouncementAuditEvent.APPLICATION_PACKAGE_UPDATED
    assert audit.application_package_id == package.application_package_id
    assert audit.audit_metadata["changed_fields"] == {
        "application_package_title": {
            "before": original_title,
            "after": "Proposal for Rural Health Access Expansion (Revised)",
        },
    }


def test_application_package_update_records_audit_multiple_fields(
    client, db_session, api_key_headers
):
    package = ApplicationPackageFactory.create(
        application_package_title="Proposal for Rural Health Access Expansion",
        public_application_package_id="ABC-134-56789",
        grace_period=5,
        contact_info="Bob Smith - Program Office",
        open_to_applicants=[
            ApplicationPackageOpenToApplicant.INDIVIDUAL,
            ApplicationPackageOpenToApplicant.ORGANIZATION,
        ],
    )
    original_title = package.application_package_title
    original_grace_period = package.grace_period

    request = create_application_package_request(
        application_package_title="Proposal for Rural Health Access Expansion (Revised)",
        public_application_package_id=package.public_application_package_id,
        grace_period=original_grace_period + 10,
        opening_timestamp=package.opening_timestamp,
        closing_timestamp=package.closing_timestamp,
        contact_info=package.contact_info,
        open_to_applicants=list(package.open_to_applicants),
    )

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    audit_rows = (
        db_session.execute(
            select(AnnouncementAudit).where(
                AnnouncementAudit.announcement_id == package.announcement_id
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    audit = audit_rows[0]
    assert audit.announcement_audit_event == AnnouncementAuditEvent.APPLICATION_PACKAGE_UPDATED
    assert audit.audit_metadata["changed_fields"] == {
        "application_package_title": {
            "before": original_title,
            "after": "Proposal for Rural Health Access Expansion (Revised)",
        },
        "grace_period": {
            "before": original_grace_period,
            "after": original_grace_period + 10,
        },
    }
