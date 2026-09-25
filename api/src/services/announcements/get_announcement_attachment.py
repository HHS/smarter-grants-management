import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.announcement_models import Announcement, AnnouncementAttachment
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import get_announcement_and_verify_access


def get_announcement_attachment_and_verify_access(
    db_session: db.Session,
    user: User,
    announcement_id: uuid.UUID,
    announcement_attachment_id: uuid.UUID,
) -> AnnouncementAttachment:
    announcement = get_announcement_and_verify_access(db_session, announcement_id, user)

    announcement_attachment = db_session.execute(
        select(AnnouncementAttachment)
        .join(Announcement)
        .where(
            AnnouncementAttachment.announcement_attachment_id == announcement_attachment_id,
            AnnouncementAttachment.announcement_id == announcement_id,
            # Don't fetch if the attachment or the announcement itself is marked as deleted
            AnnouncementAttachment.is_deleted.is_(False),
            Announcement.is_deleted.is_(False),
        )
        .options(selectinload(AnnouncementAttachment.file_attachment))
    ).scalar_one_or_none()

    if announcement_attachment is None:
        raise_flask_error(
            404, f"Could not find announcement attachment with ID {announcement_attachment_id}"
        )

    if not has_access(user, announcement, "read"):
        raise_flask_error(403, "User does not have read access to this announcement attachment")

    return announcement_attachment
