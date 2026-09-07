import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import OpportunityAuditEvent
from src.db.models.competition_models import Competition
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit
from src.db.models.user_models import User
from src.services.opportunities.authorization import has_access
from src.services.opportunities.get_opportunity import get_opportunity


def _audit_value(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (set, list)):
        return sorted(_audit_value(item) for item in value)
    return value


def _get_competition(
    db_session: db.Session, opportunity_id: uuid.UUID, competition_id: uuid.UUID
) -> Competition:
    competition = db_session.execute(
        select(Competition)
        .where(
            Competition.competition_id == competition_id,
            Competition.opportunity_id == opportunity_id,
        )
        .options(
            selectinload(Competition.opportunity_assistance_listing),
            selectinload(Competition.link_competition_open_to_applicant),
            selectinload(Competition.competition_forms),
            selectinload(Competition.competition_instructions),
        )
    ).scalar_one_or_none()
    if competition is None:
        raise_flask_error(
            404, f"Competition {competition_id} not found for opportunity {opportunity_id}"
        )
    return competition


def create_competition(
    db_session: db.Session, user: User, opportunity_id: uuid.UUID, competition_data: dict
) -> Competition:
    opportunity = get_opportunity(db_session, opportunity_id)
    if not has_access(user, opportunity, "update"):
        raise_flask_error(403, "User does not have access to update this opportunity")
    open_to_applicants = competition_data.pop("open_to_applicants")
    competition = Competition(opportunity=opportunity, **competition_data)
    competition.open_to_applicants = set(open_to_applicants)
    if opportunity.opportunity_assistance_listings:
        competition.opportunity_assistance_listing = opportunity.opportunity_assistance_listings[0]
    db_session.add(competition)
    db_session.flush()
    db_session.add(
        OpportunityGroupAudit(
            opportunity_group=opportunity.opportunity_group,
            opportunity_audit_event=OpportunityAuditEvent.COMPETITION_CREATED,
            user=user,
            opportunity=opportunity,
            competition=competition,
            audit_metadata={"competition_id": str(competition.competition_id)},
        )
    )
    db_session.flush()
    return _get_competition(db_session, opportunity_id, competition.competition_id)


def update_competition(
    db_session: db.Session,
    user: User,
    opportunity_id: uuid.UUID,
    competition_id: uuid.UUID,
    competition_data: dict,
) -> Competition:
    opportunity = get_opportunity(db_session, opportunity_id)
    if not has_access(user, opportunity, "update"):
        raise_flask_error(403, "User does not have access to update this opportunity")
    competition = _get_competition(db_session, opportunity_id, competition_id)
    open_to_applicants = competition_data.pop("open_to_applicants")
    audit_metadata: dict[str, dict[str, Any]] = {}
    for field_name, new_value in competition_data.items():
        old_value = getattr(competition, field_name)
        if old_value != new_value:
            audit_metadata[field_name] = {
                "before": _audit_value(old_value),
                "after": _audit_value(new_value),
            }
            setattr(competition, field_name, new_value)
    old_open = set(competition.open_to_applicants)
    new_open = set(open_to_applicants)
    if old_open != new_open:
        audit_metadata["open_to_applicants"] = {
            "before": _audit_value(old_open),
            "after": _audit_value(new_open),
        }
        competition.open_to_applicants = new_open
    if audit_metadata:
        db_session.add(
            OpportunityGroupAudit(
                opportunity_group=opportunity.opportunity_group,
                opportunity_audit_event=OpportunityAuditEvent.COMPETITION_UPDATED,
                user=user,
                opportunity=opportunity,
                competition=competition,
                audit_metadata=audit_metadata,
            )
        )
    db_session.flush()
    return _get_competition(db_session, opportunity_id, competition_id)
