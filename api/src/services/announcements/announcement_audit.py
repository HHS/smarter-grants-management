import logging
import uuid

from src.adapters import db
from src.constants.lookup_constants import AnnouncementAuditEvent
from src.db.models.announcement_models import Announcement, AnnouncementAudit, AnnouncementSummary
from src.db.models.application_package_models import ApplicationPackage
from src.db.models.user_models import User
from src.util.dict_util import diff_nested_dicts

logger = logging.getLogger(__name__)


def record_announcement_audit(
    *,
    db_session: db.Session,
    user: User,
    announcement: Announcement,
    audit_event: AnnouncementAuditEvent,
    before: dict,
    after: dict,
    announcement_summary: AnnouncementSummary | None = None,
    application_package: ApplicationPackage | None = None,
) -> AnnouncementAudit:
    audit = AnnouncementAudit(
        announcement_audit_id=uuid.uuid4(),
        announcement=announcement,
        user=user,
        announcement_audit_event=audit_event,
        announcement_summary=announcement_summary,
        application_package=application_package,
        audit_metadata={"changed_fields": diff_nested_dicts(before, after)},
    )
    db_session.add(audit)

    logger.info(
        "Recorded announcement audit event",
        extra={
            "announcement_id": announcement.announcement_id,
            "announcement_audit_event": audit_event,
            "announcement_summary_id": (
                announcement_summary.announcement_summary_id if announcement_summary else None
            ),
            "application_package_id": (
                application_package.application_package_id if application_package else None
            ),
        },
    )

    return audit
