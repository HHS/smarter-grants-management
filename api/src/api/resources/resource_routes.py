import uuid
from grants_shared.api import response

from src.api.resources import resource_blueprint
from src.api.resources.resource_schemas import ListUserForResourceResponseSchema
from src.constants.lookup_constants import MgmtResourceType


@resource_blueprint.post("/<resource_type:resource_type>/<uuid:resource_id>/users/list")
@resource_blueprint.output(ListUserForResourceResponseSchema)
def list_users_in_resource(resource_type: MgmtResourceType, resource_id: uuid.UUID) -> response.ApiResponse:
    print(resource_type)
    print(resource_id)

    return response.ApiResponse(message="Success")