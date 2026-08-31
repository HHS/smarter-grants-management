import uuid

from sqlalchemy import UUID, FetchedValue, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.adapters.db.lookup.lookup_column import LookupColumn
from src.adapters.db.ltree_column import Ltree, LtreeType
from src.constants.lookup_constants import (
    GrantorOrganizationAuditEvent,
    GrantorOrganizationType,
    PartnerAuditEvent,
    ResourceType,
)
from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import (
    LkGrantorOrganizationAuditEvent,
    LkGrantorOrganizationType,
    LkPartnerAuditEvent,
)
from src.db.models.resource_models import AbstractResourceTableMixin, Resource
from src.db.models.user_models import User


class Partner(GrantorSchemaTable, TimestampMixin, AbstractResourceTableMixin):
    __tablename__ = "partner"

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Resource.resource_id), primary_key=True, default=uuid.uuid4
    )
    resource: Mapped[Resource] = relationship(
        Resource, single_parent=True, cascade="all, delete-orphan"
    )

    partner_name: Mapped[str]

    programs: Mapped[list[Program]] = relationship(back_populates="partner", uselist=True)

    organizations: Mapped[list[GrantorOrganization]] = relationship(
        back_populates="partner", uselist=True
    )

    def get_resource_id(self) -> uuid.UUID:
        return self.partner_id

    def get_resource_type(self) -> ResourceType:
        return ResourceType.PARTNER

    @property
    def resource_name(self) -> str | None:
        return self.partner_name


class GrantorOrganization(GrantorSchemaTable, TimestampMixin, AbstractResourceTableMixin):
    __tablename__ = "grantor_organization"

    grantor_organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Resource.resource_id), primary_key=True, default=uuid.uuid4
    )
    resource: Mapped[Resource] = relationship(
        Resource, single_parent=True, cascade="all, delete-orphan"
    )

    organization_name: Mapped[str]

    partner_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(Partner.partner_id), index=True)
    partner: Mapped[Partner] = relationship(Partner)

    parent_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey(grantor_organization_id), index=True
    )
    parent_organization: Mapped[GrantorOrganization | None] = relationship(
        lambda: GrantorOrganization, remote_side=[grantor_organization_id]
    )

    grantor_organization_type: Mapped[GrantorOrganizationType] = mapped_column(
        "grantor_organization_type_id",
        LookupColumn(LkGrantorOrganizationType),
        ForeignKey(LkGrantorOrganizationType.grantor_organization_type_id),
    )

    path: Mapped[Ltree] = mapped_column(
        LtreeType, index=True, server_default=FetchedValue(), server_onupdate=FetchedValue()
    )

    def get_resource_id(self) -> uuid.UUID:
        return self.grantor_organization_id

    def get_resource_type(self) -> ResourceType:
        return ResourceType.GRANTOR_ORGANIZATION

    @property
    def resource_name(self) -> str | None:
        return self.organization_name


class Program(GrantorSchemaTable, TimestampMixin, AbstractResourceTableMixin):
    __tablename__ = "program"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Resource.resource_id), primary_key=True, default=uuid.uuid4
    )
    resource: Mapped[Resource] = relationship(
        Resource, single_parent=True, cascade="all, delete-orphan"
    )

    program_name: Mapped[str]

    partner_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(Partner.partner_id), index=True)
    partner: Mapped[Partner] = relationship(Partner)

    program_office_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(GrantorOrganization.grantor_organization_id), index=True
    )
    program_office: Mapped[GrantorOrganization] = relationship(
        GrantorOrganization, foreign_keys=[program_office_id]
    )

    grant_office_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(GrantorOrganization.grantor_organization_id), index=True
    )
    grant_office: Mapped[GrantorOrganization] = relationship(
        GrantorOrganization, foreign_keys=[grant_office_id]
    )

    link_secondary_program_partners: Mapped[list[SecondaryProgramPartner]] = relationship(
        back_populates="program", uselist=True
    )

    @property
    def secondary_program_partners(self) -> list[Partner]:
        return [spp.partner for spp in self.link_secondary_program_partners]

    def get_resource_id(self) -> uuid.UUID:
        return self.program_id

    def get_resource_type(self) -> ResourceType:
        return ResourceType.PROGRAM

    @property
    def resource_name(self) -> str | None:
        return self.program_name


class SecondaryProgramPartner(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "secondary_program_partner"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Program.program_id), primary_key=True
    )
    program: Mapped[Program] = relationship(Program)

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Partner.partner_id), primary_key=True
    )
    partner: Mapped[Partner] = relationship(Partner)


class PartnerAudit(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "partner_audit"

    partner_audit_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    partner_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(Partner.partner_id))
    partner: Mapped[Partner] = relationship(Partner)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(User.user_id))
    user: Mapped[User] = relationship(User, foreign_keys=[user_id])

    partner_audit_event: Mapped[PartnerAuditEvent] = mapped_column(
        "partner_audit_event_id",
        LookupColumn(LkPartnerAuditEvent),
        ForeignKey(LkPartnerAuditEvent.partner_audit_event_id),
    )

    target_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey(User.user_id))
    target_user: Mapped[User | None] = relationship(User, foreign_keys=[target_user_id])

    audit_metadata: Mapped[dict | None] = mapped_column(JSONB)


class GrantorOrganizationAudit(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "grantor_organization_audit"

    grantor_organization_audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    grantor_organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(GrantorOrganization.grantor_organization_id)
    )
    grantor_organization: Mapped[GrantorOrganization] = relationship(GrantorOrganization)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(User.user_id))
    user: Mapped[User] = relationship(User, foreign_keys=[user_id])

    grantor_organization_audit_event: Mapped[GrantorOrganizationAuditEvent] = mapped_column(
        "grantor_organization_audit_event_id",
        LookupColumn(LkGrantorOrganizationAuditEvent),
        ForeignKey(LkGrantorOrganizationAuditEvent.grantor_organization_audit_event_id),
    )

    target_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey(User.user_id))
    target_user: Mapped[User | None] = relationship(User, foreign_keys=[target_user_id])

    audit_metadata: Mapped[dict | None] = mapped_column(JSONB)
