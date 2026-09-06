import uuid

from sqlalchemy import UUID, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable


class FileAttachment(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "file_attachment"

    file_attachment_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    file_location: Mapped[str]
    file_name: Mapped[str]
    mime_type: Mapped[str]
    file_description: Mapped[str | None]
    file_size_bytes: Mapped[int] = mapped_column(BigInteger)
