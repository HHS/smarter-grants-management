import uuid

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.adapters.db.lookup.lookup_column import LookupColumn
from src.constants.lookup_constants import OpportunityCategory, ResourceType
from src.db.models.assistance_listing_models import AssistanceListing
from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import LkOpportunityCategory
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
