import uuid

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import OpportunityAuditEvent
from src.db.models.opportunity_group_audit_models import OpportunityGroupAudit
from src.db.models.opportunity_models import Opportunity
from src.db.models.user_models import User
from src.services.opportunities.authorization import has_access
from src.services.opportunities.get_opportunity import get_opportunity


def update_opportunity(
    db_session: db.Session,
    user: User,
    opportunity_id: uuid.UUID,
    json_data: dict,
) -> Opportunity:
    opportunity = get_opportunity(db_session, opportunity_id)

    if not has_access(user, opportunity, "update"):
        raise_flask_error(403, "User does not have access to update this opportunity")

    audit_metadata: dict[str, dict[str, object]] = {}

    for field_name in (
        "opportunity_title",
        "tagline",
        "purpose_statement",
        "category",
        "category_explanation",
    ):
        if field_name not in json_data:
            continue

        old_value = getattr(opportunity, field_name)
        new_value = json_data[field_name]
        if old_value != new_value:
            audit_metadata[field_name] = {
                "before": old_value,
                "after": new_value,
            }
            setattr(opportunity, field_name, new_value)

    if audit_metadata:
        db_session.add(
            OpportunityGroupAudit(
                opportunity_group=opportunity.opportunity_group,
                opportunity_audit_event=OpportunityAuditEvent.OPPORTUNITY_UPDATED,
                user=user,
                opportunity=opportunity,
                audit_metadata=audit_metadata,
            )
        )

    db_session.flush()
    return opportunity
