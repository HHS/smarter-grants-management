import uuid
from datetime import datetime

from sqlalchemy import UUID, Column, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable


class AssistanceListing(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "assistance_listing"

    __table_args__ = (
        # Add a GIN index that stores the program title as a tsvector for better querying
        # This will render like:
        #
        #  create index ix_v_assistance_listing_program_title on grantor.assistance_listing USING GIN (to_tsvector('english', program_title))
        Index(
            "ix_v_assistance_listing_program_title",
            func.to_tsvector(text("'english'"), Column("program_title")),
            postgresql_using="GIN",
        ),
        GrantorSchemaTable.__table_args__,
    )

    assistance_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    assistance_listing_number: Mapped[str] = mapped_column(unique=True)

    is_active: Mapped[bool]

    published_date: Mapped[datetime | None]

    program_title: Mapped[str]
