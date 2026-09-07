import uuid

import pytest

from src.auth.internal_resource import get_internal_resource
from src.constants.lookup_constants import FileScanStatus, Privilege
from src.db.models.file_upload_models import PendingFile
from tests.db.models.factories import UserApiKeyFactory, UserFactory
from tests.test_utils.auth_test_utils import setup_user_with_roles


@pytest.fixture
def file_user(enable_factory_create):
    return UserFactory.create()


@pytest.fixture
def file_api_key(file_user):
    return UserApiKeyFactory.create(user=file_user)


@pytest.fixture
def file_api_key_headers(file_api_key):
    return {"X-API-Key": file_api_key.key_id}


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


@pytest.fixture
def s3_scan_api_key(
    db_session,
    enable_factory_create,
    internal_resource,
):
    resource = get_internal_resource(db_session)

    user = setup_user_with_roles(
        db_session,
        [resource],
        privileges=[Privilege.INTERNAL_S3_SCAN],
    )

    return UserApiKeyFactory.create(user=user)
