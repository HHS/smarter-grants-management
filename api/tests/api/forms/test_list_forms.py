import pytest

from tests.db.models.factories import UserApiKeyFactory


@pytest.fixture
def api_key_headers(enable_factory_create):
    api_key = UserApiKeyFactory.create()
    return {"X-API-Key": api_key.key_id}


def test_list_forms_200(client, api_key_headers):
    response = client.post("/v1/forms/list", headers=api_key_headers)
    assert response.status_code == 200

    forms = response.get_json()["data"]

    assert len(forms) == 5

    assert forms[0]["form_id"] == 713
    assert forms[0]["short_name"] == "SF424"
    assert forms[0]["version"] == "4.0"

    assert forms[1]["form_id"] == 768
    assert forms[1]["short_name"] == "RR_SF424"
    assert forms[1]["version"] == "5.0"

    assert forms[2]["form_id"] == 241
    assert forms[2]["short_name"] == "SF424A"
    assert forms[2]["version"] == "1.0"

    assert forms[3]["form_id"] == 591
    assert forms[3]["short_name"] == "Project_AbstractSummary"
    assert forms[3]["version"] == "2.0"

    assert forms[4]["form_id"] == 255
    assert forms[4]["short_name"] == "GG_LobbyingForm"
    assert forms[4]["version"] == "1.1"


def test_list_forms_bad_auth_401(client):
    response = client.post("/v1/forms/list", headers={"X-API-Key": "not an api key"})
    assert response.status_code == 401


def test_list_forms_no_auth_403(client):
    response = client.post("/v1/forms/list")
    assert response.status_code == 401
