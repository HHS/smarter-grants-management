import uuid

import pytest

from src.auth.api_jwt_auth import create_jwt_for_user
from src.constants.lookup_constants import MgmtPrivilege, MgmtResourceType
from tests.db.models.factories import (
    MgmtInternalResourceFactory,
    MgmtUserApiKeyFactory,
    MgmtUserFactory,
)
from tests.test_utils.auth_test_utils import setup_user_with_roles


@pytest.fixture
def user_and_token(enable_factory_create, db_session, app):
    """Create a user and a valid JWT token for them."""
    user = MgmtUserFactory.create()
    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()
    return user, token


def _post(client, user_id, token, resource_type, resource_id, privileges):
    return client.post(
        f"v1/users/{user_id}/can_access",
        headers={"X-MGMT-Token": token},
        json={
            "mgmt_resource_type": resource_type,
            "mgmt_resource_id": str(resource_id),
            "mgmt_privileges": privileges,
        },
    )


def test_can_access_multiple_privileges_requires_all_403(user_and_token, client, db_session):
    """When multiple privileges are requested, the user must have all of them."""
    user, token = user_and_token
    internal_resource = MgmtInternalResourceFactory.create()
    setup_user_with_roles(
        db_session, [internal_resource], user=user, privileges=[MgmtPrivilege.VIEW_PARTNER]
    )

    resp = _post(
        client,
        user.mgmt_user_id,
        token,
        MgmtResourceType.INTERNAL,
        internal_resource.mgmt_internal_resource_id,
        [MgmtPrivilege.VIEW_PARTNER, MgmtPrivilege.VIEW_PROGRAM],
    )

    assert resp.status_code == 403


def test_can_access_missing_privilege_403(user_and_token, client, db_session):
    user, token = user_and_token
    internal_resource = MgmtInternalResourceFactory.create()
    setup_user_with_roles(
        db_session, [internal_resource], user=user, privileges=[MgmtPrivilege.VIEW_PARTNER]
    )

    resp = _post(
        client,
        user.mgmt_user_id,
        token,
        MgmtResourceType.INTERNAL,
        internal_resource.mgmt_internal_resource_id,
        [MgmtPrivilege.UPDATE_PARTNER],
    )

    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Forbidden"


def test_can_access_no_roles_403(user_and_token, client, db_session):
    """A user with no roles at all against the resource is denied."""
    user, token = user_and_token
    internal_resource = MgmtInternalResourceFactory.create()

    resp = _post(
        client,
        user.mgmt_user_id,
        token,
        MgmtResourceType.INTERNAL,
        internal_resource.mgmt_internal_resource_id,
        [MgmtPrivilege.VIEW_PARTNER],
    )

    assert resp.status_code == 403


def test_can_access_other_user_403(user_and_token, client, db_session):
    """A user may only check access for their own user ID."""
    user, token = user_and_token
    internal_resource = MgmtInternalResourceFactory.create()
    setup_user_with_roles(
        db_session, [internal_resource], user=user, privileges=[MgmtPrivilege.VIEW_PARTNER]
    )

    other_user_id = uuid.uuid4()
    resp = _post(
        client,
        other_user_id,
        token,
        MgmtResourceType.INTERNAL,
        internal_resource.mgmt_internal_resource_id,
        [MgmtPrivilege.VIEW_PARTNER],
    )

    assert resp.status_code == 403


def test_can_access_resource_not_found_404(user_and_token, client):
    user, token = user_and_token

    resp = _post(
        client,
        user.mgmt_user_id,
        token,
        MgmtResourceType.INTERNAL,
        uuid.uuid4(),
        [MgmtPrivilege.VIEW_PARTNER],
    )

    assert resp.status_code == 404


def test_can_access_unsupported_resource_type_404(user_and_token, client):
    """Resource types without a getter (e.g. opportunity) are not supported yet."""
    user, token = user_and_token

    resp = _post(
        client,
        user.mgmt_user_id,
        token,
        MgmtResourceType.OPPORTUNITY,
        uuid.uuid4(),
        [MgmtPrivilege.VIEW_PARTNER],
    )

    assert resp.status_code == 404


def test_can_access_internal_resource_type_200(user_and_token, client, db_session):
    user, token = user_and_token
    internal_resource = MgmtInternalResourceFactory.create()
    setup_user_with_roles(
        db_session, [internal_resource], user=user, privileges=[MgmtPrivilege.VIEW_PARTNER]
    )

    resp = _post(
        client,
        user.mgmt_user_id,
        token,
        MgmtResourceType.INTERNAL,
        internal_resource.mgmt_internal_resource_id,
        [MgmtPrivilege.VIEW_PARTNER],
    )

    assert resp.status_code == 200


def test_can_access_empty_privileges_422(user_and_token, client, db_session):
    user, token = user_and_token
    internal_resource = MgmtInternalResourceFactory.create()

    resp = _post(
        client,
        user.mgmt_user_id,
        token,
        MgmtResourceType.INTERNAL,
        internal_resource.mgmt_internal_resource_id,
        [],
    )

    assert resp.status_code == 422


def test_can_access_via_api_key_200(enable_factory_create, client, db_session):
    """The endpoint also authenticates via an API key (X-API-Key)."""
    api_key = MgmtUserApiKeyFactory.create(is_active=True)
    internal_resource = MgmtInternalResourceFactory.create()
    setup_user_with_roles(
        db_session,
        [internal_resource],
        user=api_key.mgmt_user,
        privileges=[MgmtPrivilege.VIEW_PARTNER],
    )

    resp = client.post(
        f"v1/users/{api_key.mgmt_user_id}/can_access",
        headers={"X-API-Key": api_key.key_id},
        json={
            "mgmt_resource_type": MgmtResourceType.INTERNAL,
            "mgmt_resource_id": str(internal_resource.mgmt_internal_resource_id),
            "mgmt_privileges": [MgmtPrivilege.VIEW_PARTNER],
        },
    )

    assert resp.status_code == 200


def test_can_access_no_token_401(client):
    resp = client.post(
        f"v1/users/{uuid.uuid4()}/can_access",
        json={
            "mgmt_resource_type": MgmtResourceType.INTERNAL,
            "mgmt_resource_id": str(uuid.uuid4()),
            "mgmt_privileges": [MgmtPrivilege.VIEW_PARTNER],
        },
    )

    assert resp.status_code == 401
