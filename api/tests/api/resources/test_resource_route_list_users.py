import uuid

import pytest

from src.auth.api_jwt_auth import create_jwt_for_user
from src.constants.lookup_constants import Privilege, ResourceInheritance, ResourceType
from tests.db.models.factories import (
    GrantorOrganizationFactory,
    LinkExternalUserFactory,
    PartnerFactory,
    ProgramFactory,
    UserFactory,
)
from tests.test_utils.auth_test_utils import setup_user_with_roles

#################################
#
# Tests for POST /v1/resources/<resource_type>/<resource_id>/users/list
#
# The inheritance and privilege semantics are pinned in
# tests/auth/test_authorization_enforcer.py - these cover the endpoint: auth, the
# request schema, the response shape, and pagination.
#
#################################


DEFAULT_PAGINATION = {
    "page_offset": 1,
    "page_size": 25,
    "sort_order": [{"order_by": "user_id", "sort_direction": "ascending"}],
}


@pytest.fixture
def partner(enable_factory_create):
    return PartnerFactory.create(partner_name="Test Partner")


@pytest.fixture
def organization(partner):
    return GrantorOrganizationFactory.create(organization_name="Test Office", partner=partner)


@pytest.fixture
def viewer_token(db_session, partner):
    """A user who may list users on the partner and anything beneath it.

    Which privilege the endpoint requires depends on the resource type being listed, so
    this holds all three view privileges. They're granted at the partner level, which
    means this user shows up in `full` inheritance results for resources below the
    partner but never in `direct` ones.
    """
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


def post_list(client, resource_type, resource_id, token=None, body=None):
    payload = {"pagination": DEFAULT_PAGINATION}
    if body is not None:
        payload = {**payload, **body}

    headers = {"X-MGMT-Token": token} if token else {}
    return client.post(
        f"/v1/resources/{resource_type}/{resource_id}/users/list", json=payload, headers=headers
    )


####################################
# Happy Path
####################################


def test_list_users_for_partner_200(client, db_session, partner, viewer_token):
    """The response reports each user with the roles granting them access."""
    user = setup_user_with_roles(
        db_session, resources=[partner], privileges=[Privilege.UPDATE_PARTNER]
    )
    LinkExternalUserFactory.create(user=user, email="grantee@example.com")
    db_session.commit()

    response = post_list(client, ResourceType.PARTNER, partner.partner_id, viewer_token)

    assert response.status_code == 200
    entry = next(row for row in response.json["data"] if row["user_id"] == str(user.user_id))
    assert entry["email"] == "grantee@example.com"
    assert len(entry["roles"]) == 1

    role = entry["roles"][0]
    assert role["privileges"] == [Privilege.UPDATE_PARTNER]
    assert role["resource_type"] == ResourceType.PARTNER
    assert role["resource"]["resource_id"] == str(partner.partner_id)
    assert role["resource"]["resource_name"] == "Test Partner"


def test_list_users_reports_null_email_for_user_without_login(
    client, db_session, partner, viewer_token
):
    """A user with no login.gov link still appears, with a null email."""
    user = UserFactory.create(linked_login_gov_external_user=None)
    setup_user_with_roles(
        db_session, resources=[partner], user=user, privileges=[Privilege.UPDATE_PARTNER]
    )
    db_session.commit()

    response = post_list(client, ResourceType.PARTNER, partner.partner_id, viewer_token)

    assert response.status_code == 200
    entry = next(row for row in response.json["data"] if row["user_id"] == str(user.user_id))
    assert entry["email"] is None


def test_list_users_privilege_filter_200(client, db_session, partner, viewer_token):
    """The privilege filter narrows the result to holders of that privilege."""
    wanted = setup_user_with_roles(
        db_session, resources=[partner], privileges=[Privilege.MANAGE_PARTNER_MEMBERS]
    )
    db_session.commit()

    response = post_list(
        client,
        ResourceType.PARTNER,
        partner.partner_id,
        viewer_token,
        {"filters": {"privilege": {"one_of": [Privilege.MANAGE_PARTNER_MEMBERS]}}},
    )

    assert response.status_code == 200
    assert [row["user_id"] for row in response.json["data"]] == [str(wanted.user_id)]


