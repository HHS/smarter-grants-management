from src.auth.api_jwt_auth import parse_jwt_for_user
from tests.db.models.factories import UserApiKeyFactory


def test_internal_route_get_jwt_200(client, db_session, enable_factory_create):
    api_key = UserApiKeyFactory.create()

    resp = client.get("/v1/internal/api-jwt", headers={"X-API-Key": api_key.key_id})
    assert resp.status_code == 200

    # Easiest way to verify the token we got back is valid is
    # run it through the logic we use during login.
    jwt_token = resp.get_json()["data"]["jwt_token"]
    token_session = parse_jwt_for_user(jwt_token, db_session)
    assert token_session.is_valid is True


def test_internal_route_get_jwt_bad_api_key_401(client, db_session, enable_factory_create):
    api_key = UserApiKeyFactory.create(is_active=False)

    resp = client.get("/v1/internal/api-jwt", headers={"X-API-Key": api_key.key_id})
    assert resp.status_code == 401


def test_internal_route_get_jwt_no_api_key_401(client, db_session):
    resp = client.get("/v1/internal/api-jwt")
    assert resp.status_code == 401
