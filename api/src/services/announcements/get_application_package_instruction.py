import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.announcement_models import Announcement
from src.db.models.application_package_models import (
    ApplicationPackage,
    ApplicationPackageInstruction,
)
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access


def get_application_package_instruction_and_verify_access(
    db_session: db.Session,
    user: User,
    announcement_id: uuid.UUID,
    application_package_id: uuid.UUID,
    application_package_instruction_id: uuid.UUID,
) -> ApplicationPackageInstruction:

    application_package_instruction = db_session.execute(
        select(ApplicationPackageInstruction)
        .join(ApplicationPackage)
        .join(Announcement)
        .where(
            ApplicationPackageInstruction.application_package_instruction_id
            == application_package_instruction_id,
            ApplicationPackageInstruction.is_deleted.is_(False),
        )
        .where(
            ApplicationPackage.application_package_id == application_package_id,
            ApplicationPackage.is_deleted.is_(False),
        )
        .where(Announcement.announcement_id == announcement_id, Announcement.is_deleted.is_(False))
        .options(selectinload(ApplicationPackageInstruction.file_attachment))
    ).scalar_one_or_none()

    if application_package_instruction is None:
        raise_flask_error(
            404,
            f"Could not find application package instruction with id {application_package_instruction_id}",
        )

    if not has_access(user, application_package_instruction.application_package, "read"):
        raise_flask_error(
            403, "User does not have read access to this application package instruction"
        )

    return application_package_instruction
