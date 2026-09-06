import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.competition_models import Competition, CompetitionInstruction
from src.db.models.opportunity_models import (
    Opportunity,
    OpportunityAssistanceListing,
    OpportunityAttachment,
    OpportunitySummary,
)
from src.db.models.user_models import User
from src.services.opportunities.authorization import has_access


def opportunity_response_options() -> tuple[ORMOption, ...]:
    return (
        selectinload(Opportunity.opportunity_group),
        selectinload(Opportunity.opportunity_assistance_listings).selectinload(
            OpportunityAssistanceListing.assistance_listing
        ),
        selectinload(Opportunity.opportunity_summaries).selectinload(
            OpportunitySummary.link_funding_instruments
        ),
        selectinload(Opportunity.opportunity_summaries).selectinload(
            OpportunitySummary.link_funding_categories
        ),
        selectinload(Opportunity.opportunity_summaries).selectinload(
            OpportunitySummary.link_applicant_types
        ),
        selectinload(Opportunity.opportunity_attachments).selectinload(
            OpportunityAttachment.file_attachment
        ),
        selectinload(Opportunity.competitions).selectinload(
            Competition.link_competition_open_to_applicant
        ),
        selectinload(Opportunity.competitions).selectinload(Competition.competition_forms),
        selectinload(Opportunity.competitions)
        .selectinload(Competition.competition_instructions)
        .selectinload(CompetitionInstruction.file_attachment),
    )


def get_opportunity(db_session: db.Session, opportunity_id: uuid.UUID) -> Opportunity:
    opportunity = db_session.execute(
        select(Opportunity)
        .where(Opportunity.opportunity_id == opportunity_id)
        .options(*opportunity_response_options())
    ).scalar_one_or_none()

    if opportunity is None:
        raise_flask_error(404, f"Could not find opportunity with ID {opportunity_id}")

    return opportunity


def get_opportunity_and_verify_access(
    db_session: db.Session, opportunity_id: uuid.UUID, user: User
) -> Opportunity:
    opportunity = get_opportunity(db_session, opportunity_id)

    if not has_access(user, opportunity, "view"):
        raise_flask_error(403, "User does not have access to this opportunity")

    return opportunity
