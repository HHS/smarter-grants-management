import uuid

import boto3

from src.constants.lookup_constants import FileScanStatus
from tests.db.models.factories import UserApiKeyFactory

PLACEHOLDER_S3_PATH = "s3://example-bucket/scanned/abc/example.txt"


def _build_url(pending_file_id: uuid.UUID) -> str:
    return f"/v1/files/{pending_file_id}"


def _put_scanned_file(bucket: str, key: str) -> str:
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=b"scanned content",
    )
    return f"s3://{bucket}/{key}"


def test_update_file_scan_status_complete_200(
    client,
    db_session,
    pending_file,
    s3_scan_api_key,
    mock_file_scan_s3_bucket,
):
    file_location = _put_scanned_file(
        mock_file_scan_s3_bucket,
        "scanned/abc/example.txt",
    )

    response = client.post(
        _build_url(pending_file.pending_file_id),
        headers={"X-API-Key": s3_scan_api_key.key_id},
        json={
            "file_scan_status": "complete",
            "file_location": file_location,
        },
    )

    assert response.status_code == 200

    db_session.refresh(pending_file)
    assert pending_file.file_scan_status == FileScanStatus.COMPLETE
    assert pending_file.file_location == file_location


def test_update_file_scan_status_infected_200(
    client,
    db_session,
    pending_file,
    s3_scan_api_key,
    mock_file_scan_s3_bucket,
):
    pending_file.file_scan_status = FileScanStatus.IN_PROGRESS
    db_session.commit()

    file_location = _put_scanned_file(
        mock_file_scan_s3_bucket,
        "infected/abc/example.txt",
    )

    response = client.post(
        _build_url(pending_file.pending_file_id),
        headers={"X-API-Key": s3_scan_api_key.key_id},
        json={
            "file_scan_status": "infected",
            "file_location": file_location,
        },
    )

    assert response.status_code == 200

    db_session.refresh(pending_file)
    assert pending_file.file_scan_status == FileScanStatus.INFECTED
    assert pending_file.file_location == file_location


def test_update_file_scan_status_without_internal_privilege_403(
    client,
    enable_factory_create,
    pending_file,
):
    api_key = UserApiKeyFactory.create()

    response = client.post(
        _build_url(pending_file.pending_file_id),
        headers={"X-API-Key": api_key.key_id},
        json={
            "file_scan_status": "complete",
            "file_location": PLACEHOLDER_S3_PATH,
        },
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "Forbidden"


def test_update_file_scan_status_unknown_pending_file_404(
    client,
    s3_scan_api_key,
    mock_file_scan_s3_bucket,
):
    file_location = _put_scanned_file(
        mock_file_scan_s3_bucket,
        "scanned/abc/example.txt",
    )

    response = client.post(
        _build_url(uuid.uuid4()),
        headers={"X-API-Key": s3_scan_api_key.key_id},
        json={
            "file_scan_status": "complete",
            "file_location": file_location,
        },
    )

    assert response.status_code == 404


def test_update_file_scan_status_missing_file_422(
    client,
    pending_file,
    s3_scan_api_key,
    mock_file_scan_s3_bucket,
):
    missing_location = f"s3://{mock_file_scan_s3_bucket}/scanned/abc/does-not-exist.txt"

    response = client.post(
        _build_url(pending_file.pending_file_id),
        headers={"X-API-Key": s3_scan_api_key.key_id},
        json={
            "file_scan_status": "complete",
            "file_location": missing_location,
        },
    )

    assert response.status_code == 422
    assert response.get_json()["message"] == "File does not exist at the provided s3 path"


def test_update_file_scan_status_invalid_status_422(
    client,
    pending_file,
    s3_scan_api_key,
):
    response = client.post(
        _build_url(pending_file.pending_file_id),
        headers={"X-API-Key": s3_scan_api_key.key_id},
        json={
            "file_scan_status": "not_a_real_status",
            "file_location": PLACEHOLDER_S3_PATH,
        },
    )

    assert response.status_code == 422


def test_update_file_scan_status_invalid_location_422(
    client,
    pending_file,
    s3_scan_api_key,
):
    response = client.post(
        _build_url(pending_file.pending_file_id),
        headers={"X-API-Key": s3_scan_api_key.key_id},
        json={
            "file_scan_status": "complete",
            "file_location": "not-an-s3-path",
        },
    )

    assert response.status_code == 422


def test_update_file_scan_status_no_auth_401(
    client,
    pending_file,
):
    response = client.post(
        _build_url(pending_file.pending_file_id),
        json={
            "file_scan_status": "complete",
            "file_location": PLACEHOLDER_S3_PATH,
        },
    )

    assert response.status_code == 401
