import uuid

import pytest

from src.constants.lookup_constants import (
    ALLOWED_RESOURCES_FOR_PRIVILEGE,
    MgmtPrivilege,
    MgmtResourceType,
)
from src.util.role_util import build_role


def test_allowed_resources_for_privilege_is_complete():
    # Every privilege must be mapped so build_role can validate it.
    assert set(ALLOWED_RESOURCES_FOR_PRIVILEGE.keys()) == set(
        MgmtPrivilege
    ), f"Privileges not defined in ALLOWED_RESOURCES_FOR_PRIVILEGE: {', '.join(set(MgmtPrivilege) - set(ALLOWED_RESOURCES_FOR_PRIVILEGE.keys()))}"


def test_build_role_sets_privileges_and_resource_types():
    role_id = uuid.uuid4()
    role = build_role(
        role_id=role_id,
        role_name="Test Partner Role",
        privileges={MgmtPrivilege.VIEW_PARTNER, MgmtPrivilege.UPDATE_PARTNER},
        resource_types={MgmtResourceType.PARTNER},
    )

    assert role.mgmt_role_id == role_id
    assert role.role_name == "Test Partner Role"
    assert role.is_core is True
    assert set(role.privileges) == {MgmtPrivilege.VIEW_PARTNER, MgmtPrivilege.UPDATE_PARTNER}
    assert set(role.resource_types) == {MgmtResourceType.PARTNER}
    # Every link row is stamped with the role id so the merge-based sync persists them.
    assert all(link.mgmt_role_id == role_id for link in role.link_privileges)
    assert all(link.mgmt_role_id == role_id for link in role.link_role_resource_types)


def test_build_role_rejects_privilege_not_allowed_for_resource_type():
    # view_partner is only allowed at the partner level, so it cannot
    # be assigned to an organization-level role.
    with pytest.raises(ValueError, match="view_partner"):
        build_role(
            role_id=uuid.uuid4(),
            role_name="Bad Organization Role",
            privileges={MgmtPrivilege.VIEW_PARTNER},
            resource_types={MgmtResourceType.GRANTOR_ORGANIZATION},
        )


def test_build_role_rejects_privilege_missing_from_mapping(monkeypatch):
    monkeypatch.delitem(ALLOWED_RESOURCES_FOR_PRIVILEGE, MgmtPrivilege.VIEW_PARTNER)

    with pytest.raises(ValueError, match="missing from ALLOWED_RESOURCES_FOR_PRIVILEGE"):
        build_role(
            role_id=uuid.uuid4(),
            role_name="Missing Mapping Role",
            privileges={MgmtPrivilege.VIEW_PARTNER},
            resource_types={MgmtResourceType.PARTNER},
        )
