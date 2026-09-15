from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.announcement_models import AnnouncementAssistanceListing
from src.db.models.application_package_models import ApplicationPackage, ApplicationPackageInstruction
from src.db.models.user_models import User
import uuid

from src.services.announcements.authorization import has_access


def get_application_package(db_session: db.Session, announcement_id: uuid.UUID, application_package_id: uuid.UUID) -> ApplicationPackage:

    application_package = db_session.execute(
        select(ApplicationPackage)
        .where(ApplicationPackage.announcement_id == announcement_id, ApplicationPackage.application_package_id == application_package_id)
        .options(selectinload(ApplicationPackage.application_package_forms),
                 selectinload(ApplicationPackage.link_application_package_open_to_applicant),
                 selectinload(ApplicationPackage.application_package_instructions).selectinload(ApplicationPackageInstruction.file_attachment),
                 selectinload(ApplicationPackage.announcement_assistance_listing).selectinload(AnnouncementAssistanceListing.assistance_listing))
    ).scalar_one_or_none()

    if application_package is None:
        raise_flask_error(404, message=f"Could not find application package with ID {application_package_id}")

    return application_package

def get_application_package_and_verify_access(db_session: db.Session, user: User, announcement_id: uuid.UUID, application_package_id: uuid.UUID) -> ApplicationPackage:
    application_package = get_application_package(db_session, announcement_id, application_package_id)

    if not has_access(user, application_package, "read"):
        raise_flask_error(403, "User does not have access to read this application package")

    return application_package