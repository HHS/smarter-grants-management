import uuid
from datetime import datetime

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


def test_application_package_update_announcement_deleted_404(client, api_key_headers):
    announcement = AnnouncementFactory.create(is_deleted=True)
    package = ApplicationPackageFactory.create(announcement=announcement)

    request = create_application_package_request()

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
        json=request,
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_application_package_update_package_deleted_404(client, api_key_headers):
    package = ApplicationPackageFactory.create(is_deleted=True)

    request = create_application_package_request()

    resp = client.put(
        f"/v1/announcements/{package.announcement_id}/application-packages/{package.application_package_id}",
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
