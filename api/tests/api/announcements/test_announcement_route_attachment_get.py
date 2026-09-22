import uuid

from src.util import file_util
from tests.db.models.factories import AnnouncementAttachmentFactory, AnnouncementFactory


def test_announcement_attachment_get_200(client, api_key_headers):
    announcement_attachment = AnnouncementAttachmentFactory.create(
        file_attachment__file_contents="this is a file, yay"
    )

    resp = client.get(
        f"/v1/announcements/{announcement_attachment.announcement_id}/attachments/{announcement_attachment.announcement_attachment_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 200

    data = resp.get_json()["data"]

    assert data["announcement_attachment_id"] == str(
        announcement_attachment.announcement_attachment_id
    )
    assert data["file_name"] == announcement_attachment.file_attachment.file_name
    assert data["file_description"] == announcement_attachment.file_attachment.file_description
    assert data["mime_type"] == announcement_attachment.file_attachment.mime_type
    assert data["file_size_bytes"] == announcement_attachment.file_attachment.file_size_bytes
    assert data["created_at"] == announcement_attachment.file_attachment.created_at.isoformat()

    assert file_util.read_file(data["download_path"]) == "this is a file, yay"


def test_attachment_get_missing_announcement_404(client, api_key_headers):
    announcement_attachment = AnnouncementAttachmentFactory.create()

    resp = client.get(
        f"/v1/announcements/{uuid.uuid4()}/attachments/{announcement_attachment.announcement_attachment_id}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_attachment_get_missing_attachment_404(client, api_key_headers):
    announcement = AnnouncementFactory.create()

    resp = client.get(
        f"/v1/announcements/{announcement.announcement_id}/attachments/{uuid.uuid4()}",
        headers=api_key_headers,
    )
    assert resp.status_code == 404


def test_attachment_get_bad_api_key_401(client):
    resp = client.get(
        f"/v1/announcements/{uuid.uuid4()}/attachments/{uuid.uuid4()}",
        headers={"X-API-Key": "not a good key"},
    )
    assert resp.status_code == 401


def test_attachment_get_no_api_key_401(client):
    resp = client.get(f"/v1/announcements/{uuid.uuid4()}/attachments/{uuid.uuid4()}")
    assert resp.status_code == 401
