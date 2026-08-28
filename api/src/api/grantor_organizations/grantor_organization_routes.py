import logging
import uuid

from grants_shared.adapters import db
from grants_shared.adapters.db import flask_db
from grants_shared.api import response
from grants_shared.logs.flask_logger import add_extra_data_to_current_request_logs

from src.api.grantor_organizations.grantor_organization_blueprint import (
    grantor_organization_blueprint,
)
from src.api.grantor_organizations.grantor_organization_schemas import (
    GetGrantorOrganizationResponseSchema,
)
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.services.grantor_organizations.get_grantor_organization import (
    get_grantor_organization_and_verify_access,
)

logger = logging.getLogger(__name__)


@grantor_organization_blueprint.get("/<uuid:grantor_organization_id>")
@grantor_organization_blueprint.output(GetGrantorOrganizationResponseSchema)
@grantor_organization_blueprint.doc(
    summary="Fetch a Grantor Organization", responses=[200, 401, 403, 404, 422]
)
@grantor_organization_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def grantor_organization_get(
    db_session: db.Session, grantor_organization_id: uuid.UUID
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"grantor_organization_id": grantor_organization_id})
    logger.info("GET /v1/grantor-organizations/:grantor_organization_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        grantor_organization = get_grantor_organization_and_verify_access(
            db_session, grantor_organization_id, user
        )

    return response.ApiResponse(message="Success", data=grantor_organization)
