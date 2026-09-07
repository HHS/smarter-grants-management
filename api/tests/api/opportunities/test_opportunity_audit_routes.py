from src.constants.lookup_constants import OpportunityAuditEvent
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit
from tests.db.models.factories import OpportunityFactory, UserFactory


def audit_request(**filters):
    payload = {
        "pagination": {
            "page_offset": 1,
            "page_size": 25,
        }
    }
    if filters:
        payload["filters"] = filters
    return payload


def add_audit(db_session, opportunity, user, event):
    audit = OpportunityGroupAudit(
        opportunity_group=opportunity.opportunity_group,
        opportunity_audit_event=event,
        user=user,
        opportunity=opportunity,
        audit_metadata={"test": event.value},
    )
    db_session.add(audit)
    db_session.commit()
    return audit


def test_opportunity_audit_list_returns_events(
    client,
    db_session,
    api_key_headers,
    opportunity,
):
    user = UserFactory.create()
    created = add_audit(
        db_session,
        opportunity,
        user,
        OpportunityAuditEvent.OPPORTUNITY_CREATED,
    )
    updated = add_audit(
        db_session,
        opportunity,
        user,
        OpportunityAuditEvent.OPPORTUNITY_UPDATED,
    )

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/audit_history",
        json=audit_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 200
    response_json = response.get_json()
    returned_ids = {item["opportunity_group_audit_id"] for item in response_json["data"]}
    assert str(created.opportunity_group_audit_id) in returned_ids
    assert str(updated.opportunity_group_audit_id) in returned_ids
    assert response_json["pagination_info"]["total_records"] >= 2


def test_opportunity_audit_list_filters_by_event(
    client,
    db_session,
    api_key_headers,
    opportunity,
):
    user = UserFactory.create()
    created = add_audit(
        db_session,
        opportunity,
        user,
        OpportunityAuditEvent.OPPORTUNITY_CREATED,
    )
    add_audit(
        db_session,
        opportunity,
        user,
        OpportunityAuditEvent.OPPORTUNITY_UPDATED,
    )

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/audit_history",
        json=audit_request(
            opportunity_audit_event=[OpportunityAuditEvent.OPPORTUNITY_CREATED.value]
        ),
        headers=api_key_headers,
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert [item["opportunity_group_audit_id"] for item in data] == [
        str(created.opportunity_group_audit_id)
    ]


def test_opportunity_audit_list_does_not_return_other_opportunity_events(
    client,
    db_session,
    api_key_headers,
    opportunity,
    enable_factory_create,
):
    user = UserFactory.create()
    target = add_audit(
        db_session,
        opportunity,
        user,
        OpportunityAuditEvent.OPPORTUNITY_CREATED,
    )
    other_opportunity = OpportunityFactory.create()
    other = add_audit(
        db_session,
        other_opportunity,
        user,
        OpportunityAuditEvent.OPPORTUNITY_CREATED,
    )

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/audit_history",
        json=audit_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 200
    ids = {item["opportunity_group_audit_id"] for item in response.get_json()["data"]}
    assert str(target.opportunity_group_audit_id) in ids
    assert str(other.opportunity_group_audit_id) not in ids


def test_opportunity_audit_list_paginates(
    client,
    db_session,
    api_key_headers,
    opportunity,
):
    user = UserFactory.create()
    for _ in range(3):
        add_audit(
            db_session,
            opportunity,
            user,
            OpportunityAuditEvent.OPPORTUNITY_UPDATED,
        )

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/audit_history",
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


def test_opportunity_audit_list_unknown_opportunity_404(
    client,
    api_key_headers,
):
    import uuid

    response = client.post(
        f"/v1/opportunities/{uuid.uuid4()}/audit_history",
        json=audit_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_opportunity_audit_list_no_auth_401(client, opportunity):
    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/audit_history",
        json=audit_request(),
    )

    assert response.status_code == 401
