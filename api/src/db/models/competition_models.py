import uuid
from datetime import datetime

from sqlalchemy import UUID, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.adapters.db.lookup.lookup_column import LookupColumn
from src.constants.lookup_constants import CompetitionOpenToApplicant
from src.db.models.base import TimestampMixin
from src.db.models.file_attachment_models import FileAttachment
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import LkCompetitionOpenToApplicant
from src.db.models.opportunity_models import Opportunity, OpportunityAssistanceListing


class Competition(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "competition"

    competition_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Opportunity.opportunity_id), index=True
    )
    opportunity: Mapped[Opportunity] = relationship(Opportunity, back_populates="competitions")

    public_competition_id: Mapped[str | None]
    competition_title: Mapped[str | None]

    opening_timestamp: Mapped[datetime | None]
    closing_timestamp: Mapped[datetime | None]
    grace_period: Mapped[int | None] = mapped_column(BigInteger)
    contact_info: Mapped[str | None]

    opportunity_assistance_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey(OpportunityAssistanceListing.opportunity_assistance_listing_id)
    )
    opportunity_assistance_listing: Mapped[OpportunityAssistanceListing | None] = relationship(
        OpportunityAssistanceListing, uselist=False
    )

    link_competition_open_to_applicant: Mapped[list[LinkCompetitionOpenToApplicant]] = relationship(
        back_populates="competition", uselist=True, cascade="all, delete-orphan"
    )
    open_to_applicants: AssociationProxy[set[CompetitionOpenToApplicant]] = association_proxy(
        "link_competition_open_to_applicant",
        "competition_open_to_applicant",
        creator=lambda obj: LinkCompetitionOpenToApplicant(competition_open_to_applicant=obj),
    )

    competition_forms: Mapped[list[CompetitionForm]] = relationship(
        back_populates="competition", uselist=True, cascade="all, delete-orphan"
    )
    competition_instructions: Mapped[list[CompetitionInstruction]] = relationship(
        back_populates="competition", uselist=True, cascade="all, delete-orphan"
    )


class CompetitionForm(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "competition_form"

    __table_args__ = (
        UniqueConstraint("competition_id", "form_id"),
        GrantorSchemaTable.__table_args__,
    )

    competition_form_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    competition_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Competition.competition_id), index=True
    )
    competition: Mapped[Competition] = relationship(Competition, back_populates="competition_forms")

    form_id: Mapped[uuid.UUID] = mapped_column(UUID)
    is_required: Mapped[bool]


class LinkCompetitionOpenToApplicant(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_competition_open_to_applicant"

    competition_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Competition.competition_id), primary_key=True
    )
    competition: Mapped[Competition] = relationship(
        Competition, back_populates="link_competition_open_to_applicant"
    )

    competition_open_to_applicant: Mapped[CompetitionOpenToApplicant] = mapped_column(
        "competition_open_to_applicant_id",
        LookupColumn(LkCompetitionOpenToApplicant),
        ForeignKey(LkCompetitionOpenToApplicant.competition_open_to_applicant_id),
        primary_key=True,
    )


class CompetitionInstruction(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "competition_instruction"

    competition_instruction_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    competition_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Competition.competition_id), index=True
    )
    competition: Mapped[Competition] = relationship(
        Competition, back_populates="competition_instructions"
    )

    file_attachment_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(FileAttachment.file_attachment_id)
    )
    file_attachment: Mapped[FileAttachment] = relationship(FileAttachment)
