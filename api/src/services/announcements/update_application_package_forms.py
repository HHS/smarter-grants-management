import logging
import uuid

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.application_package_models import ApplicationPackage, ApplicationPackageForm
from src.db.models.user_models import User
from src.services.announcements.authorization import has_access
from src.services.announcements.get_application_package import (
    get_application_package_and_verify_access,
)

logger = logging.getLogger(__name__)


def _reconcile_forms(
    db_session: db.Session, request_forms: list[dict], application_package: ApplicationPackage
) -> None:
    existing_form_map: dict[int, ApplicationPackageForm] = {
        form.form_id: form for form in application_package.application_package_forms
    }

    target_form_ids: set[int] = set()

    for form_data in request_forms:
        form_id = form_data["form_id"]
        is_required = form_data["is_required"]
        extra = {"form_id": form_id, "is_required": is_required}

        target_form_ids.add(form_id)

        existing_package_form = existing_form_map.get(form_id)

        # Updating an existing form
        if existing_package_form:
            logger.info("Updating application package form", extra=extra)
            existing_package_form.is_required = is_required

        else:  # Create
            logger.info("Adding application package form", extra=extra)
            db_session.add(
                ApplicationPackageForm(
                    application_package=application_package,
                    form_id=form_id,
                    is_required=is_required,
                )
            )

    # remove forms not included in request
    forms_to_remove = []
    for existing_package_form in application_package.application_package_forms:
        if existing_package_form.form_id not in target_form_ids:
            logger.info(
                "Removing application package form",
                extra={"form_id": existing_package_form.form_id},
            )
            forms_to_remove.append(existing_package_form)

    for form in forms_to_remove:
        application_package.application_package_forms.remove(form)


def update_application_package_forms(
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

    # TODO - we previously had a check here that verified the form IDs passed in were valid
    # but we don't have a place to fetch forms from at the moment, so that's excluded.

    _reconcile_forms(db_session, json_data["forms"], application_package)

    return application_package
