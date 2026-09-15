import logging
import uuid

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.application_package_models import ApplicationPackage
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_announcement import get_announcement_and_verify_access

logger = logging.getLogger(__name__)

def create_application_package(db_session: db.Session, user: User, json_data: dict, announcement_id: uuid.UUID) -> ApplicationPackage:
    # Fetch / verify announcement exists and user can access
    announcement = get_announcement_and_verify_access(db_session, announcement_id, user)

    # Verify user can update the announcement
    if not has_access(user, announcement, "update"):
        raise_flask_error(403, "User does not have access to update this announcement")

    # Create the package
    application_package = ApplicationPackage(
        application_package_id=uuid.uuid4(),
        announcement=announcement,
        # Set these to empty so when we create the response,
        # we don't try to fetch them from the DB.
        application_package_forms=[],
        application_package_instructions=[],
        # Pass in the data from the user
        **json_data
    )

    db_session.add(application_package)

    # Auto-set assistance listing from announcement (currently one per announcement)
    if announcement.announcement_assistance_listings:
        application_package.announcement_assistance_listing = announcement.announcement_assistance_listings[0]


    logger.info("Created application package", extra={"application_package_id": application_package.application_package_id})

    return application_package
