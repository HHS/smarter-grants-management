import uuid

from src.auth.api_jwt_auth import create_jwt_for_user
from src.constants.lookup_constants import Privilege
from tests.db.models.factories import GrantorOrganizationFactory, UserApiKeyFactory
from tests.test_utils.auth_test_utils import setup_user_with_roles


def test_get_grantor_organization_with_api_key_200(client, db_session, enable_factory_create):
    grantor_organization = GrantorOrganizationFactory.create()
    user = setup_user_with_roles(
        db_session,
        resources=[grantor_organization],
        privileges=[Privilege.VIEW_GRANTOR_ORGANIZATION],
    )
    api_key = UserApiKeyFactory.create(user=user)

    resp = client.get(
        f"/v1/grantor-organizations/{grantor_organization.grantor_organization_id}",
        headers={"X-API-Key": api_key.key_id},
    )

    assert resp.status_code == 200
    data = resp.get_json()["data"]

    assert data["grantor_organization_id"] == str(grantor_organization.grantor_organization_id)
    assert data["organization_name"] == grantor_organization.organization_name
    assert data["grantor_organization_type"] == grantor_organization.grantor_organization_type
    assert data["partner"]["partner_id"] == str(grantor_organization.partner_id)
    assert data["partner"]["partner_name"] == grantor_organization.partner.partner_name


def test_get_grantor_organization_with_jwt_200(client, db_session, enable_factory_create):
    grantor_organization = GrantorOrganizationFactory.create()
    user = setup_user_with_roles(
        db_session,
        resources=[grantor_organization],
        privileges=[Privilege.VIEW_GRANTOR_ORGANIZATION],
    )

    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()

    resp = client.get(
        f"/v1/grantor-organizations/{grantor_organization.grantor_organization_id}",
        headers={"X-MGMT-Token": token},
    )

    assert resp.status_code == 200
    data = resp.get_json()["data"]

    assert data["grantor_organization_id"] == str(grantor_organization.grantor_organization_id)
    assert data["organization_name"] == grantor_organization.organization_name
    assert data["grantor_organization_type"] == grantor_organization.grantor_organization_type
    assert data["partner"]["partner_id"] == str(grantor_organization.partner_id)
    assert data["partner"]["partner_name"] == grantor_organization.partner.partner_name


def test_get_grantor_organization_with_parent_200(client, db_session, enable_factory_create):
    parent_organization = GrantorOrganizationFactory.create()
    grantor_organization = GrantorOrganizationFactory.create(
        parent_organization=parent_organization, partner=parent_organization.partner
    )
    user = setup_user_with_roles(
        db_session,
        resources=[grantor_organization],
        privileges=[Privilege.VIEW_GRANTOR_ORGANIZATION],
    )
    api_key = UserApiKeyFactory.create(user=user)

    resp = client.get(
        f"/v1/grantor-organizations/{grantor_organization.grantor_organization_id}",
        headers={"X-API-Key": api_key.key_id},
    )

    assert resp.status_code == 200
    data = resp.get_json()["data"]

    assert data["grantor_organization_id"] == str(grantor_organization.grantor_organization_id)
    assert data["organization_name"] == grantor_organization.organization_name
    assert data["parent_organization"]["grantor_organization_id"] == str(
        parent_organization.grantor_organization_id
    )
    assert data["parent_organization"]["organization_name"] == parent_organization.organization_name
    assert (
        data["parent_organization"]["grantor_organization_type"]
        == parent_organization.grantor_organization_type
    )
    assert "partner" not in data["parent_organization"]
    assert "parent_organization" not in data["parent_organization"]


def test_get_grantor_organization_404(client, db_session, enable_factory_create):
    api_key = UserApiKeyFactory.create()

    resp = client.get(
        f"/v1/grantor-organizations/{uuid.uuid4()}", headers={"X-API-Key": api_key.key_id}
    )

    assert resp.status_code == 404
    assert resp.get_json()["message"].startswith("Could not find grantor organization with ID")


def test_get_grantor_organization_403(client, db_session, enable_factory_create):
    grantor_organization = GrantorOrganizationFactory.create()
    user = setup_user_with_roles(
        db_session, resources=[grantor_organization], privileges=[Privilege.VIEW_PROGRAM]
    )
    api_key = UserApiKeyFactory.create(user=user)

    resp = client.get(
        f"/v1/grantor-organizations/{grantor_organization.grantor_organization_id}",
        headers={"X-API-Key": api_key.key_id},
    )
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Forbidden"


def test_get_grantor_organization_invalid_auth_401(client, db_session, enable_factory_create):
    grantor_organization = GrantorOrganizationFactory.create()
    resp = client.get(
        f"/v1/grantor-organizations/{grantor_organization.grantor_organization_id}",
        headers={"X-API-Key": "not-a-real-key"},
    )
    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Invalid API key"


def test_get_grantor_organization_no_auth_401(client, db_session, enable_factory_create):
    grantor_organization = GrantorOrganizationFactory.create()
    resp = client.get(f"/v1/grantor-organizations/{grantor_organization.grantor_organization_id}")
    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Unauthorized"
