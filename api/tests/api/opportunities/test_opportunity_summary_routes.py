import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from src.constants.lookup_constants import (
    ApplicantType,
    FundingCategory,
    FundingInstrument,
    OpportunityAuditEvent,
)
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit
from src.db.models.opportunity_models import OpportunitySummary
from tests.db.models.factories import OpportunityFactory, OpportunitySummaryFactory


def build_summary_request(is_forecast=False):
    now = datetime.now(UTC)
    return {
        "summary_description": "A summary for testing the Opportunity API.",
        "is_cost_sharing": False,
        "post_timestamp": now.isoformat(),
        "close_timestamp": (now + timedelta(days=30)).isoformat(),
        "award_floor": 10_000,
        "award_ceiling": 100_000,
        "funding_categories": [next(iter(FundingCategory)).value],
        "funding_instruments": [next(iter(FundingInstrument)).value],
        "applicant_types": [next(iter(ApplicantType)).value],
        "agency_contact_description": None,
        "agency_email_address": None,
        "agency_email_address_description": None,
        "is_forecast": is_forecast,
    }


def build_summary_update_request(summary):
    request = build_summary_request()
    request.pop("is_forecast")
    request["summary_description"] = summary.summary_description
    request["is_cost_sharing"] = summary.is_cost_sharing
    request["post_timestamp"] = summary.post_timestamp.isoformat()
    return request


def test_opportunity_summary_create_200(
    client,
    db_session,
    api_key_headers,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/summaries",
        json=build_summary_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert data["summary_description"] == "A summary for testing the Opportunity API."
    assert data["is_forecast"] is False

    summary = db_session.execute(
        select(OpportunitySummary).where(
            OpportunitySummary.opportunity_summary_id == uuid.UUID(data["opportunity_summary_id"])
        )
    ).scalar_one()
    assert summary.opportunity_id == opportunity.opportunity_id

    audit = db_session.execute(
        select(OpportunityGroupAudit).where(
            OpportunityGroupAudit.opportunity_summary_id == summary.opportunity_summary_id,
            OpportunityGroupAudit.opportunity_audit_event
            == OpportunityAuditEvent.OPPORTUNITY_SUMMARY_CREATED,
        )
    ).scalar_one()
    assert audit.opportunity_id == opportunity.opportunity_id


def test_opportunity_summary_create_forecast_200(
    client,
    api_key_headers,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()
    request = build_summary_request(is_forecast=True)

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/summaries",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["is_forecast"] is True


def test_opportunity_summary_create_duplicate_type_422(
    client,
    api_key_headers,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()
    OpportunitySummaryFactory.create(opportunity=opportunity, is_forecast=False)

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/summaries",
        json=build_summary_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 422
    assert "already exists" in response.get_json()["message"]


def test_opportunity_summary_create_unknown_opportunity_404(
    client,
    api_key_headers,
):
    response = client.post(
        f"/v1/opportunities/{uuid.uuid4()}/summaries",
        json=build_summary_request(),
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_opportunity_summary_create_invalid_award_values_422(
    client,
    api_key_headers,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()
    request = build_summary_request()
    request["award_floor"] = 200_000
    request["award_ceiling"] = 100_000

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/summaries",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 422


def test_opportunity_summary_create_no_auth_401(
    client,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()

    response = client.post(
        f"/v1/opportunities/{opportunity.opportunity_id}/summaries",
        json=build_summary_request(),
    )

    assert response.status_code == 401


def test_opportunity_summary_update_200(
    client,
    db_session,
    api_key_headers,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()
    summary = OpportunitySummaryFactory.create(
        opportunity=opportunity,
        is_forecast=False,
    )
    request = build_summary_update_request(summary)
    request["summary_description"] = "Updated summary description"

    response = client.put(
        f"/v1/opportunities/{opportunity.opportunity_id}/summaries/"
        f"{summary.opportunity_summary_id}",
        json=request,
        headers=api_key_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["summary_description"] == "Updated summary description"

    db_session.refresh(summary)
    assert summary.summary_description == "Updated summary description"

    audit = db_session.execute(
        select(OpportunityGroupAudit).where(
            OpportunityGroupAudit.opportunity_summary_id == summary.opportunity_summary_id,
            OpportunityGroupAudit.opportunity_audit_event
            == OpportunityAuditEvent.OPPORTUNITY_SUMMARY_UPDATED,
        )
    ).scalar_one()
    assert audit.audit_metadata is not None
    assert audit.audit_metadata["summary_description"]["before"] != "Updated summary description"
    assert audit.audit_metadata["summary_description"]["after"] == "Updated summary description"


def test_opportunity_summary_update_wrong_opportunity_404(
    client,
    api_key_headers,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()
    other_opportunity = OpportunityFactory.create()
    summary = OpportunitySummaryFactory.create(
        opportunity=other_opportunity,
        is_forecast=False,
    )

    response = client.put(
        f"/v1/opportunities/{opportunity.opportunity_id}/summaries/"
        f"{summary.opportunity_summary_id}",
        json=build_summary_update_request(summary),
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_opportunity_summary_update_unknown_summary_404(
    client,
    api_key_headers,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()

    response = client.put(
        f"/v1/opportunities/{opportunity.opportunity_id}/summaries/{uuid.uuid4()}",
        json={key: value for key, value in build_summary_request().items() if key != "is_forecast"},
        headers=api_key_headers,
    )

    assert response.status_code == 404


def test_opportunity_summary_update_no_auth_401(
    client,
    enable_factory_create,
):
    opportunity = OpportunityFactory.create()
    summary = OpportunitySummaryFactory.create(
        opportunity=opportunity,
        is_forecast=False,
    )

    response = client.put(
        f"/v1/opportunities/{opportunity.opportunity_id}/summaries/"
        f"{summary.opportunity_summary_id}",
        json=build_summary_update_request(summary),
    )

    assert response.status_code == 401
