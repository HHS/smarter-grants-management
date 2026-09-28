import logging
import uuid

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_application_package_instruction import (
    get_application_package_instruction_and_verify_access,
)

logger = logging.getLogger(__name__)


def delete_application_package_instruction(
    db_session: db.Session,
    user: User,
    announcement_id: uuid.UUID,
    application_package_id: uuid.UUID,
    application_package_instruction_id: uuid.UUID,
) -> None:
    application_package_instruction = get_application_package_instruction_and_verify_access(
        db_session,
        user,
        announcement_id,
        application_package_id,
        application_package_instruction_id,
    )

    if not has_access(user, application_package_instruction.application_package, "update"):
        raise_flask_error(
            403, "User does not have access to update this application package instruction"
        )

    application_package_instruction.is_deleted = True

    logger.info(
        "Soft-deleted application package instruction",
        extra={
            "announcement_id": announcement_id,
            "application_package_id": application_package_id,
            "application_package_instruction_id": application_package_instruction_id,
        },
    )
