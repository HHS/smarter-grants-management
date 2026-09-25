import logging

from src.adapters import db
from src.adapters.db import flask_db
from src.api import response
from src.api.internal.internal_blueprint import internal_blueprint
from src.api.internal.internal_schemas import ApiJwtResponseSchema
from src.auth.api_jwt_auth import create_jwt_for_user
from src.auth.api_user_key_auth import api_user_key_auth

logger = logging.getLogger(__name__)


@internal_blueprint.get("/api-jwt")
@internal_blueprint.output(ApiJwtResponseSchema)
@internal_blueprint.doc(
    summary="Get a JWT for a user by using an API key to authenticate", responses=[200, 401]
)
@internal_blueprint.auth_required(api_user_key_auth)
@flask_db.with_db_session()
def get_jwt_from_key(db_session: db.Session) -> response.ApiResponse:
    """
    Get a JWT for a user based on the API key authenticated user calling it.

    This is a temporary workaround for login before we build/adjust our existing
    login approach to integrate with the rest of the system.
    """
    logger.info("GET /v1/internal/api-jwt")

    with db_session.begin():
        user = api_user_key_auth.get_user()
        db_session.add(user)

        jwt_token, _ = create_jwt_for_user(user, db_session)

    return response.ApiResponse(message="Success", data={"jwt_token": jwt_token})
