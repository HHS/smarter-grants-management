import uuid

import pytest
from sqlalchemy import update

from src.auth.api_jwt_auth import create_jwt_for_user
from src.constants.lookup_constants import Privilege, ResourceType
from src.db.models.resource_models import Role
from tests.db.models.factories import (
    GrantorOrganizationFactory,
    PartnerFactory,
    ProgramFactory,
    RoleFactory,
)
from tests.test_utils.auth_test_utils import setup_user_with_roles

#################################
#
# Tests for POST /v1/resources/<resource_type>/<resource_id>/roles/list
#
#################################


DEFAULT_PAGINATION = {
    "page_offset": 1,
    "page_size": 25,
    "sort_order": [{"order_by": "role_name", "sort_direction": "ascending"}],
}


@pytest.fixture(autouse=True)
def clear_core_roles(db_session):
    """Set all existing roles to is_core=False to isolate tests from other test data."""
    db_session.execute(update(Role).values(is_core=False))
    db_session.commit()


@pytest.fixture
def partner(enable_factory_create):
    return PartnerFactory.create(partner_name="Test Partner")


@pytest.fixture
def organization(partner):
    return GrantorOrganizationFactory.create(organization_name="Test Office", partner=partner)


@pytest.fixture
def program(partner, organization):
    return ProgramFactory.create(
        program_name="Test Program", partner=partner, program_office=organization
    )


@pytest.fixture
def viewer_token(db_session, partner):
    """A user who may list roles on the partner and anything beneath it."""
    user = setup_user_with_roles(
        db_session,
        resources=[partner],
        privileges=[
            Privilege.VIEW_PARTNER,
            Privilege.VIEW_GRANTOR_ORGANIZATION,
            Privilege.VIEW_PROGRAM,
        ],
    )
    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()
    return token


@pytest.fixture
def partner_role(enable_factory_create):
    """A core role applicable to partners."""
    return RoleFactory.create(
        role_name="Partner Admin",
        is_core=True,
        resource_types=[ResourceType.PARTNER],
        privileges=[Privilege.VIEW_PARTNER, Privilege.UPDATE_PARTNER],
    )


@pytest.fixture
def org_role(enable_factory_create):
    """A core role applicable to grantor organizations."""
    return RoleFactory.create(
        role_name="Organization Manager",
        is_core=True,
        resource_types=[ResourceType.GRANTOR_ORGANIZATION],
        privileges=[Privilege.VIEW_GRANTOR_ORGANIZATION, Privilege.UPDATE_GRANTOR_ORGANIZATION],
    )


@pytest.fixture
def multi_resource_role(enable_factory_create):
    """A core role applicable to both partners and grantor organizations."""
    return RoleFactory.create(
        role_name="Multi Resource Role",
        is_core=True,
        resource_types=[ResourceType.PARTNER, ResourceType.GRANTOR_ORGANIZATION],
        privileges=[Privilege.VIEW_PARTNER, Privilege.VIEW_GRANTOR_ORGANIZATION],
    )


def post_list(client, resource_type, resource_id, token=None, body=None):
    payload = {"pagination": DEFAULT_PAGINATION}
    if body is not None:
        payload = {**payload, **body}

    headers = {"X-MGMT-Token": token} if token else {}
    return client.post(
        f"/v1/resources/{resource_type}/{resource_id}/roles/list", json=payload, headers=headers
    )


####################################
# Happy Path
####################################


def test_list_roles_for_partner_200(client, db_session, partner, viewer_token, partner_role):
    """The response reports core roles applicable to the partner resource type."""
    response = post_list(client, ResourceType.PARTNER, partner.partner_id, viewer_token)

    assert response.status_code == 200
    assert response.json["message"] == "Success"

    data = response.json["data"]
    assert len(data) == 1

    role = data[0]
    assert role["role_id"] == str(partner_role.role_id)
    assert role["role_name"] == "Partner Admin"
    assert set(role["privileges"]) == {Privilege.VIEW_PARTNER, Privilege.UPDATE_PARTNER}


def test_list_roles_for_organization_200(client, db_session, organization, viewer_token, org_role):
    """The response reports core roles applicable to the grantor organization resource type."""
    response = post_list(
        client,
        ResourceType.GRANTOR_ORGANIZATION,
        organization.grantor_organization_id,
        viewer_token,
    )

    assert response.status_code == 200

    data = response.json["data"]
    assert len(data) == 1

    role = data[0]
    assert role["role_id"] == str(org_role.role_id)
    assert role["role_name"] == "Organization Manager"
    assert set(role["privileges"]) == {
        Privilege.VIEW_GRANTOR_ORGANIZATION,
        Privilege.UPDATE_GRANTOR_ORGANIZATION,
    }


