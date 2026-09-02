import uuid
from datetime import datetime

from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable


class AssistanceListing(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "assistance_listing"

    assistance_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    assistance_listing_number: Mapped[str] = mapped_column(unique=True)

    is_active: Mapped[bool]

    published_date: Mapped[datetime | None]

    program_title: Mapped[str]
