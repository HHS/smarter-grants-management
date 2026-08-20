import uuid

import pytest

from src.auth.api_jwt_auth import create_jwt_for_user
from src.constants.lookup_constants import Privilege, ResourceType
from tests.db.models.factories import (
    GrantorOrganizationFactory,
    InternalResourceFactory,
    PartnerFactory,
    ProgramFactory,
    UserApiKeyFactory,
    UserFactory,
)
from tests.test_utils.auth_test_utils import setup_user_with_roles


@pytest.fixture
def user_and_token(enable_factory_create, db_session, app):
    """Create a user and a valid JWT token for them."""
    user = UserFactory.create()
    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()
    return user, token


def _post(client, user_id, token, resource_type, resource_id, privileges):
    return client.post(
        f"v1/users/{user_id}/can_access",
        headers={"X-MGMT-Token": token},
        json={
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "privileges": privileges,
        },
    )


def test_can_access_multiple_privileges_requires_all_403(user_and_token, client, db_session):
    """When multiple privileges are requested, the user must have all of them."""
    user, token = user_and_token
    internal_resource = InternalResourceFactory.create()
    setup_user_with_roles(
        db_session, [internal_resource], user=user, privileges=[Privilege.VIEW_PARTNER]
    )

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.INTERNAL,
        internal_resource.internal_resource_id,
        [Privilege.VIEW_PARTNER, Privilege.VIEW_PROGRAM],
    )

    assert resp.status_code == 403


def test_can_access_missing_privilege_403(user_and_token, client, db_session):
    user, token = user_and_token
    internal_resource = InternalResourceFactory.create()
    setup_user_with_roles(
        db_session, [internal_resource], user=user, privileges=[Privilege.VIEW_PARTNER]
    )

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.INTERNAL,
        internal_resource.internal_resource_id,
        [Privilege.UPDATE_PARTNER],
    )

    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Forbidden"


def test_can_access_no_roles_403(user_and_token, client, db_session):
    """A user with no roles at all against the resource is denied."""
    user, token = user_and_token
    internal_resource = InternalResourceFactory.create()

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.INTERNAL,
        internal_resource.internal_resource_id,
        [Privilege.VIEW_PARTNER],
    )

    assert resp.status_code == 403


def test_can_access_other_user_403(user_and_token, client, db_session):
    """A user may only check access for their own user ID."""
    user, token = user_and_token
    internal_resource = InternalResourceFactory.create()
    setup_user_with_roles(
        db_session, [internal_resource], user=user, privileges=[Privilege.VIEW_PARTNER]
    )

    other_user_id = uuid.uuid4()
    resp = _post(
        client,
        other_user_id,
        token,
        ResourceType.INTERNAL,
        internal_resource.internal_resource_id,
        [Privilege.VIEW_PARTNER],
    )

    assert resp.status_code == 403


def test_can_access_resource_not_found_404(user_and_token, client):
    user, token = user_and_token

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.INTERNAL,
        uuid.uuid4(),
        [Privilege.VIEW_PARTNER],
    )

    assert resp.status_code == 404


def test_can_access_unsupported_resource_type_404(user_and_token, client):
    """Resource types without a getter (e.g. opportunity) are not supported yet."""
    user, token = user_and_token

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.OPPORTUNITY,
        uuid.uuid4(),
        [Privilege.VIEW_PARTNER],
    )

    assert resp.status_code == 404


def test_can_access_internal_resource_type_200(user_and_token, client, db_session):
    user, token = user_and_token
    internal_resource = InternalResourceFactory.create()
    setup_user_with_roles(
        db_session, [internal_resource], user=user, privileges=[Privilege.VIEW_PARTNER]
    )

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.INTERNAL,
        internal_resource.internal_resource_id,
        [Privilege.VIEW_PARTNER],
    )

    assert resp.status_code == 200


def test_can_access_empty_privileges_422(user_and_token, client, db_session):
    user, token = user_and_token
    internal_resource = InternalResourceFactory.create()

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.INTERNAL,
        internal_resource.internal_resource_id,
        [],
    )

    assert resp.status_code == 422


