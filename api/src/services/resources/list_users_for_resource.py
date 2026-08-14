import dataclasses
import logging
import uuid
from collections.abc import Sequence

from grants_shared.adapters import db
from grants_shared.pagination.pagination_models import PaginationInfo, PaginationParams
from grants_shared.pagination.paginator import Paginator
from grants_shared.pagination.sorting_util import apply_sorting
from pydantic import BaseModel, Field
from sqlalchemy.orm import InstrumentedAttribute

from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import Privilege, ResourceInheritance, ResourceType
from src.db.models.resource_models import AbstractResourceTableMixin, Role
from src.db.models.user_models import LinkExternalUser, User
from src.services.resources.get_resource import get_resource

logger = logging.getLogger(__name__)

# The privilege a caller needs on the resource in order to list its users. This also
# defines which resource types the endpoint supports at all - deliberately narrower than
# what get_resource can fetch, with the others added as we need them.
REQUIRED_PRIVILEGE_FOR_RESOURCE_TYPE = {
    ResourceType.PARTNER: Privilege.VIEW_PARTNER,
    ResourceType.GRANTOR_ORGANIZATION: Privilege.VIEW_GRANTOR_ORGANIZATION,
    ResourceType.PROGRAM: Privilege.VIEW_PROGRAM,
}

# email lives on the login.gov link rather than the user, so it can't be resolved by
# name off User - we join that table below and point sorting straight at its column.
SORT_COLUMN_MAP: dict[str, InstrumentedAttribute] = {
    "user_id": User.user_id,
    "email": LinkExternalUser.email,
}


class PrivilegeFilter(BaseModel):
    one_of: set[Privilege] = set()


class InheritanceFilter(BaseModel):
    one_of: list[ResourceInheritance] = []


class ListUsersForResourceFilters(BaseModel):
    privilege: PrivilegeFilter = Field(default_factory=PrivilegeFilter)
    inheritance: InheritanceFilter = Field(default_factory=InheritanceFilter)

    @property
    def required_privileges(self) -> set[Privilege]:
        return self.privilege.one_of

    @property
    def resource_inheritance(self) -> ResourceInheritance:
        """The single inheritance value, defaulting to direct.

        Shaped as a one_of for consistency with every other filter, but the schema caps
        it at one value, so at most one ever arrives here.
        """
        if self.inheritance.one_of:
            return self.inheritance.one_of[0]

        return ResourceInheritance.DIRECT


class ListUsersForResourceRequest(BaseModel):
    filters: ListUsersForResourceFilters = Field(default_factory=ListUsersForResourceFilters)
    pagination: PaginationParams


####################################
# Response objects
#
# The response is a reshaped view of the data model rather than a direct dump of it,
# so it gets built explicitly here instead of the schema reaching through relationships.
####################################


@dataclasses.dataclass
class ResourceRef:
    resource_id: uuid.UUID
    resource_name: str | None


@dataclasses.dataclass
class RoleForUser:
    """A role a user holds, and the resource that granted it."""

    role_id: uuid.UUID
    role_name: str
    privileges: list[Privilege]
    resource_type: ResourceType
    resource: ResourceRef


@dataclasses.dataclass
class UserForResource:
    user_id: uuid.UUID
    email: str | None
    roles: list[RoleForUser]


def list_users_for_resource(
    db_session: db.Session,
    acting_user: User,
    resource_type: ResourceType,
    resource_id: uuid.UUID,
    json_data: dict,
) -> tuple[Sequence[UserForResource], PaginationInfo]:
    """List the users holding roles on a resource, with the roles that grant them.

    Raises:
        404: If the resource doesn't exist, or isn't a type this endpoint supports
        403: If the acting user can't view the resource
    """
    params = ListUsersForResourceRequest.model_validate(json_data)

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

    # The resources that can grant a role for this lookup. We keep the objects rather
    # than just their IDs because they carry the names the response reports, which saves
    # re-fetching them per role below.
    relevant_resources = enforcer.get_resources_for_user_lookup(
        resource, params.filters.resource_inheritance
    )
    resource_by_id = {relevant.get_resource_id(): relevant for relevant in relevant_resources}

    log_extra = {
        "resource_id": resource_id,
        "resource_type": resource_type,
        "inheritance": params.filters.resource_inheritance,
        "required_privileges": "|".join(sorted(params.filters.required_privileges)),
        "relevant_resource_count": len(relevant_resources),
    }
    logger.info("Listing users for resource", extra=log_extra)

    stmt = enforcer.get_users_for_resource_query(
        relevant_resources, required_privileges=params.filters.required_privileges
    )

    # Sorting is allowed on email, which lives on the login.gov link rather than on
    # User, so that table has to be in the FROM clause. Outer, because a user
    # without a login still belongs in the results.
    # nulls_last so those users sort to the end rather than leading the first page.
    stmt = stmt.outerjoin(User.linked_login_gov_external_user)
    stmt = apply_sorting(stmt, params.pagination.sort_order, SORT_COLUMN_MAP, nulls_last=True)

    paginator: Paginator[User] = Paginator(
        User, stmt, db_session, page_size=params.pagination.page_size
    )
    users = paginator.page_at(page_offset=params.pagination.page_offset)
    pagination_info = PaginationInfo.from_pagination_params(params.pagination, paginator)

    # Roles are fetched for just this page of users rather than joined into the query
    # above, which would fan out the user rows and throw off the pagination counts.
    roles_by_user = enforcer.get_roles_by_user_for_resources(
        [user.user_id for user in users], list(resource_by_id.keys())
    )

    users_for_resource = [
        UserForResource(
            user_id=user.user_id,
            email=user.email,
            roles=[
                _build_role_for_user(role, resource_by_id[granting_resource_id])
                for granting_resource_id, role in roles_by_user.get(user.user_id, [])
            ],
        )
        for user in users
    ]

    logger.info(
        "Listed users for resource",
        extra=log_extra | {"user_count": pagination_info.total_records},
    )

    return users_for_resource, pagination_info


def _build_role_for_user(role: Role, granting_resource: AbstractResourceTableMixin) -> RoleForUser:
    return RoleForUser(
        role_id=role.role_id,
        role_name=role.role_name,
        # privileges is a set on the model, so sort it for a stable response order
        privileges=sorted(role.privileges),
        resource_type=granting_resource.get_resource_type(),
        resource=ResourceRef(
            resource_id=granting_resource.get_resource_id(),
            resource_name=granting_resource.resource_name,
        ),
    )
