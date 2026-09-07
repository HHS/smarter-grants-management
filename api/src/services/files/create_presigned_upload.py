import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from pydantic import Field
from sqlalchemy import func, select

from src.adapters import db
from src.adapters.aws import S3Config
from src.adapters.aws.dynamodb_adapter import DynamoDBClient, DynamoDBConfig
from src.api.route_utils import raise_flask_error
from src.constants.lookup_constants import FileScanStatus
from src.db.models.file_upload_models import PendingFile
from src.db.models.user_models import User
from src.util import datetime_util, file_util
from src.util.env_config import PydanticBaseEnvConfig

logger = logging.getLogger(__name__)


class PresignedUploadConfig(PydanticBaseEnvConfig):
    pending_file_upload_rate_window_hours: int = Field(
        default=1,
        alias="PENDING_FILE_UPLOAD_RATE_WINDOW_HOURS",
    )
    pending_file_upload_rate_limit: int = Field(
        default=100,
        alias="PENDING_FILE_UPLOAD_RATE_LIMIT",
    )


@dataclass(frozen=True)
class PresignedUploadResult:
    pending_file_id: uuid.UUID
    url: str
    body: dict[str, Any]


class GrantsManagementPresignFileUploadService:
    def __init__(
        self,
        db_session: db.Session,
        s3_config: S3Config | None = None,
        dynamodb_client: DynamoDBClient | None = None,
        dynamodb_config: DynamoDBConfig | None = None,
        config: PresignedUploadConfig | None = None,
    ):
        self.db_session = db_session
        self.s3_config = s3_config or S3Config()
        self.dynamodb_client = dynamodb_client or DynamoDBClient()
        self.dynamodb_config = dynamodb_config or DynamoDBConfig()
        self.config = config or PresignedUploadConfig()

    def create_presigned_upload(
        self,
        user: User,
        file_name: str,
        mime_type: str,
    ) -> PresignedUploadResult:
        self._validate_user_can_presign(user)

        secure_file_name = file_util.get_secure_file_name(file_name)
        pending_file_id = uuid.uuid4()
        s3_file_location = file_util.join(
            self.s3_config.file_scan_bucket_path,
            "unscanned",
            str(pending_file_id),
            secure_file_name,
        )

        pending_file = PendingFile(
            pending_file_id=pending_file_id,
            user=user,
            file_name=file_name,
            file_location=s3_file_location,
            mime_type=mime_type,
            file_scan_status=FileScanStatus.PENDING,
        )
        self.db_session.add(pending_file)

        presigned = file_util.pre_sign_upload(
            file_path=s3_file_location,
            content_type=mime_type,
            metadata={
                "file-id": str(pending_file_id),
                "user-id": str(user.get_user_id()),
            },
            s3_config=self.s3_config,
        )

        self.dynamodb_client.put_item(
            table_name=self.dynamodb_config.file_scan_cache_table_name,
            item={
                "file_id": {"S": str(pending_file_id)},
                "user_id": {"S": str(user.get_user_id())},
                "status": {"S": FileScanStatus.PENDING.value},
            },
        )

        logger.info(
            "Created presigned upload for pending file",
            extra={
                "pending_file_id": pending_file_id,
                "user_id": user.user_id,
                "file_scan_status": FileScanStatus.PENDING,
            },
        )

        return PresignedUploadResult(
            pending_file_id=pending_file_id,
            url=presigned["url"],
            body=presigned["fields"],
        )

    def _validate_user_can_presign(self, user: User) -> None:
        cutoff = datetime_util.utcnow() - timedelta(
            hours=self.config.pending_file_upload_rate_window_hours
        )
        recent_count = self.db_session.execute(
            select(func.count())
            .select_from(PendingFile)
            .where(
                PendingFile.user_id == user.user_id,
                PendingFile.created_at >= cutoff,
            )
        ).scalar_one()

        if recent_count >= self.config.pending_file_upload_rate_limit:
            logger.info(
                "User exceeded pending file upload rate limit",
                extra={
                    "user_id": user.user_id,
                    "recent_pending_file_count": recent_count,
                    "pending_file_upload_rate_limit": self.config.pending_file_upload_rate_limit,
                    "pending_file_upload_rate_window_hours": (
                        self.config.pending_file_upload_rate_window_hours
                    ),
                },
            )
            raise_flask_error(429, message="Too many pending file uploads")
