import uuid

import pytest
from apiflask.exceptions import HTTPError

from src.constants.lookup_constants import FileScanStatus
from src.services.files.pending_file_handling_domain_specific import (
    fetch_and_validate_scan_complete_file,
    move_pending_file_to_destination,
)
from src.util import file_util
from tests.db.models.factories import UserFactory


def test_fetch_and_validate_scan_complete_file_success(
    db_session,
    file_user,
    complete_pending_file,
):
    result = fetch_and_validate_scan_complete_file(
        db_session,
        complete_pending_file.pending_file_id,
        file_user,
    )

    assert result.pending_file_id == complete_pending_file.pending_file_id
    assert result.user_id == file_user.user_id
    assert result.file_scan_status == FileScanStatus.COMPLETE


def test_fetch_and_validate_scan_complete_file_not_found(
    db_session,
    file_user,
):
    with pytest.raises(
        HTTPError,
        check=lambda error: (
            error.status_code == 404 and error.message == "Pending file not found"
        ),
    ):
        fetch_and_validate_scan_complete_file(
            db_session,
            uuid.uuid4(),
            file_user,
        )


def test_fetch_and_validate_scan_complete_file_wrong_user(
    db_session,
    enable_factory_create,
    complete_pending_file,
):
    other_user = UserFactory.create()

    with pytest.raises(
        HTTPError,
        check=lambda error: (
            error.status_code == 403
            and error.message == "You do not have permission to access this file"
        ),
    ):
        fetch_and_validate_scan_complete_file(
            db_session,
            complete_pending_file.pending_file_id,
            other_user,
        )


def test_fetch_and_validate_scan_complete_file_not_complete(
    db_session,
    file_user,
    pending_file,
):
    with pytest.raises(
        HTTPError,
        check=lambda error: (
            error.status_code == 422
            and error.message == "File cannot be used, status must be complete"
        ),
    ):
        fetch_and_validate_scan_complete_file(
            db_session,
            pending_file.pending_file_id,
            file_user,
        )


def test_move_pending_file_to_destination_success(
    db_session,
    complete_pending_file,
    s3_config,
):
    source_location = complete_pending_file.file_location
    file_util.write_to_file(source_location, "test file content")

    destination_path = f"{s3_config.public_files_bucket_path}" "/domain_specific/example.txt"

    assert file_util.file_exists(source_location)

    move_pending_file_to_destination(
        complete_pending_file,
        destination_path,
    )
    db_session.commit()

    assert file_util.file_exists(destination_path)
    assert not file_util.file_exists(source_location)

    db_session.refresh(complete_pending_file)
    assert complete_pending_file.file_scan_status == FileScanStatus.PROCESSED
    assert complete_pending_file.file_location == destination_path


def test_move_pending_file_to_destination_failure_does_not_process(
    db_session,
    complete_pending_file,
    mock_file_scan_s3_bucket,
):
    file_util.write_to_file(
        complete_pending_file.file_location,
        "test file content",
    )

    with pytest.raises(
        Exception,
        match="Cannot download/upload between disk and S3",
    ):
        move_pending_file_to_destination(
            complete_pending_file,
            "not-an-s3-path",
        )

    db_session.refresh(complete_pending_file)
    assert complete_pending_file.file_scan_status == FileScanStatus.COMPLETE
