import logging
import uuid
from collections.abc import Callable, Sequence
from typing import Any

from src.adapters import db
from src.constants.lookup_constants import AnnouncementAuditEvent
from src.db.models.announcement_models import AnnouncementAudit
from src.db.models.user_models import User
from src.util.dict_util import diff_nested_dicts
from src.util.json_util import json_encoder

logger = logging.getLogger(__name__)


def snapshot_fields(
    obj: object | None,
    fields: Sequence[str],
    extractors: dict[str, Callable[[object], Any]] | None = None,
) -> dict[str, Any]:
    extractors = extractors or {}
    snapshot: dict[str, Any] = {}
    for field in fields:
        if obj is None:
            snapshot[field] = None
        elif field in extractors:
            snapshot[field] = extractors[field](obj)
        else:
            snapshot[field] = getattr(obj, field)
    return snapshot


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_normalize(val) for val in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return json_encoder(value)


def build_changed_fields(before: dict, after: dict) -> dict:
    normalized_before = _normalize(before)
    normalized_after = _normalize(after)

    diffs = diff_nested_dicts(normalized_before, normalized_after)

    return {
        "changed_fields": {
            diff["field"]: {"before": diff["before"], "after": diff["after"]} for diff in diffs
        }
    }


def record_announcement_audit(
    db_session: db.Session,
    user: User,
    announcement_id: uuid.UUID,
    audit_event: AnnouncementAuditEvent,
    before: dict,
    after: dict,
    *,
    announcement_summary_id: uuid.UUID | None = None,
    application_package_id: uuid.UUID | None = None,
) -> AnnouncementAudit:
    audit = AnnouncementAudit(
        announcement_audit_id=uuid.uuid4(),
        announcement_id=announcement_id,
        user_id=user.user_id,
        announcement_audit_event=audit_event,
        announcement_summary_id=announcement_summary_id,
        application_package_id=application_package_id,
        audit_metadata=build_changed_fields(before, after),
    )
    db_session.add(audit)

    logger.info(
        "Recorded announcement audit event",
        extra={
            "announcement_id": announcement_id,
            "announcement_audit_event": audit_event,
            "announcement_summary_id": announcement_summary_id,
            "application_package_id": application_package_id,
        },
    )

    return audit
