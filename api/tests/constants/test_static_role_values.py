from src.constants.static_role_values import CORE_ROLES

# The privileges each core role is expected to grant, keyed by role name.
EXPECTED_ROLE_PRIVILEGES = {}

EXPECTED_ROLE_RESOURCE_TYPES = {}


def test_core_roles_defines_exactly_seven_roles():
    assert len(CORE_ROLES) == 0
    assert {role.role_name for role in CORE_ROLES} == set(EXPECTED_ROLE_PRIVILEGES.keys())


def test_core_roles_have_expected_privileges_and_resource_types():
    for role in CORE_ROLES:
        assert role.is_core is True
        assert set(role.privileges) == EXPECTED_ROLE_PRIVILEGES[role.role_name]
        assert set(role.resource_types) == EXPECTED_ROLE_RESOURCE_TYPES[role.role_name]


def test_core_roles_have_unique_ids():
    role_ids = [role.mgmt_role_id for role in CORE_ROLES]
    assert len(role_ids) == len(set(role_ids))
