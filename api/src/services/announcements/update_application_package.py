import logging
import uuid
from typing import cast

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import ApplicationPackageOpenToApplicant
from src.db.models.application_package_models import ApplicationPackage
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_application_package import (
    get_application_package_and_verify_access,
)

logger = logging.getLogger(__name__)


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

    logger.info("Updated application package")

    return application_package
