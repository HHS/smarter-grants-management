import uuid

from src.auth.api_jwt_auth import create_jwt_for_user
from src.constants.lookup_constants import Privilege
from tests.db.models.factories import PartnerFactory, UserApiKeyFactory
from tests.test_utils.auth_test_utils import setup_user_with_roles


def test_get_partner_with_api_key_200(client, db_session, enable_factory_create):
    partner = PartnerFactory.create()
    user = setup_user_with_roles(
        db_session, resources=[partner], privileges=[Privilege.VIEW_PARTNER]
    )
    api_key = UserApiKeyFactory.create(user=user)

    resp = client.get(f"/v1/partners/{partner.partner_id}", headers={"X-API-Key": api_key.key_id})

    assert resp.status_code == 200
    data = resp.get_json()["data"]

    assert data["partner_id"] == str(partner.partner_id)
    assert data["partner_name"] == partner.partner_name


def test_get_partner_with_jwt_200(client, db_session, enable_factory_create):
    partner = PartnerFactory.create()
    user = setup_user_with_roles(
        db_session, resources=[partner], privileges=[Privilege.VIEW_PARTNER]
    )

    token, user_token_session = create_jwt_for_user(user, db_session)
    db_session.commit()

    resp = client.get(f"/v1/partners/{partner.partner_id}", headers={"X-MGMT-Token": token})

    assert resp.status_code == 200
    data = resp.get_json()["data"]

    assert data["partner_id"] == str(partner.partner_id)
    assert data["partner_name"] == partner.partner_name


def test_get_partner_404(client, db_session, enable_factory_create):
    api_key = UserApiKeyFactory.create()

    resp = client.get(f"/v1/partners/{uuid.uuid4()}", headers={"X-API-Key": api_key.key_id})

    assert resp.status_code == 404
    assert resp.get_json()["message"].startswith("Could not find partner with ID")


def test_get_partner_403(client, db_session, enable_factory_create):
    # User doesn't have view_partner
    partner = PartnerFactory.create()
    user = setup_user_with_roles(
        db_session, resources=[partner], privileges=[Privilege.VIEW_PROGRAM]
    )
    api_key = UserApiKeyFactory.create(user=user)

    resp = client.get(f"/v1/partners/{partner.partner_id}", headers={"X-API-Key": api_key.key_id})
    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Forbidden"


def test_get_partner_invalid_auth_401(client, db_session, enable_factory_create):
    partner = PartnerFactory.create()
    resp = client.get(f"/v1/partners/{partner.partner_id}", headers={"X-API-Key": "not-a-real-key"})
    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Invalid API key"


def test_get_partner_no_auth_401(client, db_session, enable_factory_create):
    partner = PartnerFactory.create()
    resp = client.get(f"/v1/partners/{partner.partner_id}")
    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Unauthorized"
