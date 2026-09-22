import uuid

from src.util import file_util
from tests.db.models.factories import (
    ApplicationPackageFactory,
    ApplicationPackageInstructionFactory,
)


def test_package_instruction_delete_200(client, api_key_headers, db_session):
    instructions = ApplicationPackageInstructionFactory.create()

    resp = client.delete(
        f"/v1/announcements/{instructions.application_package.announcement_id}/application-packages/{instructions.application_package_id}/instructions/{instructions.application_package_instruction_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    # Verify it was marked deleted in the DB
    db_session.refresh(instructions)
    assert instructions.is_deleted is True

    # The file will still exist as we only soft deleted it
    assert file_util.file_exists(instructions.file_attachment.file_location) is True


def test_package_instruction_delete_missing_announcement_404(client, api_key_headers):
    instructions = ApplicationPackageInstructionFactory.create()

    resp = client.delete(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{instructions.application_package_id}/instructions/{instructions.application_package_instruction_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_package_instruction_delete_missing_package_404(client, api_key_headers):
    instructions = ApplicationPackageInstructionFactory.create()

    resp = client.delete(
        f"/v1/announcements/{instructions.application_package.announcement_id}/application-packages/{uuid.uuid4()}/instructions/{instructions.application_package_instruction_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_package_instruction_delete_missing_instruction_404(client, api_key_headers):
    application_package = ApplicationPackageFactory.create()

    resp = client.delete(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{application_package.application_package_id}/instructions/{uuid.uuid4()}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_package_instruction_delete_deleted_announcement_404(client, api_key_headers):
    instructions = ApplicationPackageInstructionFactory.create(
        application_package__announcement__is_deleted=True
    )

    resp = client.delete(
        f"/v1/announcements/{instructions.application_package.announcement_id}/application-packages/{instructions.application_package_id}/instructions/{instructions.application_package_instruction_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_package_instruction_delete_deleted_package_404(client, api_key_headers):
    instructions = ApplicationPackageInstructionFactory.create(application_package__is_deleted=True)

    resp = client.delete(
        f"/v1/announcements/{instructions.application_package.announcement_id}/application-packages/{instructions.application_package_id}/instructions/{instructions.application_package_instruction_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_package_instruction_delete_deleted_instruction_404(client, api_key_headers):
    instructions = ApplicationPackageInstructionFactory.create(is_deleted=True)

    resp = client.delete(
        f"/v1/announcements/{instructions.application_package.announcement_id}/application-packages/{instructions.application_package_id}/instructions/{instructions.application_package_instruction_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_package_instruction_delete_bad_api_key_401(client):
    resp = client.delete(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}/instructions/{uuid.uuid4()}",
        headers={"X-API-Key": "not a good key"},
    )
    assert resp.status_code == 401


def test_package_instruction_delete_no_api_key_401(client):
    resp = client.delete(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}/instructions/{uuid.uuid4()}"
    )
    assert resp.status_code == 401
