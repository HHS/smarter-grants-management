"""Tests for the SAM.gov client factory."""

from unittest import mock

from src.adapters.sam_gov.client import SamGovClient
from src.adapters.sam_gov.config import SamGovConfig
from src.adapters.sam_gov.factory import MOCK_ASSISTANCE_LISTINGS, create_sam_gov_client
from src.adapters.sam_gov.mock_client import MockSamGovClient


class TestSamGovClientFactory:
    """Tests for the SAM.gov client factory."""

    def test_create_real_client(self, monkeypatch):
        """Test creating a real client."""
        monkeypatch.setenv("SAM_GOV_USE_MOCK", "false")

        # Create config directly instead of relying on environment variables
        config = SamGovConfig(
            api_key="test-api-key", base_url="https://test-api.sam.gov", use_mock=False
        )
        client = create_sam_gov_client(config=config)
        assert isinstance(client, SamGovClient)
        assert not isinstance(client, MockSamGovClient)

    def test_create_mock_client(self, monkeypatch):
        """Test creating a mock client."""
        monkeypatch.setenv("SAM_GOV_USE_MOCK", "true")
        monkeypatch.setenv("SAM_GOV_INCLUDE_MOCK_ALNS", "false")

        client = create_sam_gov_client()
        assert isinstance(client, MockSamGovClient)

        assert client.assistance_listings == []

    def test_create_client_with_config(self, monkeypatch):
        """Test creating a client with custom config."""
        monkeypatch.setenv("SAM_GOV_USE_MOCK", "false")
        monkeypatch.setenv("SAM_GOV_BASE_URL", "https://custom-api.sam.gov")
        monkeypatch.setenv("SAM_GOV_API_KEY", "custom-key")

        client = create_sam_gov_client()
        assert isinstance(client, SamGovClient)
        assert client.api_url == "https://custom-api.sam.gov"
        assert client.api_key == "custom-key"

    def test_create_mock_client_with_mock_params(self):
        """Test creating a mock client with custom mock parameters."""
        # We need to patch the MockSamGovClient._load_additional_mock_extract_data method to avoid actually trying to read the file

        with mock.patch(
            "src.adapters.sam_gov.mock_client.MockSamGovClient._load_additional_mock_extract_data",
            return_value=None,
        ) as mock_load:
            config = SamGovConfig(
                use_mock=True,
                mock_data_file="/path/to/data.json",
                mock_extract_dir="/path/to/extracts",
                include_mock_alns=True,
            )
            client = create_sam_gov_client(config=config)

            assert client.mock_extract_dir == "/path/to/extracts"
            assert client.assistance_listings == MOCK_ASSISTANCE_LISTINGS

            # Assert that the factory tried to create a MockSamGovClient with the correct parameters
            mock_load.assert_called_once_with(mock_data_file="/path/to/data.json")
