import uuid

from src.util import file_util
from tests.db.models.factories import (
    ApplicationPackageFactory,
    ApplicationPackageInstructionFactory,
)


def test_application_package_get_200(client, api_key_headers, mock_s3_bucket):

    application_package = ApplicationPackageFactory.create()
    application_package_instruction = ApplicationPackageInstructionFactory.create(
        application_package=application_package, file_attachment__file_contents="this is a file"
    )

    resp = client.get(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{application_package.application_package_id}",
        headers=api_key_headers,
    )

    assert resp.status_code == 200
    response_package = resp.get_json()["data"]

    assert response_package["application_package_id"] == str(
        application_package.application_package_id
    )
    assert response_package["announcement_id"] == str(application_package.announcement_id)
    assert (
        response_package["application_package_title"]
        == application_package.application_package_title
    )
    assert (
        response_package["opening_timestamp"] == application_package.opening_timestamp.isoformat()
    )
    assert (
        response_package["closing_timestamp"] == application_package.closing_timestamp.isoformat()
    )
    assert response_package["contact_info"] == application_package.contact_info
    assert (
        response_package["announcement_assistance_listing"]["assistance_listing_number"]
        == application_package.announcement_assistance_listing.assistance_listing_number
    )
    assert response_package["open_to_applicants"] == application_package.open_to_applicants

    assert len(response_package["application_package_instructions"]) == 1
    response_instructions = response_package["application_package_instructions"][0]

    assert (
        response_instructions["file_name"]
        == application_package_instruction.file_attachment.file_name
    )
    assert (
        response_instructions["file_description"]
        == application_package_instruction.file_attachment.file_description
    )
    assert (
        response_instructions["file_size_bytes"]
        == application_package_instruction.file_attachment.file_size_bytes
    )
    assert file_util.read_file(response_instructions["download_path"]) == "this is a file"


def test_application_package_get_not_found_404(client, api_key_headers):
    resp = client.get(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}",
        headers=api_key_headers,
    )

    assert resp.status_code == 404


def test_application_package_get_is_deleted_404(client, api_key_headers):
    application_package = ApplicationPackageFactory.create(is_deleted=True)

    resp = client.get(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{application_package.application_package_id}",
        headers=api_key_headers,
    )

    assert resp.status_code == 404


def test_application_package_get_bad_api_key_401(client):
    resp = client.get(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}",
        headers={"X-API-Key": "bad key"},
    )

    assert resp.status_code == 401


def test_application_package_get_no_api_key_401(client):
    resp = client.get(f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}")

    assert resp.status_code == 401
