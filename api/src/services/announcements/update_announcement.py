import logging
import uuid

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import AnnouncementAuditEvent
from src.db.models.announcement_models import Announcement
from src.db.models.user_models import User
from src.services.announcements.announcement_audit import record_announcement_audit
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import get_announcement
from src.util.dict_util import snapshot_fields

logger = logging.getLogger(__name__)

ANNOUNCEMENT_UPDATE_FIELDS = (
    "announcement_title",
    "tagline",
    "purpose_statement",
    "category",
    "category_explanation",
)


def update_announcement(
    db_session: db.Session,
    user: User,
    announcement_id: uuid.UUID,
    json_data: dict,
) -> Announcement:
    announcement = get_announcement(db_session, announcement_id)

    if not has_access(user, announcement, "update"):
        raise_flask_error(403, "User does not have access to update this announcement")

    before = snapshot_fields(announcement, ANNOUNCEMENT_UPDATE_FIELDS)

    for field, value in json_data.items():
        setattr(announcement, field, value)

    after = snapshot_fields(announcement, ANNOUNCEMENT_UPDATE_FIELDS)

    logger.info("Updated announcement", extra={"announcement_id": announcement_id})

    record_announcement_audit(
        db_session=db_session,
        user=user,
        announcement=announcement,
        audit_event=AnnouncementAuditEvent.ANNOUNCEMENT_UPDATED,
        before=before,
        after=after,
    )

    return announcement