def test_list_users_inheritance_filter_200(client, db_session, partner, organization, viewer_token):
    """Full inheritance reaches role holders above the resource, direct does not."""
    partner_user = setup_user_with_roles(
        db_session, resources=[partner], privileges=[Privilege.VIEW_GRANTOR_ORGANIZATION]
    )
    org_user = setup_user_with_roles(
        db_session, resources=[organization], privileges=[Privilege.VIEW_GRANTOR_ORGANIZATION]
    )
    db_session.commit()

    direct = post_list(
        client,
        ResourceType.GRANTOR_ORGANIZATION,
        organization.grantor_organization_id,
        viewer_token,
        {"filters": {"inheritance": ResourceInheritance.DIRECT}},
    )
    assert direct.status_code == 200
    assert {row["user_id"] for row in direct.json["data"]} == {str(org_user.user_id)}

    full = post_list(
        client,
        ResourceType.GRANTOR_ORGANIZATION,
        organization.grantor_organization_id,
        viewer_token,
        {"filters": {"inheritance": ResourceInheritance.FULL}},
    )
    assert full.status_code == 200
    assert {row["user_id"] for row in full.json["data"]} >= {
        str(org_user.user_id),
        str(partner_user.user_id),
    }


def test_list_users_for_program_uses_its_offices(client, db_session, partner, viewer_token):
    """Direct on a program finds users on its offices, since none are on the program."""
    program_office = GrantorOrganizationFactory.create(
        organization_name="Program Office", partner=partner
    )
    grant_office = GrantorOrganizationFactory.create(
        organization_name="Grant Office", partner=partner
    )
    program = ProgramFactory.create(
        partner=partner, program_office=program_office, grant_office=grant_office
    )
    office_user = setup_user_with_roles(
        db_session, resources=[program_office], privileges=[Privilege.VIEW_PROGRAM]
    )
    db_session.commit()

    response = post_list(client, ResourceType.PROGRAM, program.program_id, viewer_token)

    assert response.status_code == 200
    assert {row["user_id"] for row in response.json["data"]} == {str(office_user.user_id)}
    assert response.json["data"][0]["roles"][0]["resource"]["resource_name"] == "Program Office"


####################################
# Pagination
####################################


def test_list_users_paginates_over_distinct_users(
    client, db_session, partner, organization, viewer_token
):
    """Page counts are per user, even when a user holds roles on several resources.

    A user with roles both on the partner and on the organization must count once.
    """
    for _ in range(3):
        user = setup_user_with_roles(
            db_session, resources=[partner], privileges=[Privilege.VIEW_PROGRAM]
        )
        setup_user_with_roles(
            db_session,
            resources=[organization],
            user=user,
            privileges=[Privilege.VIEW_PROGRAM],
        )
    db_session.commit()

    response = post_list(
        client,
        ResourceType.GRANTOR_ORGANIZATION,
        organization.grantor_organization_id,
        viewer_token,
        {
            "filters": {"inheritance": ResourceInheritance.FULL},
            "pagination": {**DEFAULT_PAGINATION, "page_size": 2},
        },
    )

    assert response.status_code == 200
    # 3 role-holders plus the viewer fixture's own user, each counted once despite
    # holding two roles apiece
    assert response.json["pagination_info"]["total_records"] == 4
    assert response.json["pagination_info"]["total_pages"] == 2
    assert len(response.json["data"]) == 2

    # Each returned user reports both of their roles
    assert all(len(row["roles"]) in (1, 2) for row in response.json["data"])


def test_list_users_sort_by_email(client, db_session, partner, viewer_token):
    """Sorting by email works even though email lives on the login.gov link table."""
    for email in ["c@example.com", "a@example.com", "b@example.com"]:
        user = setup_user_with_roles(
            db_session, resources=[partner], privileges=[Privilege.UPDATE_PARTNER]
        )
        LinkExternalUserFactory.create(user=user, email=email)
    db_session.commit()

    response = post_list(
        client,
        ResourceType.PARTNER,
        partner.partner_id,
        viewer_token,
        {
            "filters": {"privilege": {"one_of": [Privilege.UPDATE_PARTNER]}},
            "pagination": {
                **DEFAULT_PAGINATION,
                "sort_order": [{"order_by": "email", "sort_direction": "ascending"}],
            },
        },
    )

    assert response.status_code == 200
    assert [row["email"] for row in response.json["data"]] == [
        "a@example.com",
        "b@example.com",
        "c@example.com",
    ]


