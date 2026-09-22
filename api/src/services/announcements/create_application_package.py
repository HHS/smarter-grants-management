import logging
import uuid

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import AnnouncementAuditEvent
from src.db.models.application_package_models import ApplicationPackage
from src.db.models.user_models import User
from src.services.announcements.announcement_audit import record_announcement_audit, snapshot_fields
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import get_announcement_and_verify_access

logger = logging.getLogger(__name__)

APPLICATION_PACKAGE_CREATE_FIELDS = (
    "application_package_title",
    "public_application_package_id",
    "opening_timestamp",
    "closing_timestamp",
    "grace_period",
    "contact_info",
    "open_to_applicants",
    "announcement_assistance_listing_id",
)


def create_application_package(
    db_session: db.Session, user: User, json_data: dict, announcement_id: uuid.UUID
) -> ApplicationPackage:
    # Fetch / verify announcement exists and user can access
    announcement = get_announcement_and_verify_access(db_session, announcement_id, user)

    # Verify user can update the announcement
    if not has_access(user, announcement, "update"):
        raise_flask_error(403, "User does not have access to update this announcement")

    before = snapshot_fields(None, APPLICATION_PACKAGE_CREATE_FIELDS)

    # Create the package
    application_package = ApplicationPackage(
        application_package_id=uuid.uuid4(),
        announcement=announcement,
        # Set these to empty so when we create the response,
        # we don't try to fetch them from the DB.
        application_package_forms=[],
        application_package_instructions=[],
        # Pass in the data from the user
        **json_data,
    )

    db_session.add(application_package)

    # Auto-set assistance listing from announcement (currently one per announcement)
    if announcement.announcement_assistance_listings:
        application_package.announcement_assistance_listing = (
            announcement.announcement_assistance_listings[0]
        )
    else:
        # Set this to None explicitly so SQLAlchemy doesn't try to load it when we make the response
        application_package.announcement_assistance_listing = None

    # Flush so the assistance-listing FK column (synced only at flush, not at
    # assignment) is populated before we snapshot it below.
    db_session.flush()
    after = snapshot_fields(application_package, APPLICATION_PACKAGE_CREATE_FIELDS)

    logger.info(
        "Created application package",
        extra={"application_package_id": application_package.application_package_id},
    )

    record_announcement_audit(
        db_session,
        user,
        announcement.announcement_id,
        AnnouncementAuditEvent.APPLICATION_PACKAGE_CREATED,
        before,
        after,
        application_package_id=application_package.application_package_id,
    )

    return application_package
