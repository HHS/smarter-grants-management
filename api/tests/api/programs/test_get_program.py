import uuid

from src.auth.api_jwt_auth import create_jwt_for_user
from src.constants.lookup_constants import Privilege
from tests.db.models.factories import ProgramFactory, UserApiKeyFactory
from tests.test_utils.auth_test_utils import setup_user_with_roles


def validate_program_response(data, program):
    assert data["program_id"] == str(program.program_id)
    assert data["program_name"] == program.program_name

    assert data["partner"]["partner_id"] == str(program.partner_id)
    assert data["partner"]["partner_name"] == program.partner.partner_name

    program_office = data["program_office"]
    assert program_office["grantor_organization_id"] == str(program.program_office_id)
    assert program_office["organization_name"] == program.program_office.organization_name
    assert (
        program_office["grantor_organization_type"]
        == program.program_office.grantor_organization_type
    )
    assert "partner" not in program_office
    assert "parent_organization" not in program_office

    grant_office = data["grant_office"]
    assert grant_office["grantor_organization_id"] == str(program.grant_office_id)
    assert grant_office["organization_name"] == program.grant_office.organization_name
    assert (
        grant_office["grantor_organization_type"] == program.grant_office.grantor_organization_type
    )
    assert "partner" not in grant_office
    assert "parent_organization" not in grant_office


def test_get_program_with_api_key_200(client, db_session, enable_factory_create):
    program = ProgramFactory.create()
    # Users are never attached to program resources directly, so assign the
    # role on the partner that owns the program
    user = setup_user_with_roles(
        db_session, resources=[program.partner], privileges=[Privilege.VIEW_PROGRAM]
    )
    api_key = UserApiKeyFactory.create(user=user)

    resp = client.get(f"/v1/programs/{program.program_id}", headers={"X-API-Key": api_key.key_id})

    assert resp.status_code == 200
    validate_program_response(resp.get_json()["data"], program)


def test_get_program_with_jwt_200(client, db_session, enable_factory_create):
    program = ProgramFactory.create()
    user = setup_user_with_roles(
        db_session, resources=[program.partner], privileges=[Privilege.VIEW_PROGRAM]
    )

    token, _ = create_jwt_for_user(user, db_session)
    db_session.commit()

    resp = client.get(f"/v1/programs/{program.program_id}", headers={"X-MGMT-Token": token})

    assert resp.status_code == 200
    validate_program_response(resp.get_json()["data"], program)


def test_get_program_404(client, db_session, enable_factory_create):
    api_key = UserApiKeyFactory.create()

    resp = client.get(f"/v1/programs/{uuid.uuid4()}", headers={"X-API-Key": api_key.key_id})

    assert resp.status_code == 404
    assert resp.get_json()["message"].startswith("Could not find program with ID")


def test_get_program_via_grant_office_200(client, db_session, enable_factory_create):
    program = ProgramFactory.create()
    user = setup_user_with_roles(
        db_session, resources=[program.grant_office], privileges=[Privilege.VIEW_PROGRAM]
    )
    api_key = UserApiKeyFactory.create(user=user)

    resp = client.get(f"/v1/programs/{program.program_id}", headers={"X-API-Key": api_key.key_id})

    assert resp.status_code == 200
    validate_program_response(resp.get_json()["data"], program)


def test_get_program_via_program_office_200(client, db_session, enable_factory_create):
    program = ProgramFactory.create()
    user = setup_user_with_roles(
        db_session, resources=[program.program_office], privileges=[Privilege.VIEW_PROGRAM]
    )
    api_key = UserApiKeyFactory.create(user=user)

    resp = client.get(f"/v1/programs/{program.program_id}", headers={"X-API-Key": api_key.key_id})

    assert resp.status_code == 200
    validate_program_response(resp.get_json()["data"], program)


def test_get_program_403(client, db_session, enable_factory_create):
    # User doesn't have view_program
    program = ProgramFactory.create()
    user = setup_user_with_roles(
        db_session, resources=[program.partner], privileges=[Privilege.VIEW_PARTNER]
    )
    api_key = UserApiKeyFactory.create(user=user)

    resp = client.get(f"/v1/programs/{program.program_id}", headers={"X-API-Key": api_key.key_id})

    assert resp.status_code == 403
    assert resp.get_json()["message"] == "Forbidden"


def test_get_program_invalid_auth_401(client, db_session, enable_factory_create):
    program = ProgramFactory.create()

    resp = client.get(f"/v1/programs/{program.program_id}", headers={"X-API-Key": "not-a-real-key"})

    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Invalid API key"


def test_get_program_no_auth_401(client, db_session, enable_factory_create):
    program = ProgramFactory.create()

    resp = client.get(f"/v1/programs/{program.program_id}")

    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Unauthorized"
