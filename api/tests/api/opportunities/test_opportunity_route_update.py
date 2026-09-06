from sqlalchemy import select

from src.constants.lookup_constants import OpportunityAuditEvent, OpportunityCategory
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit


def build_update_request(opportunity):
    category_explanation = opportunity.category_explanation
    if opportunity.category == OpportunityCategory.OTHER and not category_explanation:
        category_explanation = "Other category explanation"

    return {
        "opportunity_title": opportunity.opportunity_title,
        "tagline": opportunity.tagline,
        "purpose_statement": opportunity.purpose_statement,
        "category": opportunity.category.value,
        "category_explanation": category_explanation,
    }


def test_opportunity_update_200(
    client,
    db_session,
    api_key_headers,
    opportunity,
):
    request = build_update_request(opportunity)
    request["opportunity_title"] = "Updated Opportunity Title"
    request["tagline"] = "Updated tagline"
    request["purpose_statement"] = "Updated purpose statement"

    response = client.put(
        f"/v1/opportunities/{opportunity.opportunity_id}",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["opportunity_title"] == request["opportunity_title"]
    assert data["tagline"] == request["tagline"]
    assert data["purpose_statement"] == request["purpose_statement"]

    db_session.refresh(opportunity)
    assert opportunity.opportunity_title == request["opportunity_title"]
    assert opportunity.tagline == request["tagline"]
    assert opportunity.purpose_statement == request["purpose_statement"]

    audit = db_session.execute(
        select(OpportunityGroupAudit).where(
            OpportunityGroupAudit.opportunity_id == opportunity.opportunity_id,
            OpportunityGroupAudit.opportunity_audit_event
            == OpportunityAuditEvent.OPPORTUNITY_UPDATED,
        )
    ).scalar_one()

    assert audit.audit_metadata is not None
    assert audit.audit_metadata["opportunity_title"]["before"] != request["opportunity_title"]
    assert audit.audit_metadata["opportunity_title"]["after"] == request["opportunity_title"]


def test_opportunity_update_no_changes_does_not_create_audit(
    client,
    db_session,
    api_key_headers,
    opportunity,
):
    response = client.put(
        f"/v1/opportunities/{opportunity.opportunity_id}",
        json=build_update_request(opportunity),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    audits = (
        db_session.execute(
            select(OpportunityGroupAudit).where(
                OpportunityGroupAudit.opportunity_id == opportunity.opportunity_id,
                OpportunityGroupAudit.opportunity_audit_event
                == OpportunityAuditEvent.OPPORTUNITY_UPDATED,
            )
        )
        .scalars()
        .all()
    )

    assert audits == []


def test_opportunity_update_no_auth_401(client, opportunity):
    response = client.put(
        f"/v1/opportunities/{opportunity.opportunity_id}",
        json=build_update_request(opportunity),
    )

    assert response.status_code == 401
