import uuid
from datetime import datetime

from sqlalchemy import UUID, BigInteger, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.adapters.db.lookup.lookup_column import LookupColumn
from src.constants.lookup_constants import ApplicationPackageOpenToApplicant, FormFamily
from src.db.models.announcement_models import Announcement, AnnouncementAssistanceListing
from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import LkApplicationPackageOpenToApplicant, LkFormFamily


class ApplicationPackage(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "application_package"

    application_package_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Announcement.announcement_id), index=True
    )
    announcement: Mapped[Announcement] = relationship(
        Announcement, back_populates="application_packages"
    )

    public_application_package_id: Mapped[str | None]
    application_package_title: Mapped[str | None]

    opening_timestamp: Mapped[datetime | None]
    closing_timestamp: Mapped[datetime | None]
    grace_period: Mapped[int | None] = mapped_column(BigInteger)
    contact_info: Mapped[str | None]

    form_family: Mapped[FormFamily | None] = mapped_column(
        "form_family_id",
        LookupColumn(LkFormFamily),
        ForeignKey(LkFormFamily.form_family_id),
        index=True,
    )

    announcement_assistance_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey(AnnouncementAssistanceListing.announcement_assistance_listing_id)
    )
    announcement_assistance_listing: Mapped[AnnouncementAssistanceListing | None] = relationship(
        AnnouncementAssistanceListing, uselist=False
    )

    link_application_package_open_to_applicant: Mapped[
        list[LinkApplicationPackageOpenToApplicant]
    ] = relationship(
        back_populates="application_package", uselist=True, cascade="all, delete-orphan"
    )
    open_to_applicants: AssociationProxy[set[ApplicationPackageOpenToApplicant]] = (
        association_proxy(
            "link_application_package_open_to_applicant",
            "application_package_open_to_applicant",
            creator=lambda obj: LinkApplicationPackageOpenToApplicant(
                application_package_open_to_applicant=obj
            ),
        )
    )

    application_package_forms: Mapped[list[ApplicationPackageForm]] = relationship(
        back_populates="application_package", uselist=True, cascade="all, delete-orphan"
    )


class ApplicationPackageForm(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "application_package_form"

    __table_args__ = (
        UniqueConstraint("application_package_id", "form_id"),
        GrantorSchemaTable.__table_args__,
    )

    application_package_form_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    application_package_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(ApplicationPackage.application_package_id), index=True
    )
    application_package: Mapped[ApplicationPackage] = relationship(
        ApplicationPackage, back_populates="application_package_forms"
    )

    # Grants.gov uses integer form IDs. This intentionally differs from the UUID
    # carried over in the first port.
    form_id: Mapped[int] = mapped_column(Integer)
    is_required: Mapped[bool]


class LinkApplicationPackageOpenToApplicant(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_application_package_open_to_applicant"

    application_package_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(ApplicationPackage.application_package_id), primary_key=True
    )
    application_package: Mapped[ApplicationPackage] = relationship(
        ApplicationPackage, back_populates="link_application_package_open_to_applicant"
    )

    application_package_open_to_applicant: Mapped[ApplicationPackageOpenToApplicant] = (
        mapped_column(
            "application_package_open_to_applicant_id",
            LookupColumn(LkApplicationPackageOpenToApplicant),
            ForeignKey(
                LkApplicationPackageOpenToApplicant.application_package_open_to_applicant_id
            ),
            primary_key=True,
        )
    )
