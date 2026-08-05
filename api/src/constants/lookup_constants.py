from enum import StrEnum


class JobType(StrEnum):
    MIGRATE_UP = "migrate-up"
    MIGRATE_DOWN = "migrate-down"
    MIGRATE_DOWNALL = "migrate-downall"


class MgmtUserType(StrEnum):
    STANDARD = "standard"
    INTERNAL_FRONTEND = "internal_frontend"


class ExternalUserType(StrEnum):
    LOGIN_GOV = "login_gov"


class MgmtPrivilege(StrEnum):
    VIEW_PARTNER = "view_partner"
    UPDATE_PARTNER = "update_partner"
    MANAGE_PARTNER_MEMBERS = "manage_partner_members"

    VIEW_PROGRAM = "view_program"
    UPDATE_PROGRAM = "update_program"
    UNUSED_PRIVILEGE_101 = "unused_privilege_101"

    VIEW_GRANTOR_ORGANIZATION = "view_grantor_organization"
    UPDATE_GRANTOR_ORGANIZATION = "update_grantor_organization"
    MANAGE_GRANTOR_ORGANIZATION_MEMBERS = "manage_grantor_organization_members"
    UNUSED_PRIVILEGE_102 = "unused_privilege_102"
    UNUSED_PRIVILEGE_103 = "unused_privilege_103"


class MgmtResourceType(StrEnum):
    INTERNAL = "internal"
    PARTNER = "partner"
    PROGRAM = "program"
    GRANTOR_ORGANIZATION = "grantor_organization"
    OPPORTUNITY = "opportunity"


# The resource types each privilege is allowed to be assigned at. A privilege may only be
# included in a role when the role's resource types are a subset of the privilege's allowed
# resource types (validated in src/util/role_util.py::build_role). This prevents assigning,
# for example, a department-only privilege on a team-level role.
ALLOWED_RESOURCES_FOR_PRIVILEGE: dict[MgmtPrivilege, set[MgmtResourceType]] = {
    # Partner-level
    MgmtPrivilege.VIEW_PARTNER: {MgmtResourceType.PARTNER},
    MgmtPrivilege.UPDATE_PARTNER: {MgmtResourceType.PARTNER},
    MgmtPrivilege.MANAGE_PARTNER_MEMBERS: {MgmtResourceType.PARTNER},
    # Program-level
    MgmtPrivilege.VIEW_PROGRAM: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
        MgmtResourceType.PROGRAM,
    },
    MgmtPrivilege.UPDATE_PROGRAM: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
        MgmtResourceType.PROGRAM,
    },
    # Grantor organization level
    MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
    },
    MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
    },
    MgmtPrivilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
    },
    MgmtPrivilege.UNUSED_PRIVILEGE_101: set(),
    MgmtPrivilege.UNUSED_PRIVILEGE_102: set(),
    MgmtPrivilege.UNUSED_PRIVILEGE_103: set(),
}
