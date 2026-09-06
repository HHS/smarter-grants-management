import uuid

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.adapters.db.lookup.lookup_column import LookupColumn
from src.constants.lookup_constants import OpportunityAuditEvent
from src.db.models.base import TimestampMixin
from src.db.models.competition_models import Competition
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import LkOpportunityAuditEvent
from src.db.models.opportunity_models import Opportunity, OpportunityGroup, OpportunitySummary
from src.db.models.user_models import User


class OpportunityGroupAudit(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "opportunity_group_audit"

    opportunity_group_audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    opportunity_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(OpportunityGroup.opportunity_group_id), index=True
    )
    opportunity_group: Mapped[OpportunityGroup] = relationship(OpportunityGroup)

    opportunity_audit_event: Mapped[OpportunityAuditEvent] = mapped_column(
        "opportunity_audit_event_id",
        LookupColumn(LkOpportunityAuditEvent),
        ForeignKey(LkOpportunityAuditEvent.opportunity_audit_event_id),
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(User.user_id), index=True)
    user: Mapped[User] = relationship(User)

    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey(Opportunity.opportunity_id)
    )
    opportunity: Mapped[Opportunity | None] = relationship(Opportunity)

    opportunity_summary_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey(OpportunitySummary.opportunity_summary_id)
    )
    opportunity_summary: Mapped[OpportunitySummary | None] = relationship(OpportunitySummary)

    competition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey(Competition.competition_id)
    )
    competition: Mapped[Competition | None] = relationship(Competition)

    audit_metadata: Mapped[dict | None] = mapped_column(JSONB)
