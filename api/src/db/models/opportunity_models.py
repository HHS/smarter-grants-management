from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable

if TYPE_CHECKING:
    from src.db.models.announcement_models import Announcement


class Opportunity(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "opportunity"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    # Temporary stand-in for agency / partner until those concepts are settled
    partner_code: Mapped[str]

    announcements: Mapped[list[Announcement]] = relationship(
        "Announcement", back_populates="opportunity", uselist=True
    )