####################################
# AuthN / AuthZ
####################################


def test_list_users_no_token_401(client, partner):
    response = post_list(client, ResourceType.PARTNER, partner.partner_id)

    assert response.status_code == 401


def test_list_users_without_view_privilege_403(client, db_session, partner):
    """A user who can't view the resource can't list its users."""
    user = setup_user_with_roles(
        db_session, resources=[partner], privileges=[Privilege.MANAGE_PARTNER_MEMBERS]
    )
    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()

    response = post_list(client, ResourceType.PARTNER, partner.partner_id, token)

    assert response.status_code == 403
    assert response.json["message"] == "Forbidden"


####################################
# Not Found / Validation
####################################


def test_list_users_resource_not_found_404(client, viewer_token):
    response = post_list(client, ResourceType.PARTNER, uuid.uuid4(), viewer_token)

    assert response.status_code == 404


def test_list_users_resource_type_mismatch_404(client, partner, viewer_token):
    """A real ID under the wrong type is a 404, not a leak that it exists elsewhere."""
    response = post_list(
        client, ResourceType.GRANTOR_ORGANIZATION, partner.partner_id, viewer_token
    )

    assert response.status_code == 404


def test_list_users_unsupported_resource_type_404(client, db_session, viewer_token):
    """Internal resources are fetchable but this endpoint doesn't list them."""
    response = post_list(client, ResourceType.INTERNAL, uuid.uuid4(), viewer_token)

    assert response.status_code == 404


def test_list_users_unknown_resource_type_in_path_404(client, partner, viewer_token):
    """A path segment that isn't a resource type at all doesn't match the route."""
    response = post_list(client, "not_a_resource_type", partner.partner_id, viewer_token)

    assert response.status_code == 404


def test_list_users_multiple_privileges_requires_all_of_them(
    client, db_session, partner, viewer_token
):
    """More than one privilege is allowed, and a user must hold every one.

    The endpoint originally capped this at one privilege on the assumption the query
    would be awkward; it isn't, so the cap is gone.
    """
    has_both = setup_user_with_roles(
        db_session,
        resources=[partner],
        privileges=[Privilege.UPDATE_PARTNER, Privilege.MANAGE_PARTNER_MEMBERS],
    )
    setup_user_with_roles(db_session, resources=[partner], privileges=[Privilege.UPDATE_PARTNER])
    db_session.commit()

    response = post_list(
        client,
        ResourceType.PARTNER,
        partner.partner_id,
        viewer_token,
        {
            "filters": {
                "privilege": {
                    "one_of": [
                        Privilege.UPDATE_PARTNER,
                        Privilege.MANAGE_PARTNER_MEMBERS,
                    ]
                }
            }
        },
    )

    assert response.status_code == 200
    assert [row["user_id"] for row in response.json["data"]] == [str(has_both.user_id)]


@pytest.mark.parametrize(
    "body,expected_field",
    [
        # Not a real privilege
        ({"filters": {"privilege": {"one_of": ["not_a_privilege"]}}}, "privilege"),
        # Not a real inheritance value
        ({"filters": {"inheritance": "sideways"}}, "inheritance"),
        # Not a sortable field
        (
            {
                "pagination": {
                    **DEFAULT_PAGINATION,
                    "sort_order": [{"order_by": "role_name", "sort_direction": "ascending"}],
                }
            },
            "sort_order",
        ),
    ],
)
def test_list_users_request_validation_422(client, partner, viewer_token, body, expected_field):
    response = post_list(client, ResourceType.PARTNER, partner.partner_id, viewer_token, body)

    assert response.status_code == 422
    assert any(expected_field in error["field"] for error in response.json["errors"])


def test_list_users_pagination_required_422(client, partner, viewer_token):
    response = client.post(
        f"/v1/resources/{ResourceType.PARTNER}/{partner.partner_id}/users/list",
        json={},
        headers={"X-MGMT-Token": viewer_token},
    )

    assert response.status_code == 422
    assert any("pagination" in error["field"] for error in response.json["errors"])
