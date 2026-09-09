import logging
import uuid

from src.adapters import db
from src.adapters.db import flask_db
from src.api import response
from src.api.programs.program_blueprint import program_blueprint
from src.api.programs.program_schemas import GetProgramResponseSchema
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.logs.flask_logger import add_extra_data_to_current_request_logs
from src.services.programs.get_program import get_program_and_verify_access

logger = logging.getLogger(__name__)


@program_blueprint.get("/<uuid:program_id>")
@program_blueprint.output(GetProgramResponseSchema)
@program_blueprint.doc(summary="Fetch a Program", responses=[200, 401, 403, 404, 422])
@program_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def program_get(db_session: db.Session, program_id: uuid.UUID) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"program_id": program_id})
    logger.info("GET /v1/programs/:program_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        program = get_program_and_verify_access(db_session, program_id, user)

    return response.ApiResponse(message="Success", data=program)
