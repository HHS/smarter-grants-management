def list_request(**filters):
    payload = {
        "pagination": {
            "page_offset": 1,
            "page_size": 25,
        }
    }
    if filters:
        payload["filters"] = filters
    return payload


def test_opportunity_list_returns_opportunities(
    client,
    api_key_headers,
    enable_factory_create,
):
    from tests.db.models.factories import OpportunityFactory

    opportunities = OpportunityFactory.create_batch(3)

    response = client.post(
        "/v1/opportunities/list",
        json=list_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    response_json = response.get_json()
    returned_ids = {item["opportunity_id"] for item in response_json["data"]}

    for opportunity in opportunities:
        assert str(opportunity.opportunity_id) in returned_ids

    assert response_json["pagination_info"]["total_records"] >= 3


def test_opportunity_list_filters_by_group(
    client,
    api_key_headers,
    enable_factory_create,
):
    from tests.db.models.factories import OpportunityFactory, OpportunityGroupFactory

    target_group = OpportunityGroupFactory.create()
    other_group = OpportunityGroupFactory.create()

    target_opportunity = OpportunityFactory.create(opportunity_group=target_group)
    OpportunityFactory.create(opportunity_group=other_group)

    response = client.post(
        "/v1/opportunities/list",
        json=list_request(opportunity_group_id=str(target_group.opportunity_group_id)),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    ids = [item["opportunity_id"] for item in response.get_json()["data"]]
    assert ids == [str(target_opportunity.opportunity_id)]


def test_opportunity_list_query_matches_number(
    client,
    api_key_headers,
    enable_factory_create,
):
    from tests.db.models.factories import OpportunityFactory

    target = OpportunityFactory.create(opportunity_number="SPECIAL-SEARCH-123")
    OpportunityFactory.create(opportunity_number="NOT-A-MATCH")

    response = client.post(
        "/v1/opportunities/list",
        json=list_request(query="SEARCH-123"),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    ids = [item["opportunity_id"] for item in response.get_json()["data"]]
    assert ids == [str(target.opportunity_id)]


def test_opportunity_list_query_matches_title(
    client,
    api_key_headers,
    enable_factory_create,
):
    from tests.db.models.factories import OpportunityFactory

    target = OpportunityFactory.create(opportunity_title="Distinctive Marmot Research Program")
    OpportunityFactory.create(opportunity_title="Entirely Different Opportunity")

    response = client.post(
        "/v1/opportunities/list",
        json=list_request(query="marmot research"),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    ids = [item["opportunity_id"] for item in response.get_json()["data"]]
    assert ids == [str(target.opportunity_id)]


def test_opportunity_list_paginates(
    client,
    api_key_headers,
    enable_factory_create,
):
    from tests.db.models.factories import OpportunityFactory

    OpportunityFactory.create_batch(3)

    response = client.post(
        "/v1/opportunities/list",
        json={
            "pagination": {
                "page_offset": 1,
                "page_size": 2,
            }
        },
        headers=api_key_headers,
    )

    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 2
    assert response.get_json()["pagination_info"]["page_size"] == 2


def test_opportunity_list_no_auth_401(client):
    response = client.post(
        "/v1/opportunities/list",
        json=list_request(),
    )

    assert response.status_code == 401
