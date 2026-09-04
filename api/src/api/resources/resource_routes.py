import logging
import uuid

import src.adapters.db as db
from src.adapters.db import flask_db
from src.api import response
from src.api.resources.resource_blueprint import resource_blueprint
from src.api.resources.resource_schemas import (
    ListRolesForResourceRequestSchema,
    ListRolesForResourceResponseSchema,
    ListUserForResourceRequestSchema,
    ListUserForResourceResponseSchema,
)
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.constants.lookup_constants import ResourceType
from src.logs.flask_logger import add_extra_data_to_current_request_logs
from src.services.resources.list_roles_for_resource import list_roles_for_resource
from src.services.resources.list_users_for_resource import list_users_for_resource

logger = logging.getLogger(__name__)


@resource_blueprint.post("/<resource_type:resource_type>/<uuid:resource_id>/users/list")
@resource_blueprint.input(ListUserForResourceRequestSchema)
@resource_blueprint.output(ListUserForResourceResponseSchema)
@resource_blueprint.doc(
    summary="List Users For Resource",
    description="List the users who can access a resource, along with the roles that grant them access.",
    responses=[200, 401, 403, 404, 422],
)
@resource_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def list_users_in_resource(
    db_session: db.Session,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs(
        {"resource_type": resource_type, "resource_id": str(resource_id)}
    )
    logger.info("POST /v1/resources/:resource_type/:resource_id/users/list")

    with db_session.begin():
        acting_user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(acting_user)

        users, pagination_info = list_users_for_resource(
            db_session,
            acting_user=acting_user,
            resource_type=resource_type,
            resource_id=resource_id,
            json_data=json_data,
        )

    return response.ApiResponse(message="Success", data=users, pagination_info=pagination_info)


@resource_blueprint.post("/<resource_type:resource_type>/<uuid:resource_id>/roles/list")
@resource_blueprint.input(ListRolesForResourceRequestSchema)
@resource_blueprint.output(ListRolesForResourceResponseSchema)
@resource_blueprint.doc(
    summary="List Roles For Resource",
    description="List the roles available for assignment on a resource.",
    responses=[200, 401, 403, 404, 422],
)
@resource_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def list_roles_in_resource(
    db_session: db.Session,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs(
        {"resource_type": resource_type, "resource_id": resource_id}
    )
    logger.info("POST /v1/resources/:resource_type/:resource_id/roles/list")

    with db_session.begin():
        acting_user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(acting_user)

        roles, pagination_info = list_roles_for_resource(
            db_session,
            acting_user=acting_user,
            resource_type=resource_type,
            resource_id=resource_id,
            json_data=json_data,
        )

    return response.ApiResponse(message="Success", data=roles, pagination_info=pagination_info)
