import uuid

from src.adapters import db
from src.adapters.aws import S3Config
from src.db.models.announcement_models import Announcement, AnnouncementAttachment
from src.db.models.file_upload_models import FileAttachment
from src.db.models.user_models import User
from src.services.announcements.get_announcement import get_announcement_and_verify_access
from src.services.files.pending_file_handling_domain_specific import (
    fetch_and_validate_scan_complete_file,
    move_pending_file_to_destination,
)
from src.util import file_util


def get_s3_attachment_path(
    file_name: str,
    announcement_attachment_id: uuid.UUID,
    announcement: Announcement,
    s3_config: S3Config,
) -> str:
    """Construct a path to the attachments on s3

    Will be formatted like:

        s3://<bucket>/announcements/<announcement_id>/attachments/<attachment_id>/<file_name>

    Note that we store the files under a "folder" with the attachment ID as
    someone could upload multiple files with the same name.
    """

    return file_util.join(
        s3_config.draft_files_bucket_path,
        "announcements",
        str(announcement.announcement_id),
        "attachments",
        str(announcement_attachment_id),
        file_name,
    )


def create_announcement_attachment_from_pending_file(
    db_session: db.Session, user: User, announcement_id: uuid.UUID, pending_file_id: uuid.UUID
) -> AnnouncementAttachment:

    announcement = get_announcement_and_verify_access(db_session, announcement_id, user)

    pending_file = fetch_and_validate_scan_complete_file(db_session, pending_file_id, user)

    attachment_id = uuid.uuid4()
    # pending_file.file_location already ends in a secure_filename-sanitized
    # name (applied once at presign time) - reuse it instead of re-sanitizing
    # pending_file.file_name from scratch. The raw name is kept for the DB
    # record's display file_name below.
    secure_file_name = file_util.get_file_name(pending_file.file_location)

    s3_config = S3Config()
    s3_file_location = get_s3_attachment_path(
        file_name=secure_file_name,
        announcement_attachment_id=attachment_id,
        announcement=announcement,
        s3_config=s3_config,
    )
    file_size_bytes = file_util.get_file_length_bytes(pending_file.file_location)

    # Move the file on s3
    move_pending_file_to_destination(pending_file, s3_file_location)

    file_attachment = FileAttachment(
        file_attachment_id=uuid.uuid4(),
        file_location=s3_file_location,
        mime_type=pending_file.mime_type,
        file_name=pending_file.file_name,
        file_description=None,
        file_size_bytes=file_size_bytes,
    )

    announcement_attachment = AnnouncementAttachment(
        announcement_attachment_id=uuid.uuid4(),
        announcement=announcement,
        file_attachment=file_attachment,
    )

    db_session.add(file_attachment)
    db_session.add(announcement_attachment)

    return announcement_attachment