def test_list_roles_for_program_returns_empty_200(client, db_session, program, viewer_token):
    """Programs return an empty list since users cannot be assigned directly to programs."""
    response = post_list(client, ResourceType.PROGRAM, program.program_id, viewer_token)

    assert response.status_code == 200
    assert response.json["data"] == []
    assert response.json["pagination_info"]["total_records"] == 0
    assert response.json["pagination_info"]["total_pages"] == 0


def test_list_roles_includes_multi_resource_roles_200(
    client, db_session, partner, viewer_token, partner_role, multi_resource_role
):
    """Roles applicable to multiple resource types are included when they match the requested type."""
    response = post_list(client, ResourceType.PARTNER, partner.partner_id, viewer_token)

    assert response.status_code == 200

    data = response.json["data"]
    assert len(data) == 2

    role_names = {role["role_name"] for role in data}
    assert role_names == {"Partner Admin", "Multi Resource Role"}


def test_list_roles_excludes_non_core_roles_200(
    client, db_session, partner, viewer_token, partner_role, enable_factory_create
):
    """Non-core roles are not included in the response."""
    non_core_role = RoleFactory.create(
        role_name="Non-Core Role",
        is_core=False,
        resource_types=[ResourceType.PARTNER],
        privileges=[Privilege.VIEW_PARTNER],
    )

    response = post_list(client, ResourceType.PARTNER, partner.partner_id, viewer_token)

    assert response.status_code == 200

    data = response.json["data"]
    role_ids = {role["role_id"] for role in data}

    assert str(partner_role.role_id) in role_ids
    assert str(non_core_role.role_id) not in role_ids


def test_list_roles_excludes_wrong_resource_type_200(
    client, db_session, partner, viewer_token, partner_role, org_role
):
    """Roles for other resource types are not included."""
    response = post_list(client, ResourceType.PARTNER, partner.partner_id, viewer_token)

    assert response.status_code == 200

    data = response.json["data"]
    role_ids = {role["role_id"] for role in data}

    assert str(partner_role.role_id) in role_ids
    assert str(org_role.role_id) not in role_ids


####################################
# Pagination
####################################


def test_list_roles_pagination_200(client, db_session, partner, enable_factory_create):
    """Pagination works correctly with page size and offset."""
    # Create viewer user and token
    user = setup_user_with_roles(
        db_session,
        resources=[partner],
        privileges=[
            Privilege.VIEW_PARTNER,
            Privilege.VIEW_GRANTOR_ORGANIZATION,
            Privilege.VIEW_PROGRAM,
        ],
    )

    for i in range(5):
        RoleFactory.create(
            role_name=f"Role {i:02d}",
            is_core=True,
            resource_types=[ResourceType.PARTNER],
            privileges=[Privilege.VIEW_PARTNER],
        )

    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()

    response = post_list(
        client,
        ResourceType.PARTNER,
        partner.partner_id,
        token,
        body={
            "pagination": {
                "page_offset": 1,
                "page_size": 2,
                "sort_order": [{"order_by": "role_name", "sort_direction": "ascending"}],
            }
        },
    )

    assert response.status_code == 200
    assert len(response.json["data"]) == 2
    assert response.json["pagination_info"]["total_records"] == 5
    assert response.json["pagination_info"]["total_pages"] == 3
    assert response.json["pagination_info"]["page_offset"] == 1
    assert response.json["pagination_info"]["page_size"] == 2

    first_page_names = [role["role_name"] for role in response.json["data"]]

    response = post_list(
        client,
        ResourceType.PARTNER,
        partner.partner_id,
        token,
        body={
            "pagination": {
                "page_offset": 2,
                "page_size": 2,
                "sort_order": [{"order_by": "role_name", "sort_direction": "ascending"}],
            }
        },
    )

    assert response.status_code == 200
    assert len(response.json["data"]) == 2

    second_page_names = [role["role_name"] for role in response.json["data"]]

    assert first_page_names != second_page_names


