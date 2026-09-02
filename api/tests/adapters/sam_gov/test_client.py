"""Tests for the SAM.gov API client."""

import datetime
import os
from unittest import mock

import pytest
import requests_mock
from requests.exceptions import Timeout

from src.adapters.sam_gov.client import SamGovClient, SamGovError
from src.adapters.sam_gov.config import SamGovConfig
from src.adapters.sam_gov.models import SamAssistanceListingRequest, SamExtractRequest


class TestSamGovClient:
    """Tests for the SAM.gov API client."""

    @pytest.fixture
    def config(self):
        """Fixture to create a test configuration."""
        return SamGovConfig(
            base_url="https://test-api.sam.gov",
            api_key="test-api-key",
            timeout=5,
            extract_url=None,  # Set to None to ensure fallback to base_url/download
        )

    @pytest.fixture
    def client(self, config):
        """Fixture to create a test client."""
        return SamGovClient(config)

    @mock.patch.dict(
        os.environ,
        {
            "SAM_GOV_API_KEY": "env-api-key",
            "SAM_GOV_BASE_URL": "https://env-api.sam.gov",
        },
    )
    def test_init_with_default_config(self):
        """Test initializing the client with default configuration."""
        # Create a config and manually set the values that should come from environment
        config = SamGovConfig(api_key="env-api-key", base_url="https://env-api.sam.gov")
        client = SamGovClient(config)
        assert client.api_key == "env-api-key"
        assert client.api_url == "https://env-api.sam.gov"

    def test_init_with_custom_config(self, config):
        """Test initializing the client with custom configuration."""
        client = SamGovClient(config)
        assert client.api_key == "test-api-key"
        assert client.api_url == "https://test-api.sam.gov"

    def test_download_extract_success(self, client, config, tmp_path):
        """Test successfully downloading an extract."""

        # Sample response for the download
        file_content = b"Mock extract file content"
        file_name = "SAM_PUBLIC_MONTHLY_V2_20220406.ZIP"
        output_path = tmp_path / file_name

        request = SamExtractRequest(file_name=file_name)

        # Mock the API response, verifying the x-api-key header
        with requests_mock.Mocker() as m:
            m.get(
                f"{config.base_url}/data-services/v1/extracts?fileName={file_name}",
                request_headers={"x-api-key": config.api_key},
                content=file_content,
                headers={
                    "Content-Type": "application/zip",
                    "Content-Disposition": f'attachment; filename="{file_name}"',
                    "Content-Length": str(len(file_content)),
                },
            )

            # Call the client method
            response = client.download_extract(request, str(output_path))

            # Verify the response
            assert response is not None
            assert response.file_name == str(output_path)
            assert "x-api-key" in m.last_request.headers
            assert m.last_request.headers["x-api-key"] == config.api_key

            # Verify the file was downloaded
            with open(output_path, "rb") as f:
                assert f.read() == file_content

    def test_download_extract_not_found(self, client, config, tmp_path):
        """Test extract not found."""
        # Create the request
        file_name = "NONEXISTENT_FILE.ZIP"
        output_path = tmp_path / file_name
        request = SamExtractRequest(file_name=file_name)

        # Mock a 404 response from the API
        with requests_mock.Mocker() as m:
            m.get(
                f"{config.base_url}/data-services/v1/extracts?fileName={file_name}",
                request_headers={"x-api-key": config.api_key},
                status_code=404,
                json={"error": "File not found"},
            )

            # Call the client method, should raise an exception
            with pytest.raises(SamGovError, match="Failed to download extract: 404"):
                client.download_extract(request, str(output_path))

    def test_download_extract_http_error(self, client, config, tmp_path):
        """Test handling of HTTP errors."""
        # Create the request
        file_name = "ERROR_FILE.ZIP"
        output_path = tmp_path / file_name
        request = SamExtractRequest(file_name=file_name)

        # Mock a 500 error response from the API
        with requests_mock.Mocker() as m:
            m.get(
                f"{config.base_url}/data-services/v1/extracts?fileName={file_name}",
                request_headers={"x-api-key": config.api_key},
                status_code=500,
                json={"error": "Internal server error"},
            )

            # Call the client method, should raise an exception
            with pytest.raises(SamGovError, match="Failed to download extract: 500"):
                client.download_extract(request, output_path)

    # We skip this test because the retry logic would make it take several minutes
    # But it is left in case we want to test that the retries are working for timeouts
    @pytest.mark.skip
    def test_download_extract_timeout(self, client, config, tmp_path):
        """Test handling of timeout errors."""
        # Create the request
        file_name = "TIMEOUT_FILE.ZIP"
        output_path = tmp_path / file_name
        request = SamExtractRequest(file_name=file_name)

        # Mock a timeout by raising a Timeout exception
        with requests_mock.Mocker() as m:
            m.get(
                f"{config.base_url}/data-services/v1/extracts?fileName={file_name}",
                request_headers={"x-api-key": config.api_key},
                exc=Timeout,
            )

            # Call the client method, should raise a Timeout exception
            with pytest.raises(SamGovError, match="Request failed"):
                client.download_extract(request, str(output_path))

    def test_get_assistance_listing_success(self, client, config):

        sam_gov_response = """{
            "assistanceListingsData": [
                {"assistanceListingId": "11.111", "title": "1st", "status": "Active", "publishedDate": "2026-07-03T05:00:02.401+00:00", "otherFields": []},
                {"assistanceListingId": "22.222", "title": "2nd", "status": "Active", "publishedDate": "2026-06-03T05:00:02.401+00:00", "moreStuff": 123},
                {"assistanceListingId": "33.333", "title": "3rd", "status": "Active", "publishedDate": "2026-07-02T05:00:02.401+00:00", "ignoredThings": "hello"}
            ],
            "pageNumber": 1,
            "pageSize": 3,
            "totalPages": 4,
            "totalRecords": 11
        }"""

        with requests_mock.Mocker() as m:

            m.get(
                f"{config.base_url}/assistance-listings/v1/search?api_key={config.api_key}&pageNumber=1&pageSize=3",
                text=sam_gov_response,
            )

            response = client.get_assistance_listings(
                SamAssistanceListingRequest(page_size=3, page_number=1)
            )

            assert response.page_number == 1
            assert response.page_size == 3
            assert response.total_pages == 4
            assert response.total_records == 11

            assert len(response.assistance_listings_data) == 3

            assert response.assistance_listings_data[0].assistance_listing_id == "11.111"
            assert response.assistance_listings_data[0].title == "1st"
            assert response.assistance_listings_data[0].status == "Active"
            assert response.assistance_listings_data[0].published_date == datetime.datetime(
                2026, 7, 3, 5, 0, 2, 401000, tzinfo=datetime.timezone.utc
            )

            assert response.assistance_listings_data[1].assistance_listing_id == "22.222"
            assert response.assistance_listings_data[1].title == "2nd"
            assert response.assistance_listings_data[1].status == "Active"
            assert response.assistance_listings_data[1].published_date == datetime.datetime(
                2026, 6, 3, 5, 0, 2, 401000, tzinfo=datetime.timezone.utc
            )

            assert response.assistance_listings_data[2].assistance_listing_id == "33.333"
            assert response.assistance_listings_data[2].title == "3rd"
            assert response.assistance_listings_data[2].status == "Active"
            assert response.assistance_listings_data[2].published_date == datetime.datetime(
                2026, 7, 2, 5, 0, 2, 401000, tzinfo=datetime.timezone.utc
            )

    def test_get_assistance_listing_429(self, client, config):
        """Test handling of any 4xx errors, in this case a 429 rate limit error."""

        with requests_mock.Mocker() as m:

            m.get(
                f"{config.base_url}/assistance-listings/v1/search?api_key={config.api_key}&pageNumber=1&pageSize=3",
                status_code=429,
                json={
                    "code": "900804",
                    "message": "Message throttled out",
                    "description": "You have exceeded your quota .You can access API after 2026-Sep-03 00:00:00+0000 UTC",
                    "nextAccessTime": "2026-Sep-03 00:00:00+0000 UTC",
                },
            )

            with pytest.raises(SamGovError, match="Message throttled out"):
                client.get_assistance_listings(
                    SamAssistanceListingRequest(page_size=3, page_number=1)
                )
