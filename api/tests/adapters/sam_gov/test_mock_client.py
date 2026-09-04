"""Tests for the mock SAM.gov API client."""

import json
import os
import tempfile
from datetime import datetime

import pytest
import pytz

from src.adapters.sam_gov.client import SamGovError
from src.adapters.sam_gov.mock_client import MockSamGovClient
from src.adapters.sam_gov.models import (
    SamAssistanceListingData,
    SamAssistanceListingRequest,
    SamExtractRequest,
)


class TestMockSamGovClientExtracts:
    """Tests for the SAM.gov mock client."""

    def test_load_mock_data_from_file(self):
        """Test loading mock data from a file."""
        # Create a temporary file with mock extract data
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            mock_data = {
                "extracts": {
                    "TEST_EXTRACT_FILE.ZIP": {
                        "size": 1024 * 1024,  # 1MB
                        "content_type": "application/zip",
                    }
                }
            }
            json.dump(mock_data, temp_file)
            temp_file_path = temp_file.name

        # Create a temporary output file
        with tempfile.NamedTemporaryFile(delete=False) as output_file:
            output_path = output_file.name

        try:
            # Initialize client with the temp file
            client = MockSamGovClient(mock_data_file=temp_file_path)

            # Create a request for the mock extract
            request = SamExtractRequest(file_name="TEST_EXTRACT_FILE.ZIP")

            # Download the extract
            response = client.download_extract(request, output_path)

            # Verify the extract metadata
            assert response is not None
            assert response.file_name == output_path

            # Verify the file was created
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            # Clean up the temporary files
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestMockSamGovClientAssistanceListing:

    def test_get_assistance_listing_no_setup(self):
        client = MockSamGovClient()

        response = client.get_assistance_listings(SamAssistanceListingRequest())

        assert response.assistance_listings_data == []

    def verify_results(self, client, page_size, page_number, expected_assistance_listings):
        response = client.get_assistance_listings(
            SamAssistanceListingRequest(page_size=page_size, page_number=page_number)
        )

        aln_results = [d.assistance_listing_id for d in response.assistance_listings_data]

        assert aln_results == expected_assistance_listings

    def test_get_assistance_listing(self):
        client = MockSamGovClient()

        client.add_mock_assistance_listings(
            [
                SamAssistanceListingData(
                    assistanceListingId="11.111",
                    title="1st",
                    status="Active",
                    publishedDate=datetime(2020, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                ),
                SamAssistanceListingData(
                    assistanceListingId="22.222",
                    title="2nd",
                    status="Active",
                    publishedDate=datetime(2020, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                ),
                SamAssistanceListingData(
                    assistanceListingId="33.333",
                    title="3rd",
                    status="Active",
                    publishedDate=datetime(2020, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                ),
                SamAssistanceListingData(
                    assistanceListingId="44.444",
                    title="4th",
                    status="Active",
                    publishedDate=datetime(2020, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                ),
                SamAssistanceListingData(
                    assistanceListingId="55.555",
                    title="5th",
                    status="Active",
                    publishedDate=datetime(2020, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                ),
                SamAssistanceListingData(
                    assistanceListingId="66.666",
                    title="6th",
                    status="Active",
                    publishedDate=datetime(2020, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                ),
                SamAssistanceListingData(
                    assistanceListingId="77.777",
                    title="7th",
                    status="Active",
                    publishedDate=datetime(2020, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                ),
                SamAssistanceListingData(
                    assistanceListingId="88.888",
                    title="8th",
                    status="Active",
                    publishedDate=datetime(2020, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                ),
                SamAssistanceListingData(
                    assistanceListingId="99.999",
                    title="9th",
                    status="Active",
                    publishedDate=datetime(2020, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                ),
            ]
        )

        # Verify that the pagination logic in the mock works as expected for fetching
        self.verify_results(
            client,
            page_size=10,
            page_number=1,
            expected_assistance_listings=[
                "11.111",
                "22.222",
                "33.333",
                "44.444",
                "55.555",
                "66.666",
                "77.777",
                "88.888",
                "99.999",
            ],
        )
        self.verify_results(client, page_size=10, page_number=10, expected_assistance_listings=[])
        self.verify_results(
            client,
            page_size=3,
            page_number=1,
            expected_assistance_listings=["11.111", "22.222", "33.333"],
        )
        self.verify_results(
            client,
            page_size=4,
            page_number=2,
            expected_assistance_listings=["55.555", "66.666", "77.777", "88.888"],
        )
        self.verify_results(
            client, page_size=1, page_number=3, expected_assistance_listings=["33.333"]
        )
        self.verify_results(
            client,
            page_size=6,
            page_number=2,
            expected_assistance_listings=["77.777", "88.888", "99.999"],
        )

    def test_get_assistance_listing_bad_page_size(self):
        client = MockSamGovClient()

        with pytest.raises(SamGovError, match="Invalid page size or page number"):
            client.get_assistance_listings(SamAssistanceListingRequest(page_size=-1, page_number=1))

    def test_get_assistance_listing_bad_page_number(self):
        client = MockSamGovClient()

        with pytest.raises(SamGovError, match="Invalid page size or page number"):
            client.get_assistance_listings(SamAssistanceListingRequest(page_size=1, page_number=-1))
