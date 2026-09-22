import logging
import uuid
from typing import cast

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import AnnouncementAuditEvent, ApplicationPackageOpenToApplicant
from src.db.models.application_package_models import ApplicationPackage
from src.db.models.user_models import User
from src.services.announcements.announcement_audit import record_announcement_audit, snapshot_fields
from src.services.announcements.authorization import has_access
from src.services.announcements.get_application_package import (
    get_application_package_and_verify_access,
)

logger = logging.getLogger(__name__)

APPLICATION_PACKAGE_UPDATE_FIELDS = (
    "application_package_title",
    "public_application_package_id",
    "opening_timestamp",
    "closing_timestamp",
    "grace_period",
    "contact_info",
    "open_to_applicants",
)


def update_application_package(
    db_session: db.Session,
    user: User,
    announcement_id: uuid.UUID,
    application_package_id: uuid.UUID,
    json_data: dict,
) -> ApplicationPackage:
    application_package = get_application_package_and_verify_access(
        db_session, user, announcement_id, application_package_id
    )

    if not has_access(user, application_package, "update"):
        raise_flask_error(403, "User does not have access to update this application package")

    before = snapshot_fields(application_package, APPLICATION_PACKAGE_UPDATE_FIELDS)

    application_package.application_package_title = json_data.get("application_package_title")
    application_package.public_application_package_id = json_data.get(
        "public_application_package_id"
    )
    application_package.grace_period = json_data.get("grace_period")
    application_package.opening_timestamp = json_data.get("opening_timestamp")
    application_package.closing_timestamp = json_data.get("closing_timestamp")
    application_package.contact_info = json_data.get("contact_info")
    application_package.open_to_applicants = cast(
        set[ApplicationPackageOpenToApplicant], json_data.get("open_to_applicants")
    )

    after = snapshot_fields(application_package, APPLICATION_PACKAGE_UPDATE_FIELDS)

    logger.info(
        "Updated application package", extra={"application_package_id": application_package_id}
    )

    record_announcement_audit(
        db_session,
        user,
        announcement_id,
        AnnouncementAuditEvent.APPLICATION_PACKAGE_UPDATED,
        before,
        after,
        application_package_id=application_package_id,
    )

    return application_package
