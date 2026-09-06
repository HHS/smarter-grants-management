import uuid
from datetime import datetime

from sqlalchemy import UUID, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.adapters.db.lookup.lookup_column import LookupColumn
from src.constants.lookup_constants import (
    ApplicantType,
    FundingCategory,
    FundingInstrument,
    OpportunityCategory,
    ResourceType,
)
from src.db.models.assistance_listing_models import AssistanceListing
from src.db.models.base import TimestampMixin
from src.db.models.file_attachment_models import FileAttachment
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import (
    LkApplicantType,
    LkFundingCategory,
    LkFundingInstrument,
    LkOpportunityCategory,
)
from src.db.models.resource_models import AbstractResourceTableMixin, Resource


class OpportunityGroup(GrantorSchemaTable, TimestampMixin, AbstractResourceTableMixin):
    __tablename__ = "opportunity_group"

    opportunity_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Resource.resource_id), primary_key=True, default=uuid.uuid4
    )
    resource: Mapped[Resource] = relationship(
        Resource, single_parent=True, cascade="all, delete-orphan"
    )

    opportunities: Mapped[list[Opportunity]] = relationship(
        back_populates="opportunity_group", uselist=True
    )

    def get_resource_id(self) -> uuid.UUID:
        return self.opportunity_group_id

    def get_resource_type(self) -> ResourceType:
        return ResourceType.OPPORTUNITY_GROUP


class Opportunity(GrantorSchemaTable, TimestampMixin, AbstractResourceTableMixin):
    __tablename__ = "opportunity"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Resource.resource_id), primary_key=True, default=uuid.uuid4
    )
    resource: Mapped[Resource] = relationship(
        Resource, single_parent=True, cascade="all, delete-orphan"
    )

    opportunity_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(OpportunityGroup.opportunity_group_id), index=True
    )
    opportunity_group: Mapped[OpportunityGroup] = relationship(
        OpportunityGroup, back_populates="opportunities"
    )

    opportunity_number: Mapped[str]
    opportunity_title: Mapped[str]

    tagline: Mapped[str]
    purpose_statement: Mapped[str]

    category: Mapped[OpportunityCategory | None] = mapped_column(
        "opportunity_category_id",
        LookupColumn(LkOpportunityCategory),
        ForeignKey(LkOpportunityCategory.opportunity_category_id),
        index=True,
    )
    category_explanation: Mapped[str | None]

    opportunity_assistance_listings: Mapped[list[OpportunityAssistanceListing]] = relationship(
        back_populates="opportunity", uselist=True, cascade="all, delete-orphan"
    )
    opportunity_summaries: Mapped[list[OpportunitySummary]] = relationship(
        back_populates="opportunity", uselist=True, cascade="all, delete-orphan"
    )
    opportunity_attachments: Mapped[list[OpportunityAttachment]] = relationship(
        back_populates="opportunity", uselist=True, cascade="all, delete-orphan"
    )

    def get_resource_id(self) -> uuid.UUID:
        return self.opportunity_id

    def get_resource_type(self) -> ResourceType:
        return ResourceType.OPPORTUNITY

    @property
    def resource_name(self) -> str | None:
        return self.opportunity_title


class OpportunityAssistanceListing(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "opportunity_assistance_listing"

    opportunity_assistance_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Opportunity.opportunity_id), index=True
    )
    opportunity: Mapped[Opportunity] = relationship(
        Opportunity, back_populates="opportunity_assistance_listings"
    )

    assistance_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(AssistanceListing.assistance_listing_id), index=True
    )
    assistance_listing: Mapped[AssistanceListing] = relationship(AssistanceListing)



class OpportunityAttachment(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "opportunity_attachment"

    opportunity_attachment_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Opportunity.opportunity_id), index=True
    )
    opportunity: Mapped[Opportunity] = relationship(
        Opportunity, back_populates="opportunity_attachments"
    )

    file_attachment_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(FileAttachment.file_attachment_id), index=True
    )
    file_attachment: Mapped[FileAttachment] = relationship(FileAttachment)


