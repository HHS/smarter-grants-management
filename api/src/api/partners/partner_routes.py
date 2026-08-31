import logging
import uuid

from src.adapters import db
from src.adapters.db import flask_db
from src.api import response
from src.api.partners.partner_blueprint import partner_blueprint
from src.api.partners.partner_schemas import GetPartnerResponseSchema
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.logs.flask_logger import add_extra_data_to_current_request_logs
from src.services.partners.get_partner import get_partner_and_verify_access

logger = logging.getLogger(__name__)


@partner_blueprint.get("/<uuid:partner_id>")
@partner_blueprint.output(GetPartnerResponseSchema)
@partner_blueprint.doc(summary="Fetch a Partner", responses=[200, 401, 403, 404, 422])
@partner_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def partner_get(db_session: db.Session, partner_id: uuid.UUID) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"partner_id": partner_id})
    logger.info("GET /v1/partners/:partner_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        partner = get_partner_and_verify_access(db_session, partner_id, user)

    return response.ApiResponse(message="Success", data=partner)
