import uuid

import pytest
from sqlalchemy import select

from src.constants.lookup_constants import FileScanStatus
from src.db.models.announcement_models import AnnouncementAttachment
from src.util import file_util
from tests.db.models.factories import AnnouncementFactory, PendingFileFactory, UserApiKeyFactory


def test_announcement_attachment_create_200(client, s3_config, db_session, enable_factory_create):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(
        file_scan_status=FileScanStatus.COMPLETE, user=api_key.user, file_contents="hello"
    )
    announcement = AnnouncementFactory.create()

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/attachments",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 200

    data = resp.get_json()["data"]
    assert data["file_name"] == pending_file.file_name
    assert data["mime_type"] == pending_file.mime_type
    assert data["file_size_bytes"] == 5
    assert file_util.read_file(data["download_path"]) == "hello"

    db_attachment = db_session.execute(
        select(AnnouncementAttachment).where(
            AnnouncementAttachment.announcement_attachment_id == data["announcement_attachment_id"]
        )
    ).scalar_one_or_none()
    assert db_attachment is not None

    db_session.refresh(pending_file)
    assert pending_file.file_scan_status == FileScanStatus.PROCESSED
    assert file_util.file_exists(pending_file.file_location) is False


def test_announcement_attachment_create_wrong_user_403(
    client, s3_config, db_session, enable_factory_create
):
    api_key = UserApiKeyFactory.create()

    # Pending file will be associated with a different user
    pending_file = PendingFileFactory.create(file_scan_status=FileScanStatus.COMPLETE)
    announcement = AnnouncementFactory.create()

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/attachments",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "You do not have permission to access this file"


def test_announcement_attachment_create_pending_file_not_found_404(client, enable_factory_create):
    api_key = UserApiKeyFactory.create()
    announcement = AnnouncementFactory.create()
    request = {"pending_file_id": uuid.uuid4()}

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/attachments",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 404
    assert resp.get_json()["message"] == "Pending file not found"


def test_announcement_attachment_create_announcement_not_found_404(
    client, s3_config, enable_factory_create
):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(
        file_scan_status=FileScanStatus.COMPLETE, user=api_key.user, file_contents="hello"
    )

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{uuid.uuid4()}/attachments",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 404
    assert resp.get_json()["message"].startswith("Could not find announcement with ID")


def test_announcement_attachment_create_announcement_deleted_404(
    client, s3_config, db_session, enable_factory_create
):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(
        file_scan_status=FileScanStatus.COMPLETE, user=api_key.user, file_contents="hello"
    )
    announcement = AnnouncementFactory.create(is_deleted=True)

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/attachments",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 404

    # Verify the status hasn't been updated
    db_session.refresh(pending_file)
    assert pending_file.file_scan_status == FileScanStatus.COMPLETE


@pytest.mark.parametrize("status", [FileScanStatus.INFECTED, FileScanStatus.PENDING])
def test_announcement_attachment_create_scan_not_complete_422(
    client, s3_config, db_session, enable_factory_create, status
):
    api_key = UserApiKeyFactory.create()

    pending_file = PendingFileFactory.create(file_scan_status=status, user=api_key.user)
    announcement = AnnouncementFactory.create()

    request = {"pending_file_id": pending_file.pending_file_id}

    resp = client.post(
        f"/v1/announcements/{announcement.announcement_id}/attachments",
        json=request,
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 422

    errors = resp.get_json()["errors"]
    assert len(errors) == 1
    assert errors[0]["type"] == "invalid"
    assert errors[0]["message"] == "File scan status must be 'complete'"
    assert errors[0]["value"] == status
    assert errors[0]["field"] == "file_scan_status"


def test_announcement_attachment_create_bad_api_key_401(client):
    request = {"pending_file_id": uuid.uuid4()}

    resp = client.post(
        f"/v1/announcements/{uuid.uuid4()}/attachments",
        json=request,
        headers={"X-API-Key": "not a real key"},
    )
    assert resp.status_code == 401


def test_announcement_attachment_create_no_api_key_401(client):
    request = {"pending_file_id": uuid.uuid4()}

    resp = client.post(f"/v1/announcements/{uuid.uuid4()}/attachments", json=request)
    assert resp.status_code == 401
