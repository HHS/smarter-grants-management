import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.adapters.db.lookup.lookup_column import LookupColumn
from src.constants.lookup_constants import FileScanStatus
from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import LkFileScanStatus
from src.db.models.user_models import User


class PendingFile(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "pending_file"

    pending_file_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(User.user_id), index=True)
    user: Mapped[User] = relationship("User")

    file_name: Mapped[str]
    file_location: Mapped[str]
    mime_type: Mapped[str]

    file_scan_status: Mapped[FileScanStatus] = mapped_column(
        "file_scan_status_id",
        LookupColumn(LkFileScanStatus),
        ForeignKey(LkFileScanStatus.file_scan_status_id),
    )
