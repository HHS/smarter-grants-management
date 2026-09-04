"""Configuration for SAM.gov API client."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from src.util.env_config import PydanticBaseEnvConfig


class SamGovConfig(PydanticBaseEnvConfig):
    """Configuration for SAM.gov API client."""

    model_config = SettingsConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    base_url: str = Field(default="https://api.sam.gov/", alias="SAM_GOV_BASE_URL")
    api_key: str | None = Field(default=None, alias="SAM_GOV_API_KEY")
    timeout: int = Field(default=30, alias="SAM_GOV_API_TIMEOUT")  # Timeout in seconds

    # Mock configuration (only used locally for testing)
    use_mock: bool = Field(default=False, alias="SAM_GOV_USE_MOCK")
    mock_data_file: str | None = Field(default=None, alias="SAM_GOV_MOCK_DATA_FILE")
    mock_extract_dir: str | None = Field(default=None, alias="SAM_GOV_MOCK_EXTRACT_DIR")

    # Whether to include a few default mock ALNs in the data from sam.gov when using
    # the mock client. If not using the mock client, is unused.
    include_mock_alns: bool = Field(default=False, alias="SAM_GOV_INCLUDE_MOCK_ALNS")


def get_config() -> SamGovConfig:
    """Get the SAM.gov configuration from environment variables."""
    return SamGovConfig()
