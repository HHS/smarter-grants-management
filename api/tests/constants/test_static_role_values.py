from src.constants.lookup_constants import Privilege, ResourceType
from src.constants.static_role_values import CORE_ROLES

# The privileges each core role is expected to grant, keyed by role name.
EXPECTED_ROLE_PRIVILEGES = {
    "Partner Admin": {
        Privilege.VIEW_PARTNER,
        Privilege.MANAGE_PARTNER_MEMBERS,
        Privilege.UPDATE_PARTNER,
        Privilege.VIEW_PROGRAM,
        Privilege.UPDATE_PROGRAM,
        Privilege.VIEW_GRANTOR_ORGANIZATION,
        Privilege.UPDATE_GRANTOR_ORGANIZATION,
        Privilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS,
    },
    "Partner Viewer": {
        Privilege.VIEW_PARTNER,
        Privilege.VIEW_PROGRAM,
        Privilege.VIEW_GRANTOR_ORGANIZATION,
    },
    "Grantor Organization Admin": {
        Privilege.VIEW_PROGRAM,
        Privilege.UPDATE_PROGRAM,
        Privilege.VIEW_GRANTOR_ORGANIZATION,
        Privilege.UPDATE_GRANTOR_ORGANIZATION,
        Privilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS,
    },
    "Organization Viewer": {
        Privilege.VIEW_PROGRAM,
        Privilege.VIEW_GRANTOR_ORGANIZATION,
    },
}

EXPECTED_ROLE_RESOURCE_TYPES = {
    "Partner Admin": {ResourceType.PARTNER},
    "Partner Viewer": {ResourceType.PARTNER},
    "Grantor Organization Admin": {ResourceType.GRANTOR_ORGANIZATION},
    "Organization Viewer": {ResourceType.GRANTOR_ORGANIZATION},
}


def test_core_roles_defines_exactly_four_roles():
    assert len(CORE_ROLES) == 4
    assert {role.role_name for role in CORE_ROLES} == set(EXPECTED_ROLE_PRIVILEGES.keys())


def test_core_roles_have_expected_privileges_and_resource_types():
    for role in CORE_ROLES:
        assert role.is_core is True
        assert set(role.privileges) == EXPECTED_ROLE_PRIVILEGES[role.role_name]
        assert set(role.resource_types) == EXPECTED_ROLE_RESOURCE_TYPES[role.role_name]


def test_core_roles_have_unique_ids():
    role_ids = [role.role_id for role in CORE_ROLES]
    assert len(role_ids) == len(set(role_ids))
