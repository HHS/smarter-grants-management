import logging
import uuid

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement_attachment import (
    get_announcement_attachment_and_verify_access,
)

logger = logging.getLogger(__name__)


def delete_announcement_attachment(
    db_session: db.Session,
    user: User,
    announcement_id: uuid.UUID,
    announcement_attachment_id: uuid.UUID,
) -> None:
    # Fetch the announcement
    announcement_attachment = get_announcement_attachment_and_verify_access(
        db_session, user, announcement_id, announcement_attachment_id
    )

    if not has_access(user, announcement_attachment.announcement, "update"):
        raise_flask_error(403, "User does not have access to update this announcement attachment")

    announcement_attachment.is_deleted = True

    logger.info(
        "Soft-deleted announcement attachment",
        extra={
            "announcement_id": announcement_id,
            "announcement_attachment_id": announcement_attachment_id,
        },
    )
