import logging
import uuid
from collections import defaultdict
from typing import Any

from grants_shared.adapters import db
from grants_shared.api.route_utils import raise_flask_error
from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from src.constants.lookup_constants import Privilege, ResourceInheritance, ResourceType
from src.db.models.grantor_organization_models import GrantorOrganization, Partner, Program
from src.db.models.resource_models import (
    AbstractResourceTableMixin,
    InternalResource,
    LinkRolePrivilege,
    ResourceUser,
    ResourceUserRole,
    Role,
)
from src.db.models.user_models import User

logger = logging.getLogger(__name__)


class AuthorizationEnforcer:

    def __init__(self, db_session: db.Session):
        self.db_session = db_session
        self.log_context: dict[str, Any] = {}

    def can_access(
        self,
        user: User,
        required_privileges: Privilege | set[Privilege],
        resource: AbstractResourceTableMixin,
    ) -> bool:
        """
        Check whether a user has the required privilege against the resource.

        This check has 3 core pieces:
        * Determine which resources are relevant to the resource passed in. If a resource
          has inheritance, then we'll grab all the resources that a user could be able to access
          the passed in resource through. Exact inheritance is defined per resource.
        * Determine which roles the user has against the resources determine in step 1.
        * Check whether a user has the required privileges within the roles from step 2.
          If multiple required privileges are passed in, the user does not need every
          privilege to come from the same role.

        """
        # In the event there are any unexpected, we want to get as much context as possible for what errored
        # so attach the log context we've been building up to the error message and re-raise
        try:
            return self._can_access(
                user=user, required_privileges=required_privileges, resource=resource
            )
        except Exception:
            logger.exception("Failed to run authZ checks", extra=self.log_context)
            raise

    def _can_access(
        self,
        user: User,
        required_privileges: Privilege | set[Privilege],
        resource: AbstractResourceTableMixin,
    ) -> bool:
        """Internal implementation of can_access, call that function directly instead."""
        if isinstance(required_privileges, Privilege):
            required_privileges = {required_privileges}

        self.log_context |= {
            "user_id": user.user_id,
            "resource_type": resource.get_resource_type(),
            "required_privileges": "|".join(required_privileges),
        }

        roles = self.get_user_roles_for_resource(user=user, resource=resource)
        # Flip the roles around into a privilege -> role map
        # This way we both have a convenient set of all privileges a user
        # has for the resource, but also can easily see which roles granted them
        # those privileges.
        privilege_to_role: dict[Privilege, list[Role]] = defaultdict(list)
        for role in roles:
            for privilege in role.privileges:
                privilege_to_role[privilege].append(role)

        # Check whether a user has every required privilege in the relevant roles
        # If they have all of them, then they can the resource for that privilege.
        missing_privileges = required_privileges - privilege_to_role.keys()
        if missing_privileges:
            access_granted = False
        else:
            access_granted = True

            # For logging, grab all role IDs/names that were involved in authorizing
            authorizing_role_ids = set()
            authorizing_role_names = set()
            for privilege in required_privileges:
                authorizing_roles = privilege_to_role.get(privilege, [])
                for authorizing_role in authorizing_roles:
                    authorizing_role_ids.add(str(authorizing_role.role_id))
                    authorizing_role_names.add(authorizing_role.role_name)

            self.log_context["authorizing_role_ids"] = "|".join(authorizing_role_ids)
            self.log_context["authorizing_role_names"] = "|".join(authorizing_role_names)

        self.log_context |= {"access_granted": access_granted}
        logger.info("Completed authZ check for user", extra=self.log_context)

        return access_granted

    def verify_access(
        self,
        user: User,
        required_privileges: Privilege | set[Privilege],
        resource: AbstractResourceTableMixin,
    ) -> None:
        """Wrapper function around can_access that handles raising a 403 if the user does not have access."""
        if not self.can_access(
            user=user, required_privileges=required_privileges, resource=resource
        ):
            raise_flask_error(403, "Forbidden")

    def get_user_roles_for_resource(
        self, user: User, resource: AbstractResourceTableMixin
    ) -> list[Role]:
        """
        Get all roles of the given user that are relevant to the resource.

        Depending on what resources are relevant to the passed in resource, this may
        be roles against several resources.

        For example, if having a role against a parent resource should allow access
        to the passed in resource, both resources will be relevant, and all user roles against
        both would be returned.
        """

        # Fetch the relevant resources
        resources = self._get_relevant_resources(resource)

        resource_ids = []

        relevant_resource_map: dict[ResourceType, list[str]] = defaultdict(list)
        for resource in resources:
            resource_ids.append(resource.get_resource_id())
            relevant_resource_map[resource.get_resource_type()].append(
                str(resource.get_resource_id())
            )

        # Add every resource ID we fetched to the log context
        # This'll end up like
        # {"relevant_subagency_ids": "uuid0", "relevant_team_ids": "uuid1|uuid2|uuid3"}
        for k, v in relevant_resource_map.items():
            self.log_context[f"relevant_{k}_ids"] = "|".join(v)

        # Grab all resource user connections where either one of the above resources
        # is present AND the user is the one with that role.
        stmt = select(ResourceUser).where(
            ResourceUser.resource_id.in_(resource_ids),
            ResourceUser.user_id == user.user_id,
        )

        resource_users = self.db_session.execute(stmt).scalars()

        roles = []
        for resource_user in resource_users:
            roles.extend(resource_user.roles)

        self.log_context["relevant_role_count"] = len(roles)
        return roles

    def _get_relevant_resources(
        self, resource: AbstractResourceTableMixin
    ) -> list[AbstractResourceTableMixin]:
        """
        Get all relevant resources for checking whether a user can access the provided resource.

        This factors in any inheritance that a particular type may need to consider. See the
        corresponding _get_resource_for_X function for further details on what resources are
        considered relevant.
        """

        if isinstance(resource, Partner):
            return self._get_resources_for_partner(resource)

        if isinstance(resource, GrantorOrganization):
            return self._get_resources_for_grantor_organization(resource)

        if isinstance(resource, Program):
            return self._get_resources_for_program(resource)

        if isinstance(resource, InternalResource):
            return self._get_resources_for_internal_resource(resource)

        error_message = f"No configuration found for determining relevant resources for type {resource.__class__.__name__}"
        raise NotImplementedError(error_message)

    def _get_resources_for_partner(self, partner: Partner) -> list[AbstractResourceTableMixin]:
        """Get all relevant resources for a partner - which is just the partner itself"""
        return [partner]

    def _get_resources_for_grantor_organization(
        self, grantor_organization: GrantorOrganization, fetch_partner: bool = True
    ) -> list[AbstractResourceTableMixin]:
        """
        Get all relevant resources for a grantor organization, which consists of:

        * The grantor organization itself
        * Any parent organizations (recursively up the hierarchy)
        * The partner that owns the organization

        Since all organizations in a hierarchy will have the same partner, we can ignore the partner
        attached to parent organizations.
        """
        resources: list[AbstractResourceTableMixin] = [grantor_organization]

        if fetch_partner:
            resources += self._get_resources_for_partner(grantor_organization.partner)

        if grantor_organization.parent_organization is not None:
            resources += self._get_resources_for_grantor_organization(
                grantor_organization.parent_organization, fetch_partner=False
            )

        return resources

    def _get_resources_for_program(self, program: Program) -> list[AbstractResourceTableMixin]:
        """
        Get all relevant resources for a program, which consists of:

        * The partner it belongs to
        * The grant office (recursively up the hierarchy)
        * The program office (recursively up the hierarchy)
        * Any secondary partners

        NOTE: that at this time users are not attached to the program despite it being a resource,
        so we do not add the program to this list.
        """

        resources: list[AbstractResourceTableMixin] = (
            self._get_resources_for_partner(program.partner)
            + self._get_resources_for_grantor_organization(
                program.grant_office, fetch_partner=False
            )
            + self._get_resources_for_grantor_organization(
                program.program_office, fetch_partner=False
            )
        )

        for secondary_partner in program.secondary_program_partners:
            resources += self._get_resources_for_partner(secondary_partner)

        return resources

    def _get_resources_for_internal_resource(
        self, internal_resource: InternalResource
    ) -> list[AbstractResourceTableMixin]:
        """
        Get all relevant resources for an internal resource - which is just the internal resource itself
        """
        return [internal_resource]

    ####################################
    # Looking up users for a resource
    #
    # The inverse of can_access: instead of asking whether one user may reach a
    # resource, these ask which users hold a privilege on it.
    ####################################

    def get_resources_for_user_lookup(
        self, resource: AbstractResourceTableMixin, inheritance: ResourceInheritance
    ) -> list[AbstractResourceTableMixin]:
        """Get the resources a user lookup against this resource should consider.

        Under FULL, this is the same parent-chain walk can_access uses, so the answer
        stays consistent with what the enforcer would actually allow.

        Under DIRECT it's normally just the resource itself. A program is the exception:
        users are never attached to program resources (see _get_resources_for_program),
        so a literal direct lookup on one would always come back empty. For a program,
        DIRECT means the offices immediately responsible for it - its program office and
        grant office.
        """
        if inheritance == ResourceInheritance.FULL:
            return self._get_relevant_resources(resource)

        if isinstance(resource, Program):
            return [resource.program_office, resource.grant_office]

        return [resource]

    def get_users_for_resource_query(
        self,
        resources: list[AbstractResourceTableMixin],
        required_privileges: set[Privilege] | None = None,
    ) -> Select:
        """Build the query for users holding roles on any of the given resources.

        Takes resources rather than their IDs on purpose. Which resources to search is
        a decision get_resources_for_user_lookup makes - notably, a program has to be
        widened to its offices because no user is ever attached to a program directly.
        Requiring the objects means a caller holding only an ID (a workflow's
        resource_id, say) has to go through that resolution rather than passing the
        raw ID here and silently matching nobody.

        Returns the statement rather than the rows so callers can add their own sorting,
        pagination, and filters - the endpoint paginates, the workflow approval emails
        want every recipient. A caller that needs to sort or filter on the user's email
        has to join LinkExternalUser itself, since the email lives there rather than
        on User. The link is eager-loaded either way so reading ``user.email`` off
        the results doesn't fire a query per user.

        Note that users without a login.gov link are included, with a null email -
        callers that need an address filter them out.

        A user must hold EVERY required privilege, though not necessarily all from the
        same role, matching how can_access treats a privilege set. Passing no privileges
        matches any user with a role on one of the resources.
        """
        resource_ids = [resource.get_resource_id() for resource in resources]

        stmt = select(User).options(selectinload(User.linked_login_gov_external_user))

        has_role_on_resource = (
            select(1)
            .select_from(ResourceUser)
            .join(
                ResourceUserRole,
                ResourceUserRole.resource_user_id == ResourceUser.resource_user_id,
            )
            .where(
                ResourceUser.user_id == User.user_id,
                ResourceUser.resource_id.in_(resource_ids),
            )
            .exists()
        )
        stmt = stmt.where(has_role_on_resource)

        if required_privileges:
            # Count the DISTINCT required privileges the user holds across every role
            # they have on these resources. Distinct is what makes holding the same
            # privilege via two roles count once rather than satisfying the check twice.
            held_required_privilege_count = (
                select(func.count(func.distinct(LinkRolePrivilege.privilege)))
                .select_from(ResourceUser)
                .join(
                    ResourceUserRole,
                    ResourceUserRole.resource_user_id == ResourceUser.resource_user_id,
                )
                .join(
                    LinkRolePrivilege,
                    LinkRolePrivilege.role_id == ResourceUserRole.role_id,
                )
                .where(
                    ResourceUser.user_id == User.user_id,
                    ResourceUser.resource_id.in_(resource_ids),
                    LinkRolePrivilege.privilege.in_(required_privileges),
                )
                .scalar_subquery()
            )
            stmt = stmt.where(held_required_privilege_count == len(required_privileges))

        return stmt

    def get_users_for_resource(
        self,
        resource: AbstractResourceTableMixin,
        inheritance: ResourceInheritance = ResourceInheritance.DIRECT,
        required_privileges: set[Privilege] | None = None,
    ) -> list[User]:
        """Get every user holding the required privileges on a resource.

        The convenience wrapper over get_users_for_resource_query for callers that want
        all the rows and no pagination.
        """
        resources = self.get_resources_for_user_lookup(resource, inheritance)
        stmt = self.get_users_for_resource_query(resources, required_privileges=required_privileges)

        return list(self.db_session.execute(stmt).scalars())

    def get_roles_by_user_for_resources(
        self, user_ids: list[uuid.UUID], resource_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[tuple[uuid.UUID, Role]]]:
        """Get each user's roles on the given resources, keyed by user ID.

        Each entry pairs the resource that granted the role with the role itself, since
        the same role can be granted on more than one resource in a hierarchy and
        callers need to report which one it came from.
        """
        resource_users = self.db_session.execute(
            select(ResourceUser).where(
                ResourceUser.user_id.in_(user_ids),
                ResourceUser.resource_id.in_(resource_ids),
            )
        ).scalars()

        roles_by_user: dict[uuid.UUID, list[tuple[uuid.UUID, Role]]] = defaultdict(list)
        for resource_user in resource_users:
            for role in resource_user.roles:
                roles_by_user[resource_user.user_id].append((resource_user.resource_id, role))

        return dict(roles_by_user)
