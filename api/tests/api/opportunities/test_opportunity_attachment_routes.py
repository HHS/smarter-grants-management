import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.constants.lookup_constants import FileScanStatus
from src.db.models.file_attachment_models import FileAttachment
from src.db.models.file_upload_models import PendingFile
from src.db.models.opportunity_models import OpportunityAttachment
from src.util import file_util
from tests.db.models.factories import (
    FileAttachmentFactory,
    OpportunityAttachmentFactory,
    OpportunityFactory,
    UserApiKeyFactory,
)


def create_pending_file(
    db_session,
    user,
    s3_config,
    *,
    file_scan_status=FileScanStatus.COMPLETE,
):
    pending_file_id = uuid.uuid4()
    file_location = file_util.join(
        s3_config.file_scan_bucket_path,
        "scanned",
        str(pending_file_id),
        "example.pdf",
    )
    file_util.write_to_file(file_location, "example attachment content")

    pending_file = PendingFile(
        pending_file_id=pending_file_id,
        user=user,
        file_name="Example Attachment.pdf",
        file_location=file_location,
        mime_type="application/pdf",
        file_scan_status=file_scan_status,
    )
    db_session.add(pending_file)
    db_session.commit()

    return pending_file


def test_opportunity_attachment_create_200(
    client,
    db_session,
    enable_factory_create,
    s3_config,
):
    opportunity = OpportunityFactory.create()
    api_key = UserApiKeyFactory.create()
    pending_file = create_pending_file(
        db_session,
        api_key.user,
        s3_config,
    )
    original_location = pending_file.file_location

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/attachments",
        json={"pending_file_id": str(pending_file.pending_file_id)},
        headers={"X-API-Key": api_key.key_id},
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    opportunity_attachment_id = uuid.UUID(data["opportunity_attachment_id"])

    opportunity_attachment = db_session.execute(
        select(OpportunityAttachment)
        .where(OpportunityAttachment.opportunity_attachment_id == opportunity_attachment_id)
        .options(selectinload(OpportunityAttachment.file_attachment))
    ).scalar_one()

    assert opportunity_attachment.opportunity_id == opportunity.opportunity_id
    assert opportunity_attachment.file_attachment.file_name == "Example Attachment.pdf"
    assert opportunity_attachment.file_attachment.mime_type == "application/pdf"
    assert opportunity_attachment.file_attachment.file_size_bytes > 0

    db_session.refresh(pending_file)
    assert pending_file.file_scan_status == FileScanStatus.PROCESSED
    assert pending_file.file_location == opportunity_attachment.file_attachment.file_location

    assert not file_util.file_exists(original_location)
    assert file_util.file_exists(opportunity_attachment.file_attachment.file_location)


def test_opportunity_attachment_create_unknown_opportunity_404(
    client,
    db_session,
    enable_factory_create,
    s3_config,
):
    api_key = UserApiKeyFactory.create()
    pending_file = create_pending_file(
        db_session,
        api_key.user,
        s3_config,
    )

    response = client.post(
        f"/v1/opportunities/{uuid.uuid4()}/attachments",
        json={"pending_file_id": str(pending_file.pending_file_id)},
        headers={"X-API-Key": api_key.key_id},
    )

    assert response.status_code == 404


def test_opportunity_attachment_create_unknown_pending_file_404(
    client,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()
    api_key = UserApiKeyFactory.create()

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/attachments",
        json={"pending_file_id": str(uuid.uuid4())},
        headers={"X-API-Key": api_key.key_id},
    )

    assert response.status_code == 404


def test_opportunity_attachment_create_pending_file_not_complete_422(
    client,
    db_session,
    enable_factory_create,
    s3_config,
):
    opportunity = OpportunityFactory.create()
    api_key = UserApiKeyFactory.create()
    pending_file = create_pending_file(
        db_session,
        api_key.user,
        s3_config,
        file_scan_status=FileScanStatus.PENDING,
    )

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/attachments",
        json={"pending_file_id": str(pending_file.pending_file_id)},
        headers={"X-API-Key": api_key.key_id},
    )

    assert response.status_code == 422


def test_opportunity_attachment_create_wrong_pending_file_owner_403(
    client,
    db_session,
    enable_factory_create,
    s3_config,
):
    opportunity = OpportunityFactory.create()
    owner_api_key = UserApiKeyFactory.create()
    request_api_key = UserApiKeyFactory.create()
    pending_file = create_pending_file(
        db_session,
        owner_api_key.user,
        s3_config,
    )

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/attachments",
        json={"pending_file_id": str(pending_file.pending_file_id)},
        headers={"X-API-Key": request_api_key.key_id},
    )

    assert response.status_code == 403


def test_opportunity_attachment_create_no_auth_401(
    client,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/attachments",
        json={"pending_file_id": str(uuid.uuid4())},
    )

    assert response.status_code == 401


def test_opportunity_attachment_delete_200(
    client,
    db_session,
    enable_factory_create,
    s3_config,
):
    opportunity = OpportunityFactory.create()
    api_key = UserApiKeyFactory.create()

    file_attachment = FileAttachmentFactory.create(
        file_location=file_util.join(
            s3_config.draft_files_bucket_path,
            "opportunities",
            str(opportunity.opportunity_id),
            "attachments",
            str(uuid.uuid4()),
            "example.pdf",
        )
    )
    file_util.write_to_file(
        file_attachment.file_location,
        "example attachment content",
    )

    opportunity_attachment = OpportunityAttachmentFactory.create(
        opportunity=opportunity,
        file_attachment=file_attachment,
    )
    opportunity_attachment_id = opportunity_attachment.opportunity_attachment_id
    file_attachment_id = file_attachment.file_attachment_id
    file_location = file_attachment.file_location

    response = client.delete(
        f"/v1/opportunities/{opportunity.opportunity_id}/attachments/"
        f"{opportunity_attachment_id}",
        headers={"X-API-Key": api_key.key_id},
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "Attachment successfully deleted"

    assert (
        db_session.execute(
            select(OpportunityAttachment).where(
                OpportunityAttachment.opportunity_attachment_id == opportunity_attachment_id
            )
        ).scalar_one_or_none()
        is None
    )
    assert (
        db_session.execute(
            select(FileAttachment).where(FileAttachment.file_attachment_id == file_attachment_id)
        ).scalar_one_or_none()
        is None
    )
    assert not file_util.file_exists(file_location)


def test_opportunity_attachment_delete_wrong_opportunity_404(
    client,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()
    other_opportunity = OpportunityFactory.create()
    opportunity_attachment = OpportunityAttachmentFactory.create(opportunity=other_opportunity)
    api_key = UserApiKeyFactory.create()

    response = client.delete(
        f"/v1/opportunities/{opportunity.opportunity_id}/attachments/"
        f"{opportunity_attachment.opportunity_attachment_id}",
        headers={"X-API-Key": api_key.key_id},
    )

    assert response.status_code == 404


def test_opportunity_attachment_delete_unknown_attachment_404(
    client,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()
    api_key = UserApiKeyFactory.create()

    response = client.delete(
        f"/v1/opportunities/{opportunity.opportunity_id}/attachments/{uuid.uuid4()}",
        headers={"X-API-Key": api_key.key_id},
    )

    assert response.status_code == 404


def test_opportunity_attachment_delete_no_auth_401(
    client,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()

    response = client.delete(
        f"/v1/opportunities/{opportunity.opportunity_id}/attachments/{uuid.uuid4()}",
    )

    assert response.status_code == 401
