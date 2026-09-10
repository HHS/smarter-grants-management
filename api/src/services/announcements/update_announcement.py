import logging
import uuid

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.announcement_models import Announcement
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import get_announcement

logger = logging.getLogger(__name__)


def update_announcement(
    db_session: db.Session,
    user: User,
    announcement_id: uuid.UUID,
    json_data: dict,
) -> Announcement:
    announcement = get_announcement(db_session, announcement_id)

    if not has_access(user, announcement, "update"):
        raise_flask_error(403, "User does not have access to update this announcement")

    for field, value in json_data.items():
        setattr(announcement, field, value)

    logger.info("Updated announcement", extra={"announcement_id": announcement_id})

    return announcement
