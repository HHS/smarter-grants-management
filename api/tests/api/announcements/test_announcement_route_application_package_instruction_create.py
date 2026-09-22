import uuid

import pytest
from sqlalchemy import select

from src.constants.lookup_constants import FileScanStatus
from src.db.models.application_package_models import ApplicationPackageInstruction
from src.util import file_util
from tests.db.models.factories import (
    ApplicationPackageFactory,
    PendingFileFactory,
    UserApiKeyFactory,
)


def test_package_instruction_create_200(client, s3_config, db_session, enable_factory_create):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(
        file_scan_status=FileScanStatus.COMPLETE,
        user=api_key.user,
        file_contents="this is a test file",
    )
    application_package = ApplicationPackageFactory.create()

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{application_package.application_package_id}/instructions",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 200

    data = resp.get_json()["data"]
    assert data["file_name"] == pending_file.file_name
    assert data["mime_type"] == pending_file.mime_type
    assert data["file_size_bytes"] == 19
    assert file_util.read_file(data["download_path"]) == "this is a test file"

    db_attachment = db_session.execute(
        select(ApplicationPackageInstruction).where(
            ApplicationPackageInstruction.application_package_instruction_id
            == data["application_package_instruction_id"]
        )
    ).scalar_one_or_none()
    assert db_attachment is not None

    db_session.refresh(pending_file)
    assert pending_file.file_scan_status == FileScanStatus.PROCESSED
    assert file_util.file_exists(pending_file.file_location) is False


def test_package_instruction_create_wrong_user_403(
    client, s3_config, db_session, enable_factory_create
):
    api_key = UserApiKeyFactory.create()

    # Pending file will be associated with a different user
    pending_file = PendingFileFactory.create(file_scan_status=FileScanStatus.COMPLETE)

    application_package = ApplicationPackageFactory.create()

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{application_package.application_package_id}/instructions",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "You do not have permission to access this file"


def test_package_instruction_create_pending_file_not_found_404(client, enable_factory_create):
    api_key = UserApiKeyFactory.create()
    application_package = ApplicationPackageFactory.create()
    request = {"pending_file_id": uuid.uuid4()}

    resp = client.post(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{application_package.application_package_id}/instructions",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 404
    assert resp.get_json()["message"] == "Pending file not found"


def test_package_instruction_create_announcement_not_found_404(
    client, s3_config, enable_factory_create
):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(
        file_scan_status=FileScanStatus.COMPLETE, user=api_key.user
    )
    application_package = ApplicationPackageFactory.create()

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{application_package.application_package_id}/instructions",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 404


def test_package_instruction_create_package_not_found_404(client, s3_config, enable_factory_create):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(
        file_scan_status=FileScanStatus.COMPLETE, user=api_key.user
    )
    application_package = ApplicationPackageFactory.create()

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{uuid.uuid4()}/instructions",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 404


def test_package_instruction_create_announcement_deleted_404(
    client, s3_config, enable_factory_create
):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(
        file_scan_status=FileScanStatus.COMPLETE, user=api_key.user
    )
    application_package = ApplicationPackageFactory.create(announcement__is_deleted=True)

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{application_package.application_package_id}/instructions",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 404


def test_package_instruction_create_package_package_deleted_404(
    client, s3_config, enable_factory_create
):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(
        file_scan_status=FileScanStatus.COMPLETE, user=api_key.user
    )
    application_package = ApplicationPackageFactory.create(is_deleted=True)

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{application_package.application_package_id}/instructions",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 404


@pytest.mark.parametrize("status", [FileScanStatus.INFECTED, FileScanStatus.PENDING])
def test_package_instruction_create_scan_not_complete_422(
    client, s3_config, db_session, enable_factory_create, status
):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(file_scan_status=status, user=api_key.user)
    application_package = ApplicationPackageFactory.create(is_deleted=True)

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{application_package.announcement_id}/application-packages/{application_package.application_package_id}/instructions",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 404


def test_package_instruction_create_bad_api_key_401(client):
    request = {"pending_file_id": uuid.uuid4()}
    resp = client.post(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}/instructions",
        json=request,
        headers={"X-API-Key": "not a valid API key"},
    )
    assert resp.status_code == 401


def test_package_instruction_create_no_api_key_401(client):
    request = {"pending_file_id": uuid.uuid4()}
    resp = client.post(
        f"/v1/announcements/{uuid.uuid4()}/application-packages/{uuid.uuid4()}/instructions",
        json=request,
    )
    assert resp.status_code == 401
