import logging
import uuid

from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import FileScanStatus
from src.db.models.file_upload_models import PendingFile
from src.db.models.user_models import User
from src.util import file_util

logger = logging.getLogger(__name__)


def fetch_pending_file(
    db_session: db.Session,
    pending_file_id: uuid.UUID,
) -> PendingFile:
    pending_file = db_session.execute(
        select(PendingFile).where(PendingFile.pending_file_id == pending_file_id)
    ).scalar_one_or_none()

    if pending_file is None:
        logger.info(
            "Pending file not found",
            extra={"pending_file_id": pending_file_id},
        )
        raise_flask_error(404, message="Pending file not found")

    return pending_file


def validate_user_owns_file(pending_file: PendingFile, user: User) -> None:
    if pending_file.user_id != user.user_id:
        logger.info(
            "User does not have permission to access pending file",
            extra={
                "pending_file_id": pending_file.pending_file_id,
                "requesting_user_id": user.user_id,
                "file_owner_user_id": pending_file.user_id,
            },
        )
        raise_flask_error(
            403,
            message="You do not have permission to access this file",
        )


def validate_file_scan_complete(pending_file: PendingFile) -> None:
    if pending_file.file_scan_status != FileScanStatus.COMPLETE:
        logger.info(
            "Pending file status is not valid for processing",
            extra={
                "pending_file_id": pending_file.pending_file_id,
                "file_scan_status": pending_file.file_scan_status,
            },
        )
        raise_flask_error(
            422,
            message="File cannot be used, status must be complete",
        )


def fetch_and_validate_scan_complete_file(
    db_session: db.Session,
    pending_file_id: uuid.UUID,
    user: User,
) -> PendingFile:
    pending_file = fetch_pending_file(db_session, pending_file_id)
    validate_user_owns_file(pending_file, user)
    validate_file_scan_complete(pending_file)
    return pending_file


def move_pending_file_to_destination(
    pending_file: PendingFile,
    destination_s3_path: str,
) -> None:
    logger.info(
        "Moving pending file to destination",
        extra={
            "pending_file_id": pending_file.pending_file_id,
            "source_location": pending_file.file_location,
            "destination_location": destination_s3_path,
        },
    )

    file_util.move_file(pending_file.file_location, destination_s3_path)
    pending_file.file_location = destination_s3_path
    pending_file.file_scan_status = FileScanStatus.PROCESSED

    logger.info(
        "Successfully moved pending file and updated status",
        extra={
            "pending_file_id": pending_file.pending_file_id,
            "new_status": FileScanStatus.PROCESSED,
        },
    )
