import logging
import uuid

from src.adapters import db
from src.adapters.db import flask_db
from src.api import response
from src.api.announcements.announcement_blueprint import announcement_blueprint
from src.api.announcements.announcement_schemas import (
    AnnouncementCreateRequestSchema,
    AnnouncementListRequestSchema,
    AnnouncementListResponseSchema,
    AnnouncementResponseSchema,
    AnnouncementSummaryCreateRequestSchema,
    AnnouncementSummaryResponseSchema,
    AnnouncementSummaryUpdateRequestSchema,
    AnnouncementUpdateRequestSchema, ApplicationPackageResponseSchema, ApplicationPackageCreateRequestSchema,
    ApplicationPackageUpdateRequestSchema, ApplicationPackageFormsSetRequestSchema,
)
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.logs.flask_logger import add_extra_data_to_current_request_logs
from src.services.announcements.announcement_summaries import (
    create_announcement_summary,
    update_announcement_summary,
)
from src.services.announcements.create_announcement import create_announcement
from src.services.announcements.create_application_package import create_application_package
from src.services.announcements.get_announcement import get_announcement_and_verify_access
from src.services.announcements.get_application_package import get_application_package_and_verify_access
from src.services.announcements.list_announcements import list_announcements
from src.services.announcements.update_announcement import update_announcement
from src.services.announcements.update_application_package import update_application_package
from src.services.announcements.update_application_package_forms import update_application_package_forms

logger = logging.getLogger(__name__)


@announcement_blueprint.post("")
@announcement_blueprint.input(AnnouncementCreateRequestSchema, location="json")
@announcement_blueprint.output(AnnouncementResponseSchema)
@announcement_blueprint.doc(
    summary="Create an Announcement",
    responses=[200, 401, 403, 404, 422],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def announcement_create(db_session: db.Session, json_data: dict) -> response.ApiResponse:
    logger.info("POST /v1/announcements")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)

        announcement = create_announcement(db_session, user, json_data)

    return response.ApiResponse(message="Success", data=announcement)


