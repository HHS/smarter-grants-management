import logging
import uuid

from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.auth.internal_resource import get_internal_resource
from src.constants.lookup_constants import FileScanStatus, Privilege
from src.db.models.file_upload_models import PendingFile
from src.db.models.user_models import User
from src.util import datetime_util, file_util

logger = logging.getLogger(__name__)


def update_pending_file_scan_status(
    db_session: db.Session,
    pending_file_id: uuid.UUID,
    file_scan_status: FileScanStatus,
    file_location: str,
    user: User,
) -> None:
    AuthorizationEnforcer(db_session).verify_access(
        user,
        Privilege.INTERNAL_S3_SCAN,
        get_internal_resource(db_session),
    )

    pending_file = db_session.execute(
        select(PendingFile).where(PendingFile.pending_file_id == pending_file_id)
    ).scalar_one_or_none()

    if pending_file is None:
        raise_flask_error(404, "Pending file not found")

    if not file_util.file_exists(file_location):
        raise_flask_error(
            422,
            message="File does not exist at the provided s3 path",
        )

    prior_file_scan_status = pending_file.file_scan_status
    pending_file.file_scan_status = file_scan_status
    pending_file.file_location = file_location

    now = datetime_util.utcnow()
    scan_duration_seconds = (now - pending_file.created_at).total_seconds()

    try:
        file_length = file_util.get_file_length_bytes(file_location)
    except Exception:
        logger.exception("Failed to get file length")
        file_length = None

    logger.info(
        "Updated pending file scan status",
        extra={
            "pending_file_id": pending_file.pending_file_id,
            "scanner_user_id": user.user_id,
            "uploader_user_id": pending_file.user_id,
            "prior_file_scan_status": prior_file_scan_status,
            "file_scan_status": file_scan_status,
            "scan_duration_seconds": scan_duration_seconds,
            "file_length_bytes": file_length,
        },
    )