class OpportunitySummary(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "opportunity_summary"

    __table_args__ = (
        UniqueConstraint("is_forecast", "opportunity_id"),
        GrantorSchemaTable.__table_args__,
    )

    opportunity_summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Opportunity.opportunity_id), index=True
    )
    opportunity: Mapped[Opportunity] = relationship(
        Opportunity, back_populates="opportunity_summaries"
    )

    summary_description: Mapped[str]

    is_cost_sharing: Mapped[bool]
    is_forecast: Mapped[bool]

    post_timestamp: Mapped[datetime]
    close_timestamp: Mapped[datetime | None]
    close_timestamp_description: Mapped[str | None]
    archive_timestamp: Mapped[datetime | None]

    expected_number_of_awards: Mapped[int | None] = mapped_column(BigInteger)
    estimated_total_program_funding: Mapped[int | None] = mapped_column(BigInteger)
    award_floor: Mapped[int | None] = mapped_column(BigInteger)
    award_ceiling: Mapped[int | None] = mapped_column(BigInteger)

    additional_info_url: Mapped[str | None]
    additional_info_url_description: Mapped[str | None]

    forecasted_post_timestamp: Mapped[datetime | None]
    forecasted_close_timestamp: Mapped[datetime | None]
    forecasted_close_timestamp_description: Mapped[str | None]
    forecasted_award_timestamp: Mapped[datetime | None]
    forecasted_project_start_timestamp: Mapped[datetime | None]
    fiscal_year: Mapped[int | None]

    funding_category_description: Mapped[str | None]
    applicant_eligibility_description: Mapped[str | None]

    agency_contact_description: Mapped[str | None]
    agency_email_address: Mapped[str | None]
    agency_email_address_description: Mapped[str | None]

    link_funding_instruments: Mapped[list[LinkOpportunitySummaryFundingInstrument]] = relationship(
        back_populates="opportunity_summary", uselist=True, cascade="all, delete-orphan"
    )
    link_funding_categories: Mapped[list[LinkOpportunitySummaryFundingCategory]] = relationship(
        back_populates="opportunity_summary", uselist=True, cascade="all, delete-orphan"
    )
    link_applicant_types: Mapped[list[LinkOpportunitySummaryApplicantType]] = relationship(
        back_populates="opportunity_summary", uselist=True, cascade="all, delete-orphan"
    )

    funding_instruments: AssociationProxy[set[FundingInstrument]] = association_proxy(
        "link_funding_instruments",
        "funding_instrument",
        creator=lambda obj: LinkOpportunitySummaryFundingInstrument(funding_instrument=obj),
    )
    funding_categories: AssociationProxy[set[FundingCategory]] = association_proxy(
        "link_funding_categories",
        "funding_category",
        creator=lambda obj: LinkOpportunitySummaryFundingCategory(funding_category=obj),
    )
    applicant_types: AssociationProxy[set[ApplicantType]] = association_proxy(
        "link_applicant_types",
        "applicant_type",
        creator=lambda obj: LinkOpportunitySummaryApplicantType(applicant_type=obj),
    )


class LinkOpportunitySummaryFundingInstrument(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_opportunity_summary_funding_instrument"

    opportunity_summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(OpportunitySummary.opportunity_summary_id), index=True, primary_key=True
    )
    opportunity_summary: Mapped[OpportunitySummary] = relationship(
        OpportunitySummary, back_populates="link_funding_instruments"
    )

    funding_instrument: Mapped[FundingInstrument] = mapped_column(
        "funding_instrument_id",
        LookupColumn(LkFundingInstrument),
        ForeignKey(LkFundingInstrument.funding_instrument_id),
        primary_key=True,
        index=True,
    )


class LinkOpportunitySummaryFundingCategory(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_opportunity_summary_funding_category"

    opportunity_summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(OpportunitySummary.opportunity_summary_id), primary_key=True, index=True
    )
    opportunity_summary: Mapped[OpportunitySummary] = relationship(
        OpportunitySummary, back_populates="link_funding_categories"
    )

    funding_category: Mapped[FundingCategory] = mapped_column(
        "funding_category_id",
        LookupColumn(LkFundingCategory),
        ForeignKey(LkFundingCategory.funding_category_id),
        primary_key=True,
        index=True,
    )


class LinkOpportunitySummaryApplicantType(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_opportunity_summary_applicant_type"

    opportunity_summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(OpportunitySummary.opportunity_summary_id), primary_key=True, index=True
    )
    opportunity_summary: Mapped[OpportunitySummary] = relationship(
        OpportunitySummary, back_populates="link_applicant_types"
    )

    applicant_type: Mapped[ApplicantType] = mapped_column(
        "applicant_type_id",
        LookupColumn(LkApplicantType),
        ForeignKey(LkApplicantType.applicant_type_id),
        primary_key=True,
        index=True,
    )
