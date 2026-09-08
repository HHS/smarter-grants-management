"""Factory for creating SAM.gov clients."""

import logging
from datetime import datetime

import pytz

from src.adapters.sam_gov.client import BaseSamGovClient, SamGovClient
from src.adapters.sam_gov.config import SamGovConfig
from src.adapters.sam_gov.mock_client import MockSamGovClient
from src.adapters.sam_gov.models import SamAssistanceListingData

logger = logging.getLogger(__name__)

MOCK_ASSISTANCE_LISTINGS = [
    SamAssistanceListingData(
        assistanceListingId="10.207",
        title="Animal Health and Disease Research",
        status="Active",
        publishedDate=datetime(2026, 7, 30, 12, 0, 0, tzinfo=pytz.utc),
    ),
    SamAssistanceListingData(
        assistanceListingId="43.007",
        title="Space Operations",
        status="Active",
        publishedDate=datetime(2010, 11, 1, 11, 33, 22, tzinfo=pytz.utc),
    ),
    SamAssistanceListingData(
        assistanceListingId="11.011",
        title="Ocean Exploration",
        status="Active",
        publishedDate=datetime(2009, 10, 19, 6, 11, 33, tzinfo=pytz.utc),
    ),
    SamAssistanceListingData(
        assistanceListingId="10.976",
        title="Rice Production Program",
        status="Active",
        publishedDate=datetime(2023, 5, 23, 17, 33, 56, tzinfo=pytz.utc),
    ),
    SamAssistanceListingData(
        assistanceListingId="93.NR1",
        title="Nursing Research - Research Projects",
        status="Active",
        publishedDate=datetime(2026, 1, 30, 12, 0, 0, tzinfo=pytz.utc),
    ),
]


def create_sam_gov_client(
    config: SamGovConfig | None = None,
) -> BaseSamGovClient:
    """
    Create a SAM.gov API client based on provided parameters.

    Args:
        config: Optional SamGovConfig object to use for configuration.
               If not provided, configuration will be loaded from environment variables.

    Returns:
        A SAM.gov API client instance
    """
    # If config is provided, use that, otherwise load from environment
    sam_config = config if config else SamGovConfig()

    # Use mock client if use_mock is True in the config
    if sam_config.use_mock:
        logger.info("Using mocked sam.gov client")
        client = MockSamGovClient(
            mock_data_file=sam_config.mock_data_file,
            mock_extract_dir=sam_config.mock_extract_dir,
        )

        # Include a few default ALNs.
        if sam_config.include_mock_alns:
            client.add_mock_assistance_listings(MOCK_ASSISTANCE_LISTINGS)

        return client

    # Otherwise use the real client
    logger.info("Using real sam.gov client")
    return SamGovClient(sam_config)
