import dataclasses
import logging
import uuid
from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import select

from src.adapters import db
from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import VIEW_PRIVILEGE_FOR_RESOURCE_TYPE, Privilege, ResourceType
from src.db.models.resource_models import LinkRoleResourceType, Role
from src.db.models.user_models import User
from src.pagination.pagination_models import PaginationInfo, PaginationParams, SortOrder
from src.pagination.paginator import Paginator
from src.pagination.sorting_util import apply_sorting
from src.services.resources.get_resource import get_resource

logger = logging.getLogger(__name__)


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
        403: If the acting user can't view the resource
        404: If the resource doesn't exist, or isn't a type this endpoint supports
    """
    params = ListRolesForResourceRequest.model_validate(json_data)

    resource = get_resource(
        db_session,
        resource_type,
        resource_id,
        supported_resource_types=VIEW_PRIVILEGE_FOR_RESOURCE_TYPE.keys(),
    )

    enforcer = AuthorizationEnforcer(db_session)
    enforcer.verify_access(
        user=acting_user,
        required_privileges={VIEW_PRIVILEGE_FOR_RESOURCE_TYPE[resource_type]},
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
        .join(LinkRoleResourceType)
        .where(Role.is_core.is_(True))
        .where(LinkRoleResourceType.resource_type == resource_type)
    )

    stmt = apply_sorting(stmt, params.pagination.sort_order, Role)

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
