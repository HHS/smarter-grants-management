import enum
import uuid
from datetime import datetime
from typing import Any

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import OpportunityAuditEvent
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit
from src.db.models.opportunity_models import (
    LinkOpportunitySummaryApplicantType,
    LinkOpportunitySummaryFundingCategory,
    LinkOpportunitySummaryFundingInstrument,
    Opportunity,
    OpportunitySummary,
)
from src.db.models.user_models import User
from src.services.opportunities.authorization import has_access
from src.services.opportunities.get_opportunity import get_opportunity


def _check_existing_summary(opportunity: Opportunity, is_forecast: bool) -> None:
    existing_summary = (
        opportunity.forecast_summary if is_forecast else opportunity.non_forecast_summary
    )
    if existing_summary is not None:
        summary_type = "forecast" if is_forecast else "non-forecast"
        raise_flask_error(
            422,
            f"An opportunity summary of type {summary_type} already exists",
        )


def _get_opportunity_summary(
    opportunity: Opportunity,
    opportunity_summary_id: uuid.UUID,
) -> OpportunitySummary:
    for summary in opportunity.opportunity_summaries:
        if summary.opportunity_summary_id == opportunity_summary_id:
            return summary

    raise_flask_error(
        404,
        f"Could not find Opportunity Summary with ID {opportunity_summary_id}",
    )


def _replace_summary_lookups(
    summary: OpportunitySummary,
    funding_instruments: list,
    funding_categories: list,
    applicant_types: list,
) -> None:
    summary.link_funding_instruments = [
        LinkOpportunitySummaryFundingInstrument(funding_instrument=value)
        for value in funding_instruments
    ]
    summary.link_funding_categories = [
        LinkOpportunitySummaryFundingCategory(funding_category=value)
        for value in funding_categories
    ]
    summary.link_applicant_types = [
        LinkOpportunitySummaryApplicantType(applicant_type=value) for value in applicant_types
    ]


def _audit_value(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, list):
        return [_audit_value(item) for item in value]
    return value


def create_opportunity_summary(
    db_session: db.Session,
    opportunity_id: uuid.UUID,
    summary_data: dict,
    user: User,
) -> OpportunitySummary:
    opportunity = get_opportunity(db_session, opportunity_id)

    if not has_access(user, opportunity, "update"):
        raise_flask_error(403, "User does not have access to update this opportunity")

    _check_existing_summary(opportunity, summary_data["is_forecast"])

    funding_instruments = summary_data.pop("funding_instruments")
    funding_categories = summary_data.pop("funding_categories")
    applicant_types = summary_data.pop("applicant_types")

    summary = OpportunitySummary(
        opportunity=opportunity,
        **summary_data,
    )
    _replace_summary_lookups(
        summary,
        funding_instruments,
        funding_categories,
        applicant_types,
    )

    db_session.add(summary)
    db_session.flush()

    db_session.add(
        OpportunityGroupAudit(
            opportunity_group=opportunity.opportunity_group,
            opportunity_audit_event=OpportunityAuditEvent.OPPORTUNITY_SUMMARY_CREATED,
            user=user,
            opportunity=opportunity,
            opportunity_summary=summary,
            audit_metadata={
                "opportunity_summary_id": str(summary.opportunity_summary_id),
                "is_forecast": summary.is_forecast,
            },
        )
    )
    db_session.flush()

    return summary


def update_opportunity_summary(
    db_session: db.Session,
    opportunity_id: uuid.UUID,
    opportunity_summary_id: uuid.UUID,
    summary_data: dict,
    user: User,
) -> OpportunitySummary:
    opportunity = get_opportunity(db_session, opportunity_id)

    if not has_access(user, opportunity, "update"):
        raise_flask_error(403, "User does not have access to update this opportunity")

    summary = _get_opportunity_summary(opportunity, opportunity_summary_id)

    funding_instruments = summary_data.pop("funding_instruments")
    funding_categories = summary_data.pop("funding_categories")
    applicant_types = summary_data.pop("applicant_types")

    audit_metadata: dict[str, dict[str, Any]] = {}

    for field_name, new_value in summary_data.items():
        old_value = getattr(summary, field_name)
        if old_value != new_value:
            audit_metadata[field_name] = {
                "before": _audit_value(old_value),
                "after": _audit_value(new_value),
            }
            setattr(summary, field_name, new_value)

    old_funding_instruments = set(summary.funding_instruments)
    new_funding_instruments = set(funding_instruments)

    old_funding_categories = set(summary.funding_categories)
    new_funding_categories = set(funding_categories)

    old_applicant_types = set(summary.applicant_types)
    new_applicant_types = set(applicant_types)

    if old_funding_instruments != new_funding_instruments:
        audit_metadata["funding_instruments"] = {
            "before": sorted(_audit_value(list(old_funding_instruments))),
            "after": sorted(_audit_value(list(new_funding_instruments))),
        }

    if old_funding_categories != new_funding_categories:
        audit_metadata["funding_categories"] = {
            "before": sorted(_audit_value(list(old_funding_categories))),
            "after": sorted(_audit_value(list(new_funding_categories))),
        }

    if old_applicant_types != new_applicant_types:
        audit_metadata["applicant_types"] = {
            "before": sorted(_audit_value(list(old_applicant_types))),
            "after": sorted(_audit_value(list(new_applicant_types))),
        }

    if (
        old_funding_instruments != new_funding_instruments
        or old_funding_categories != new_funding_categories
        or old_applicant_types != new_applicant_types
    ):
        _replace_summary_lookups(
            summary,
            funding_instruments,
            funding_categories,
            applicant_types,
        )

    if audit_metadata:
        db_session.add(
            OpportunityGroupAudit(
                opportunity_group=opportunity.opportunity_group,
                opportunity_audit_event=OpportunityAuditEvent.OPPORTUNITY_SUMMARY_UPDATED,
                user=user,
                opportunity=opportunity,
                opportunity_summary=summary,
                audit_metadata=audit_metadata,
            )
        )

    db_session.flush()
    return summary
