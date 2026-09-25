import uuid

from src.util import file_util
from tests.db.models.factories import AnnouncementAttachmentFactory, AnnouncementFactory


def test_attachment_delete_200(client, api_key_headers, db_session):
    announcement_attachment = AnnouncementAttachmentFactory.create()

    resp = client.delete(
        f"/v1/announcements/{announcement_attachment.announcement_id}/attachments/{announcement_attachment.announcement_attachment_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    # Verify it was deleted from the DB
    db_session.refresh(announcement_attachment)
    assert announcement_attachment.is_deleted is True

    # The file will still exist as we only soft deleted it
    assert file_util.file_exists(announcement_attachment.file_attachment.file_location) is True


def test_attachment_delete_missing_announcement_404(client, api_key_headers):
    announcement_attachment = AnnouncementAttachmentFactory.create()

    resp = client.delete(
        f"/v1/announcements/{uuid.uuid4()}/attachments/{announcement_attachment.announcement_attachment_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404

    # Verify the file wasn't deleted
    assert file_util.file_exists(announcement_attachment.file_attachment.file_location) is True


def test_attachment_delete_missing_attachment_404(client, api_key_headers):
    announcement = AnnouncementFactory.create()

    resp = client.delete(
        f"/v1/announcements/{announcement.announcement_id}/attachments/{uuid.uuid4()}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_attachment_delete_deleted_announcement_404(client, api_key_headers):
    announcement_attachment = AnnouncementAttachmentFactory.create(announcement__is_deleted=True)
    resp = client.delete(
        f"/v1/announcements/{announcement_attachment.announcement_id}/attachments/{announcement_attachment.announcement_attachment_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_attachment_delete_deleted_attachment_404(client, api_key_headers):
    announcement_attachment = AnnouncementAttachmentFactory.create(is_deleted=True)
    resp = client.delete(
        f"/v1/announcements/{announcement_attachment.announcement_id}/attachments/{announcement_attachment.announcement_attachment_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_attachment_delete_bad_api_key_401(client):
    resp = client.delete(
        f"/v1/announcements/{uuid.uuid4()}/attachments/{uuid.uuid4()}",
        headers={"X-API-Key": "not a good key"},
    )
    assert resp.status_code == 401


def test_attachment_delete_no_api_key_401(client):
    resp = client.delete(f"/v1/announcements/{uuid.uuid4()}/attachments/{uuid.uuid4()}")
    assert resp.status_code == 401