def test_list_roles_sorting_by_name_200(
    client, db_session, partner, viewer_token, enable_factory_create
):
    """Sorting by role_name works in both directions."""
    RoleFactory.create(
        role_name="Alpha Role",
        is_core=True,
        resource_types=[ResourceType.PARTNER],
        privileges=[Privilege.VIEW_PARTNER],
    )
    RoleFactory.create(
        role_name="Zeta Role",
        is_core=True,
        resource_types=[ResourceType.PARTNER],
        privileges=[Privilege.VIEW_PARTNER],
    )

    db_session.commit()

    response = post_list(
        client,
        ResourceType.PARTNER,
        partner.partner_id,
        viewer_token,
        body={
            "pagination": {
                "page_offset": 1,
                "page_size": 25,
                "sort_order": [{"order_by": "role_name", "sort_direction": "ascending"}],
            }
        },
    )

    assert response.status_code == 200
    names = [role["role_name"] for role in response.json["data"]]
    assert names == sorted(names)
    assert names[0] == "Alpha Role"

    response = post_list(
        client,
        ResourceType.PARTNER,
        partner.partner_id,
        viewer_token,
        body={
            "pagination": {
                "page_offset": 1,
                "page_size": 25,
                "sort_order": [{"order_by": "role_name", "sort_direction": "descending"}],
            }
        },
    )

    assert response.status_code == 200
    names = [role["role_name"] for role in response.json["data"]]
    assert names == sorted(names, reverse=True)
    assert names[0] == "Zeta Role"


def test_list_roles_sorting_by_id_200(
    client, db_session, partner, viewer_token, enable_factory_create
):
    """Sorting by role_id works correctly."""
    role1 = RoleFactory.create(
        role_name="Role 1",
        is_core=True,
        resource_types=[ResourceType.PARTNER],
        privileges=[Privilege.VIEW_PARTNER],
    )
    role2 = RoleFactory.create(
        role_name="Role 2",
        is_core=True,
        resource_types=[ResourceType.PARTNER],
        privileges=[Privilege.VIEW_PARTNER],
    )

    db_session.commit()

    response = post_list(
        client,
        ResourceType.PARTNER,
        partner.partner_id,
        viewer_token,
        body={
            "pagination": {
                "page_offset": 1,
                "page_size": 25,
                "sort_order": [{"order_by": "role_id", "sort_direction": "ascending"}],
            }
        },
    )

    assert response.status_code == 200
    ids = [uuid.UUID(role["role_id"]) for role in response.json["data"]]
    # Verify the IDs are in ascending order
    assert ids[0] == min(role1.role_id, role2.role_id)
    assert ids[1] == max(role1.role_id, role2.role_id)


####################################
# Authorization
####################################


def test_list_roles_requires_auth_401(client, partner):
    """Request without auth token returns 401."""
    response = post_list(client, ResourceType.PARTNER, partner.partner_id, token=None)
    assert response.status_code == 401


def test_list_roles_requires_view_privilege_403(client, db_session, partner):
    """User without view privilege on the resource gets 403."""
    user = setup_user_with_roles(
        db_session,
        resources=[partner],
        privileges=[Privilege.UPDATE_PARTNER],
    )
    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()

    response = post_list(client, ResourceType.PARTNER, partner.partner_id, token)
    assert response.status_code == 403


def test_list_roles_for_nonexistent_resource_404(client, viewer_token):
    """Request for a non-existent resource returns 404."""
    fake_partner_id = uuid.uuid4()
    response = post_list(client, ResourceType.PARTNER, fake_partner_id, viewer_token)
    assert response.status_code == 404


####################################
# Request Validation
####################################


def test_list_roles_requires_pagination_422(client, partner, viewer_token):
    """Request without pagination returns 422."""
    headers = {"X-MGMT-Token": viewer_token}
    response = client.post(
        f"/v1/resources/{ResourceType.PARTNER}/{partner.partner_id}/roles/list",
        json={},
        headers=headers,
    )
    assert response.status_code == 422


def test_list_roles_invalid_sort_field_422(client, partner, viewer_token):
    """Request with invalid sort field (resource_id as sorting field) returns 422."""
    response = post_list(
        client,
        ResourceType.PARTNER,
        partner.partner_id,
        viewer_token,
        body={
            "pagination": {
                "page_offset": 1,
                "page_size": 25,
                "sort_order": [{"order_by": "resource_id", "sort_direction": "ascending"}],
            }
        },
    )
    assert response.status_code == 422