def test_can_access_via_api_key_200(enable_factory_create, client, db_session):
    """The endpoint also authenticates via an API key (X-API-Key)."""
    api_key = UserApiKeyFactory.create(is_active=True)
    internal_resource = InternalResourceFactory.create()
    setup_user_with_roles(
        db_session,
        [internal_resource],
        user=api_key.user,
        privileges=[Privilege.VIEW_PARTNER],
    )

    resp = client.post(
        f"v1/users/{api_key.user_id}/can_access",
        headers={"X-API-Key": api_key.key_id},
        json={
            "resource_type": ResourceType.INTERNAL,
            "resource_id": str(internal_resource.internal_resource_id),
            "privileges": [Privilege.VIEW_PARTNER],
        },
    )

    assert resp.status_code == 200


def test_can_access_no_token_401(client):
    resp = client.post(
        f"v1/users/{uuid.uuid4()}/can_access",
        json={
            "resource_type": ResourceType.INTERNAL,
            "resource_id": str(uuid.uuid4()),
            "privileges": [Privilege.VIEW_PARTNER],
        },
    )

    assert resp.status_code == 401


def test_can_access_partner_resource_type_200(user_and_token, client, db_session):
    """Test that a user with proper privileges can access a Partner resource."""
    user, token = user_and_token
    partner = PartnerFactory.create()
    setup_user_with_roles(db_session, [partner], user=user, privileges=[Privilege.VIEW_PARTNER])

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.PARTNER,
        partner.partner_id,
        [Privilege.VIEW_PARTNER],
    )

    assert resp.status_code == 200


def test_can_access_program_resource_type_200(user_and_token, client, db_session):
    """Test that a user with proper privileges can access a Program resource.

    Note: Users get access to programs through the Partner or Grantor Organization
    that owns the program, not by assigning roles directly to the program.
    """
    user, token = user_and_token
    program = ProgramFactory.create()
    # Give user access to the program by assigning them a role on the partner that owns it
    setup_user_with_roles(
        db_session, [program.partner], user=user, privileges=[Privilege.VIEW_PROGRAM]
    )

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.PROGRAM,
        program.program_id,
        [Privilege.VIEW_PROGRAM],
    )

    assert resp.status_code == 200


def test_can_access_grantor_organization_resource_type_200(user_and_token, client, db_session):
    """Test that a user with proper privileges can access a Grantor Organization resource."""
    user, token = user_and_token
    organization = GrantorOrganizationFactory.create()
    setup_user_with_roles(
        db_session,
        [organization],
        user=user,
        privileges=[Privilege.VIEW_GRANTOR_ORGANIZATION],
    )

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.GRANTOR_ORGANIZATION,
        organization.grantor_organization_id,
        [Privilege.VIEW_GRANTOR_ORGANIZATION],
    )

    assert resp.status_code == 200


def test_can_access_partner_missing_privilege_403(user_and_token, client, db_session):
    """Test that a user without the required privilege cannot access a Partner resource."""
    user, token = user_and_token
    partner = PartnerFactory.create()
    setup_user_with_roles(db_session, [partner], user=user, privileges=[Privilege.VIEW_PARTNER])

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.PARTNER,
        partner.partner_id,
        [Privilege.UPDATE_PARTNER],
    )

    assert resp.status_code == 403


def test_can_access_program_missing_privilege_403(user_and_token, client, db_session):
    """Test that a user without the required privilege cannot access a Program resource."""
    user, token = user_and_token
    program = ProgramFactory.create()
    setup_user_with_roles(
        db_session, [program.partner], user=user, privileges=[Privilege.VIEW_PROGRAM]
    )

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.PROGRAM,
        program.program_id,
        [Privilege.UPDATE_PROGRAM],
    )

    assert resp.status_code == 403


def test_can_access_grantor_organization_missing_privilege_403(user_and_token, client, db_session):
    """Test that a user without the required privilege cannot access a Grantor Organization resource."""
    user, token = user_and_token
    organization = GrantorOrganizationFactory.create()
    setup_user_with_roles(
        db_session,
        [organization],
        user=user,
        privileges=[Privilege.VIEW_GRANTOR_ORGANIZATION],
    )

    resp = _post(
        client,
        user.user_id,
        token,
        ResourceType.GRANTOR_ORGANIZATION,
        organization.grantor_organization_id,
        [Privilege.UPDATE_GRANTOR_ORGANIZATION],
    )

    assert resp.status_code == 403
