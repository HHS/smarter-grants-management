import pytest

from tests.db.models.factories import UserApiKeyFactory


@pytest.fixture
def api_key_headers(enable_factory_create):
    api_key = UserApiKeyFactory.create()
    return {"X-API-Key": api_key.key_id}

def test_list_forms_200(client, api_key_headers):
    response = client.post("/v1/forms/list", headers=api_key_headers)
    assert response.status_code == 200

    print(response)