@announcement_blueprint.get("/<uuid:announcement_id>")
@announcement_blueprint.output(AnnouncementResponseSchema)
@announcement_blueprint.doc(
    summary="Fetch an Announcement",
    responses=[200, 401, 403, 404],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def announcement_get(db_session: db.Session, announcement_id: uuid.UUID) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"announcement_id": announcement_id})
    logger.info("GET /v1/announcements/:announcement_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        announcement = get_announcement_and_verify_access(db_session, announcement_id, user)

    return response.ApiResponse(message="Success", data=announcement)


@announcement_blueprint.put("/<uuid:announcement_id>")
@announcement_blueprint.input(AnnouncementUpdateRequestSchema, location="json")
@announcement_blueprint.output(AnnouncementResponseSchema)
@announcement_blueprint.doc(
    summary="Update an Announcement",
    responses=[200, 401, 403, 404, 422],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def announcement_update(
    db_session: db.Session,
    announcement_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"announcement_id": announcement_id})
    logger.info("PUT /v1/announcements/:announcement_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)

        announcement = update_announcement(
            db_session,
            user,
            announcement_id,
            json_data,
        )

    return response.ApiResponse(message="Success", data=announcement)


@announcement_blueprint.post("/list")
@announcement_blueprint.input(AnnouncementListRequestSchema, location="json")
@announcement_blueprint.output(AnnouncementListResponseSchema)
@announcement_blueprint.doc(
    summary="List Announcements",
    responses=[200, 401, 403, 422],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def announcement_list(db_session: db.Session, json_data: dict) -> response.ApiResponse:
    logger.info("POST /v1/announcements/list")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        announcements, pagination_info = list_announcements(db_session, user, json_data)

    return response.ApiResponse(
        message="Success",
        data=announcements,
        pagination_info=pagination_info,
    )


@announcement_blueprint.post("/<uuid:announcement_id>/summaries")
@announcement_blueprint.input(AnnouncementSummaryCreateRequestSchema, location="json")
@announcement_blueprint.output(AnnouncementSummaryResponseSchema)
@announcement_blueprint.doc(
    summary="Create an Announcement Summary",
    responses=[200, 401, 403, 404, 422],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def announcement_summary_create(
    db_session: db.Session,
    announcement_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"announcement_id": announcement_id})
    logger.info("POST /v1/announcements/:announcement_id/summaries")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        announcement_summary = create_announcement_summary(
            db_session,
            announcement_id,
            json_data,
            user,
        )

    return response.ApiResponse(message="Success", data=announcement_summary)


@announcement_blueprint.put("/<uuid:announcement_id>/summaries/<uuid:announcement_summary_id>")
@announcement_blueprint.input(AnnouncementSummaryUpdateRequestSchema, location="json")
@announcement_blueprint.output(AnnouncementSummaryResponseSchema)
@announcement_blueprint.doc(
    summary="Update an Announcement Summary",
    responses=[200, 401, 403, 404, 422],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def announcement_summary_update(
    db_session: db.Session,
    announcement_id: uuid.UUID,
    announcement_summary_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs(
        {
            "announcement_id": announcement_id,
            "announcement_summary_id": announcement_summary_id,
        }
    )
    logger.info("PUT /v1/announcements/:announcement_id/summaries/:announcement_summary_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        announcement_summary = update_announcement_summary(
            db_session,
            announcement_id,
            announcement_summary_id,
            json_data,
            user,
        )

    return response.ApiResponse(message="Success", data=announcement_summary)


@announcement_blueprint.get("/<uuid:announcement_id>/application-packages/<uuid:application_package_id>")
@announcement_blueprint.output(ApplicationPackageResponseSchema)
@announcement_blueprint.doc(
    summary="Fetch an Application Package",
    responses=[200, 401, 403, 404],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def application_package_get(db_session: db.Session, announcement_id: uuid.UUID, application_package_id: uuid.UUID) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"announcement_id": announcement_id, "application_package_id": application_package_id})
    logger.info("GET /v1/announcements/:announcement_id/application-packages/:application_package_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        application_package = get_application_package_and_verify_access(db_session, user, announcement_id, application_package_id)

    return response.ApiResponse(message="Success", data=application_package)


@announcement_blueprint.post("/<uuid:announcement_id>/application-packages")
@announcement_blueprint.input(ApplicationPackageCreateRequestSchema)
@announcement_blueprint.output(ApplicationPackageResponseSchema)
@announcement_blueprint.doc(
    summary="Create an Application Package",
    responses=[200, 401, 403, 404, 422],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def application_package_create(db_session: db.Session, announcement_id: uuid.UUID, json_data: dict) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"announcement_id": announcement_id})
    logger.info("POST /v1/announcements/:announcement_id/application-packages")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)

        application_package = create_application_package(db_session, user, json_data, announcement_id)

    return response.ApiResponse(message="Success", data=application_package)

@announcement_blueprint.put("/<uuid:announcement_id>/application-packages/<uuid:application_package_id>")
@announcement_blueprint.input(ApplicationPackageUpdateRequestSchema)
@announcement_blueprint.output(ApplicationPackageResponseSchema)
@announcement_blueprint.doc(
    summary="Update an Application Package",
    responses=[200, 401, 403, 404, 422],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def application_package_update(db_session: db.Session, announcement_id: uuid.UUID, application_package_id: uuid.UUID, json_data: dict) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"announcement_id": announcement_id, "application_package_id": application_package_id})
    logger.info("PUT /v1/announcements/:announcement_id/application-packages/:application_package_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)

        application_package = update_application_package(db_session, user, announcement_id, application_package_id, json_data)

    return response.ApiResponse(message="Success", data=application_package)

@announcement_blueprint.put("/<uuid:announcement_id>/application-packages/<uuid:application_package_id>/forms")
@announcement_blueprint.input(ApplicationPackageFormsSetRequestSchema)
@announcement_blueprint.output(ApplicationPackageResponseSchema)
@announcement_blueprint.doc(
    summary="Update an Application Package",
    responses=[200, 401, 403, 404, 422],
)
@announcement_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def put_application_package_forms(db_session: db.Session, announcement_id: uuid.UUID, application_package_id: uuid.UUID, json_data: dict) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"announcement_id": announcement_id, "application_package_id": application_package_id})
    logger.info("PUT /v1/announcements/:announcement_id/application-packages/:application_package_id/forms")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)

        application_package = update_application_package_forms(db_session, user, announcement_id, application_package_id, json_data)

    return response.ApiResponse(message="Success", data=application_package)
