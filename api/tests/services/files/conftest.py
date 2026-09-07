import uuid

import pytest

from src.constants.lookup_constants import FileScanStatus
from src.db.models.file_upload_models import PendingFile
from tests.db.models.factories import UserFactory


@pytest.fixture
def file_user(enable_factory_create):
    return UserFactory.create()


@pytest.fixture
def pending_file(db_session, file_user):
    pending_file = PendingFile(
        pending_file_id=uuid.uuid4(),
        user=file_user,
        file_name="example.txt",
        file_location="s3://local-mock-file-scan-bucket/unscanned/example/example.txt",
        mime_type="text/plain",
        file_scan_status=FileScanStatus.PENDING,
    )

    db_session.add(pending_file)
    db_session.commit()

    return pending_file


@pytest.fixture
def complete_pending_file(db_session, file_user):
    pending_file = PendingFile(
        pending_file_id=uuid.uuid4(),
        user=file_user,
        file_name="example.txt",
        file_location="s3://local-mock-file-scan-bucket/scanned/example/example.txt",
        mime_type="text/plain",
        file_scan_status=FileScanStatus.COMPLETE,
    )

    db_session.add(pending_file)
    db_session.commit()

    return pending_file
