import uuid

from src.adapters import db
from src.adapters.aws import S3Config
from src.db.models.application_package_models import ApplicationPackageInstruction
from src.db.models.file_upload_models import FileAttachment
from src.db.models.user_models import User
from src.services.announcements.get_application_package import (
    get_application_package_and_verify_access,
)
from src.services.files.pending_file_handling_domain_specific import (
    fetch_and_validate_scan_complete_file,
    move_pending_file_to_destination,
)
from src.util import file_util


def get_s3_attachment_path(
    file_name: str,
    announcement_id: uuid.UUID,
    application_package_id: uuid.UUID,
    application_package_instruction_id: uuid.UUID,
    s3_config: S3Config,
) -> str:
    """Construct a path to the attachments on s3

    Will be formatted like:

        s3://<bucket>/announcements/<announcement_id>/application_packages/<application_package_id>/instructions/<application_package_instruction_id>/<file_name>

    Note that we store the files under a "folder" with the attachment ID as
    someone could upload multiple files with the same name.
    """

    return file_util.join(
        s3_config.draft_files_bucket_path,
        "announcements",
        str(announcement_id),
        "application_packages",
        str(application_package_id),
        "instructions",
        str(application_package_instruction_id),
        file_name,
    )


def create_application_package_instruction(
    db_session: db.Session,
    user: User,
    announcement_id: uuid.UUID,
    application_package_id: uuid.UUID,
    pending_file_id: uuid.UUID,
) -> ApplicationPackageInstruction:

    application_package = get_application_package_and_verify_access(
        db_session, user, announcement_id, application_package_id
    )

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
        announcement_id=announcement_id,
        application_package_id=application_package_id,
        application_package_instruction_id=attachment_id,
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

    application_package_instruction = ApplicationPackageInstruction(
        application_package_instruction_id=uuid.uuid4(),
        application_package=application_package,
        file_attachment=file_attachment,
    )

    db_session.add(file_attachment)
    db_session.add(application_package_instruction)

    return application_package_instruction
