import uuid

from src.adapters.db.lookup.lookup_column import LookupColumn
from src.constants.lookup_constants import JobStatus
from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.lookup_models import LkJobStatus


class JobLog(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "job_log"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    job_type: Mapped[str]
    job_status: Mapped[JobStatus] = mapped_column(
        "job_status_id",
        LookupColumn(LkJobStatus),
        ForeignKey(LkJobStatus.job_status_id),
    )
    metrics: Mapped[dict | None] = mapped_column(JSONB)