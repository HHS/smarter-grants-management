import uuid
from collections.abc import Container

from grants_shared.adapters import db
from grants_shared.api.route_utils import raise_flask_error

from src.constants.lookup_constants import MgmtResourceType
from src.db.models.resource_models import AbstractResourceTableMixin
from src.db.resource_lookup import get_resource_model


def get_resource(
    db_session: db.Session,
    resource_type: MgmtResourceType,
    resource_id: uuid.UUID,
    supported_resource_types: Container[MgmtResourceType] | None = None,
) -> AbstractResourceTableMixin:
    """Fetch a resource by its type and ID, erroring with a 404 if we can't.

    Pass supported_resource_types to narrow what an individual endpoint accepts - a
    type outside that set is treated the same as a missing resource.
    """
    model = get_resource_model(resource_type)

    # A type with no table, one an endpoint doesn't accept, and a mismatched type are all
    # treated the same as a missing resource, so we don't reveal that a resource with
    # that ID exists as a different type.
    if model is None or (
        supported_resource_types is not None and resource_type not in supported_resource_types
    ):
        raise_flask_error(404, f"Resource {resource_id} of type {resource_type} not found")

    resource = db_session.get(model, resource_id)

    if resource is None:
        raise_flask_error(404, f"Resource {resource_id} of type {resource_type} not found")

    return resource
