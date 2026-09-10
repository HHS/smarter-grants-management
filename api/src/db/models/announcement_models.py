import uuid
from datetime import datetime

from sqlalchemy import UUID, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.src.db.models.application_package_models import ApplicationPackage
from src.adapters.db.lookup.lookup_column import LookupColumn
from src.constants.lookup_constants import (
    AnnouncementCategory,
    ApplicantType,
    FundingCategory,
    FundingInstrument,
    ResourceType,
)
from src.db.models.assistance_listing_models import AssistanceListing
from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import (
    LkAnnouncementCategory,
    LkApplicantType,
    LkFundingCategory,
    LkFundingInstrument,
)
from src.db.models.resource_models import AbstractResourceTableMixin, Resource


class Announcement(GrantorSchemaTable, TimestampMixin, AbstractResourceTableMixin):
    __tablename__ = "announcement"

    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Resource.resource_id), primary_key=True, default=uuid.uuid4
    )
    resource: Mapped[Resource] = relationship(
        Resource, single_parent=True, cascade="all, delete-orphan"
    )

    announcement_number: Mapped[str]
    announcement_title: Mapped[str]

    tagline: Mapped[str]
    purpose_statement: Mapped[str]

    category: Mapped[AnnouncementCategory | None] = mapped_column(
        "announcement_category_id",
        LookupColumn(LkAnnouncementCategory),
        ForeignKey(LkAnnouncementCategory.announcement_category_id),
        index=True,
    )
    category_explanation: Mapped[str | None]

    announcement_assistance_listings: Mapped[list[AnnouncementAssistanceListing]] = relationship(
        back_populates="announcement", uselist=True, cascade="all, delete-orphan"
    )
    announcement_summaries: Mapped[list[AnnouncementSummary]] = relationship(
        back_populates="announcement", uselist=True, cascade="all, delete-orphan"
    )
    application_packages: Mapped[list[ApplicationPackage]] = relationship(
        "ApplicationPackage",
        back_populates="announcement",
        uselist=True,
        cascade="all, delete-orphan",
    )

    def get_resource_id(self) -> uuid.UUID:
        return self.announcement_id

    def get_resource_type(self) -> ResourceType:
        return ResourceType.ANNOUNCEMENT

    @property
    def resource_name(self) -> str | None:
        return self.announcement_title


class AnnouncementAssistanceListing(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "announcement_assistance_listing"

    announcement_assistance_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Announcement.announcement_id), index=True
    )
    announcement: Mapped[Announcement] = relationship(
        Announcement, back_populates="announcement_assistance_listings"
    )

    assistance_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(AssistanceListing.assistance_listing_id), index=True
    )
    assistance_listing: Mapped[AssistanceListing] = relationship(AssistanceListing)


class AnnouncementSummary(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "announcement_summary"

    __table_args__ = (
        UniqueConstraint("is_forecast", "announcement_id"),
        GrantorSchemaTable.__table_args__,
    )

    announcement_summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Announcement.announcement_id), index=True
    )
    announcement: Mapped[Announcement] = relationship(
        Announcement, back_populates="announcement_summaries"
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

    # These existed as forecast-only fields in Simpler. Reviewer feedback on the first
    # port suggested making them generally usable and naming them as estimates.
    estimated_award_timestamp: Mapped[datetime | None]
    estimated_project_start_timestamp: Mapped[datetime | None]

    fiscal_year: Mapped[int | None]

    funding_category_description: Mapped[str | None]
    applicant_eligibility_description: Mapped[str | None]

    agency_contact_description: Mapped[str | None]
    agency_email_address: Mapped[str | None]
    agency_email_address_description: Mapped[str | None]

    link_funding_instruments: Mapped[list[LinkAnnouncementSummaryFundingInstrument]] = relationship(
        back_populates="announcement_summary", uselist=True, cascade="all, delete-orphan"
    )
    link_funding_categories: Mapped[list[LinkAnnouncementSummaryFundingCategory]] = relationship(
        back_populates="announcement_summary", uselist=True, cascade="all, delete-orphan"
    )
    link_applicant_types: Mapped[list[LinkAnnouncementSummaryApplicantType]] = relationship(
        back_populates="announcement_summary", uselist=True, cascade="all, delete-orphan"
    )

    funding_instruments: AssociationProxy[set[FundingInstrument]] = association_proxy(
        "link_funding_instruments",
        "funding_instrument",
        creator=lambda obj: LinkAnnouncementSummaryFundingInstrument(funding_instrument=obj),
    )
    funding_categories: AssociationProxy[set[FundingCategory]] = association_proxy(
        "link_funding_categories",
        "funding_category",
        creator=lambda obj: LinkAnnouncementSummaryFundingCategory(funding_category=obj),
    )
    applicant_types: AssociationProxy[set[ApplicantType]] = association_proxy(
        "link_applicant_types",
        "applicant_type",
        creator=lambda obj: LinkAnnouncementSummaryApplicantType(applicant_type=obj),
    )


class LinkAnnouncementSummaryFundingInstrument(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_announcement_summary_funding_instrument"

    announcement_summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey(AnnouncementSummary.announcement_summary_id),
        index=True,
        primary_key=True,
    )
    announcement_summary: Mapped[AnnouncementSummary] = relationship(
        AnnouncementSummary, back_populates="link_funding_instruments"
    )

    funding_instrument: Mapped[FundingInstrument] = mapped_column(
        "funding_instrument_id",
        LookupColumn(LkFundingInstrument),
        ForeignKey(LkFundingInstrument.funding_instrument_id),
        primary_key=True,
        index=True,
    )


class LinkAnnouncementSummaryFundingCategory(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_announcement_summary_funding_category"

    announcement_summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey(AnnouncementSummary.announcement_summary_id),
        primary_key=True,
        index=True,
    )
    announcement_summary: Mapped[AnnouncementSummary] = relationship(
        AnnouncementSummary, back_populates="link_funding_categories"
    )

    funding_category: Mapped[FundingCategory] = mapped_column(
        "funding_category_id",
        LookupColumn(LkFundingCategory),
        ForeignKey(LkFundingCategory.funding_category_id),
        primary_key=True,
        index=True,
    )


class LinkAnnouncementSummaryApplicantType(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_announcement_summary_applicant_type"

    announcement_summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey(AnnouncementSummary.announcement_summary_id),
        primary_key=True,
        index=True,
    )
    announcement_summary: Mapped[AnnouncementSummary] = relationship(
        AnnouncementSummary, back_populates="link_applicant_types"
    )

    applicant_type: Mapped[ApplicantType] = mapped_column(
        "applicant_type_id",
        LookupColumn(LkApplicantType),
        ForeignKey(LkApplicantType.applicant_type_id),
        primary_key=True,
        index=True,
    )
