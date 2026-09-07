import uuid

import boto3
from sqlalchemy import select

from src.constants.lookup_constants import FileScanStatus
from src.db.models.file_upload_models import PendingFile

URL = "/v1/files"


def _get_dynamodb_item(dynamodb_client, table_name, pending_file_id):
    return dynamodb_client.get_item(
        TableName=table_name,
        Key={"file_id": {"S": str(pending_file_id)}},
    ).get("Item")


def test_create_presigned_upload_200(
    client,
    db_session,
    file_user,
    file_api_key_headers,
    mock_file_scan_s3_bucket,
    file_scan_dynamodb_table,
):
    response = client.post(
        URL,
        headers=file_api_key_headers,
        json={
            "file_name": "example.txt",
            "mime_type": "text/plain",
        },
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    pending_file_id = uuid.UUID(data["pending_file_id"])

    assert data["url"].startswith("http")
    assert data["body"]["x-amz-meta-file-id"] == str(pending_file_id)
    assert data["body"]["x-amz-meta-user-id"] == str(file_user.user_id)
    assert data["body"]["Content-Type"] == "text/plain"

    pending_file = db_session.execute(
        select(PendingFile).where(PendingFile.pending_file_id == pending_file_id)
    ).scalar_one()

    assert pending_file.user_id == file_user.user_id
    assert pending_file.file_name == "example.txt"
    assert pending_file.mime_type == "text/plain"
    assert pending_file.file_scan_status == FileScanStatus.PENDING
    assert pending_file.file_location.endswith(f"/unscanned/{pending_file_id}/example.txt")

    dynamodb_client = boto3.client("dynamodb", region_name="us-east-1")
    item = _get_dynamodb_item(
        dynamodb_client,
        file_scan_dynamodb_table,
        pending_file_id,
    )

    assert item is not None
    assert item["file_id"]["S"] == str(pending_file_id)
    assert item["user_id"]["S"] == str(file_user.user_id)
    assert item["status"]["S"] == FileScanStatus.PENDING.value


def test_create_presigned_upload_secures_file_name(
    client,
    db_session,
    file_api_key_headers,
    mock_file_scan_s3_bucket,
    file_scan_dynamodb_table,
):
    unsafe_name = "../../etc/passwd weird name.txt"

    response = client.post(
        URL,
        headers=file_api_key_headers,
        json={
            "file_name": unsafe_name,
            "mime_type": "text/plain",
        },
    )

    assert response.status_code == 200

    pending_file_id = uuid.UUID(response.get_json()["data"]["pending_file_id"])
    pending_file = db_session.execute(
        select(PendingFile).where(PendingFile.pending_file_id == pending_file_id)
    ).scalar_one()

    assert "../" not in pending_file.file_location
    assert " " not in pending_file.file_location
    assert pending_file.file_location.endswith("/passwd_weird_name.txt")
    assert pending_file.file_name == unsafe_name


def test_create_presigned_upload_missing_file_name_422(
    client,
    file_api_key_headers,
    mock_file_scan_s3_bucket,
    file_scan_dynamodb_table,
):
    response = client.post(
        URL,
        headers=file_api_key_headers,
        json={"mime_type": "text/plain"},
    )

    assert response.status_code == 422


def test_create_presigned_upload_missing_mime_type_422(
    client,
    file_api_key_headers,
    mock_file_scan_s3_bucket,
    file_scan_dynamodb_table,
):
    response = client.post(
        URL,
        headers=file_api_key_headers,
        json={"file_name": "example.txt"},
    )

    assert response.status_code == 422


def test_create_presigned_upload_file_name_too_long_422(
    client,
    file_api_key_headers,
    mock_file_scan_s3_bucket,
    file_scan_dynamodb_table,
):
    response = client.post(
        URL,
        headers=file_api_key_headers,
        json={
            "file_name": "a" * 101,
            "mime_type": "text/plain",
        },
    )

    assert response.status_code == 422


def test_create_presigned_upload_no_auth_401(
    client,
    mock_file_scan_s3_bucket,
    file_scan_dynamodb_table,
):
    response = client.post(
        URL,
        json={
            "file_name": "example.txt",
            "mime_type": "text/plain",
        },
    )

    assert response.status_code == 401
