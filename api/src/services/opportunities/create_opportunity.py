from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import OpportunityAuditEvent
from src.db.models.assistance_listing_models import AssistanceListing
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit
from src.db.models.opportunity_models import (
    Opportunity,
    OpportunityAssistanceListing,
    OpportunityGroup,
)
from src.db.models.user_models import User
from src.services.opportunities.authorization import has_access


def create_opportunity(db_session: db.Session, user: User, json_data: dict) -> Opportunity:
    opportunity_group = db_session.execute(
        select(OpportunityGroup).where(
            OpportunityGroup.opportunity_group_id == json_data["opportunity_group_id"]
        )
    ).scalar_one_or_none()
    if opportunity_group is None:
        raise_flask_error(
            404,
            f"Could not find opportunity group with ID {json_data['opportunity_group_id']}",
        )

    if not has_access(user, opportunity_group, "create"):
        raise_flask_error(403, "User does not have access to create an opportunity")

    existing_opportunity = db_session.execute(
        select(Opportunity).where(Opportunity.opportunity_number == json_data["opportunity_number"])
    ).scalar_one_or_none()
    if existing_opportunity is not None:
        raise_flask_error(
            422,
            f"Opportunity number {json_data['opportunity_number']} already exists",
        )

    assistance_listing = db_session.execute(
        select(AssistanceListing).where(
            AssistanceListing.assistance_listing_number == json_data["assistance_listing_number"]
        )
    ).scalar_one_or_none()
    if assistance_listing is None:
        raise_flask_error(
            404,
            "Could not find assistance listing with number "
            f"{json_data['assistance_listing_number']}",
        )

    opportunity = Opportunity(
        opportunity_group=opportunity_group,
        opportunity_number=json_data["opportunity_number"],
        opportunity_title=json_data["opportunity_title"],
        tagline=json_data["tagline"],
        purpose_statement=json_data["purpose_statement"],
        category=json_data["category"],
        category_explanation=json_data.get("category_explanation"),
    )
    db_session.add(opportunity)
    db_session.flush()

    db_session.add(
        OpportunityAssistanceListing(
            opportunity=opportunity,
            assistance_listing=assistance_listing,
        )
    )
    db_session.add(
        OpportunityGroupAudit(
            opportunity_group=opportunity_group,
            opportunity_audit_event=OpportunityAuditEvent.OPPORTUNITY_CREATED,
            user=user,
            opportunity=opportunity,
        )
    )
    db_session.flush()

    return opportunity
