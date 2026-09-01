"""Configuration for the Simpler Grants API client."""

from pydantic import Field

from src.util.env_config import PydanticBaseEnvConfig


class SimplerGrantsConfig(PydanticBaseEnvConfig):
    """Configuration for the Simpler Grants API client."""

    base_url: str = Field(alias="SIMPLER_GRANTS_API_BASE_URL")
    api_key: str | None = Field(default=None, alias="SIMPLER_GRANTS_API_KEY")
    timeout: int = Field(default=5, alias="SIMPLER_GRANTS_API_TIMEOUT")


def get_config() -> SimplerGrantsConfig:
    """Get the Simpler Grants API configuration from environment variables."""
    return SimplerGrantsConfig()
