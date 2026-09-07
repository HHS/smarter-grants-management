import logging
import uuid

from src.adapters import db
from src.adapters.db import flask_db
from src.api import response
from src.api.files import file_schemas
from src.api.files.file_blueprint import file_blueprint
from src.auth.api_user_key_auth import api_user_key_auth
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.logs.flask_logger import add_extra_data_to_current_request_logs
from src.services.files.create_presigned_upload import GrantsManagementPresignFileUploadService
from src.services.files.update_pending_file_scan_status import update_pending_file_scan_status

logger = logging.getLogger(__name__)


@file_blueprint.post("")
@file_blueprint.input(file_schemas.CreatePresignedUploadRequestSchema, location="json")
@file_blueprint.output(file_schemas.CreatePresignedUploadResponseSchema)
@file_blueprint.doc(
    summary="Create a presigned upload URL",
    responses=[200, 401, 429],
)
@file_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def create_presigned_upload_route(
    db_session: db.Session,
    json_data: dict,
) -> response.ApiResponse:
    user = jwt_or_api_user_key_multi_auth.get_user()
    add_extra_data_to_current_request_logs({"user_id": user.user_id})
    logger.info("POST /v1/files")

    with db_session.begin():
        db_session.add(user)
        result = GrantsManagementPresignFileUploadService(db_session).create_presigned_upload(
            user=user,
            file_name=json_data["file_name"],
            mime_type=json_data["mime_type"],
        )

    add_extra_data_to_current_request_logs({"pending_file_id": result.pending_file_id})

    return response.ApiResponse(
        message="Success",
        data={
            "url": result.url,
            "body": result.body,
            "pending_file_id": result.pending_file_id,
        },
    )


@file_blueprint.post("/<uuid:pending_file_id>")
@file_blueprint.input(file_schemas.FileScanStatusUpdateRequestSchema, location="json")
@file_blueprint.output(file_schemas.FileScanStatusUpdateResponseSchema)
@file_blueprint.doc(hide=True)
@file_blueprint.auth_required(api_user_key_auth)
@flask_db.with_db_session()
def update_file_scan_status(
    db_session: db.Session,
    pending_file_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"pending_file_id": pending_file_id})
    logger.info("POST /v1/files/<pending_file_id>")

    with db_session.begin():
        user = api_user_key_auth.get_user()
        db_session.add(user)

        update_pending_file_scan_status(
            db_session,
            pending_file_id,
            json_data["file_scan_status"],
            json_data["file_location"],
            user,
        )

    return response.ApiResponse(message="Success")
