import dataclasses
import logging
import uuid
from collections.abc import Sequence

from grants_shared.adapters import db
from grants_shared.pagination.pagination_models import PaginationInfo, PaginationParams, SortOrder
from grants_shared.pagination.paginator import Paginator
from grants_shared.pagination.sorting_util import apply_sorting
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute

from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import Privilege, ResourceType
from src.db.models.resource_models import LinkRoleResourceType, Role
from src.db.models.user_models import User
from src.services.resources.get_resource import get_resource

logger = logging.getLogger(__name__)

# The privilege a caller needs on the resource in order to list its roles.
REQUIRED_PRIVILEGE_FOR_RESOURCE_TYPE = {
    ResourceType.PARTNER: Privilege.VIEW_PARTNER,
    ResourceType.GRANTOR_ORGANIZATION: Privilege.VIEW_GRANTOR_ORGANIZATION,
    ResourceType.PROGRAM: Privilege.VIEW_PROGRAM,
}

# Mapping for sorting columns on the Role table
SORT_COLUMN_MAP: dict[str, InstrumentedAttribute] = {
    "role_id": Role.role_id,
    "role_name": Role.role_name,
}


class ListRolesForResourceRequest(BaseModel):
    pagination: PaginationParams


####################################
# Response objects
####################################


@dataclasses.dataclass
class RoleForResource:
    """A role available for assignment on a resource."""

    role_id: uuid.UUID
    role_name: str
    privileges: list[Privilege]


def list_roles_for_resource(
    db_session: db.Session,
    acting_user: User,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
    json_data: dict,
) -> tuple[Sequence[RoleForResource], PaginationInfo]:
    """List the roles associated with a resource.

    Raises:
        404: If the resource doesn't exist, or isn't a type this endpoint supports
        403: If the acting user can't view the resource
    """
    params = ListRolesForResourceRequest.model_validate(json_data)

    resource = get_resource(
        db_session,
        resource_type,
        resource_id,
        supported_resource_types=REQUIRED_PRIVILEGE_FOR_RESOURCE_TYPE.keys(),
    )

    enforcer = AuthorizationEnforcer(db_session)
    enforcer.verify_access(
        user=acting_user,
        required_privileges={REQUIRED_PRIVILEGE_FOR_RESOURCE_TYPE[resource_type]},
        resource=resource,
    )

    log_extra = {
        "resource_id": resource_id,
        "resource_type": resource_type,
    }
    logger.info("Listing roles for resource", extra=log_extra)

    # If the resource type is program, return an empty list
    # as users cannot be assigned directly to programs
    if resource_type == ResourceType.PROGRAM:
        logger.info(
            "Returning empty list for program resource type",
            extra=log_extra,
        )
        # Create an empty paginator result for programs
        empty_pagination_info = PaginationInfo(
            page_offset=params.pagination.page_offset,
            page_size=params.pagination.page_size,
            total_pages=0,
            total_records=0,
            sort_order=[
                SortOrder(order_by=sort.order_by, sort_direction=sort.sort_direction)
                for sort in params.pagination.sort_order
            ],
        )
        return [], empty_pagination_info

    # Build query for core roles applicable to this resource type
    stmt = (
        select(Role)
        .where(Role.is_core.is_(True))
        .where(
            Role.role_id.in_(
                select(LinkRoleResourceType.role_id).where(
                    LinkRoleResourceType.resource_type == resource_type
                )
            )
        )
    )

    stmt = apply_sorting(stmt, params.pagination.sort_order, SORT_COLUMN_MAP)

    paginator: Paginator[Role] = Paginator(
        Role, stmt, db_session, page_size=params.pagination.page_size
    )
    roles = paginator.page_at(page_offset=params.pagination.page_offset)
    pagination_info = PaginationInfo.from_pagination_params(params.pagination, paginator)

    roles_for_resource = [
        RoleForResource(
            role_id=role.role_id,
            role_name=role.role_name,
            privileges=sorted(role.privileges),
        )
        for role in roles
    ]

    logger.info(
        "Listed roles for resource",
        extra=log_extra | {"role_count": pagination_info.total_records},
    )

    return roles_for_resource, pagination_info
