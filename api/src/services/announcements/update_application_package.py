import logging
import uuid

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.application_package_models import ApplicationPackage
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_application_package import get_application_package_and_verify_access

logger = logging.getLogger(__name__)

def update_application_package(db_session: db.Session, user: User, announcement_id: uuid.UUID, application_package_id: uuid.UUID, json_data: dict) -> ApplicationPackage:
    application_package = get_application_package_and_verify_access(db_session, user, announcement_id, application_package_id)

    if not has_access(user, application_package, "update"):
        raise_flask_error(403, "User does not have access to update this application package")

    for field, value in json_data.items():
        setattr(application_package, field, value)

    logger.info("Updated application package")

    return application_package