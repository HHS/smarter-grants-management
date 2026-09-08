import logging
from enum import StrEnum
from typing import Any

from pydantic import Field
from sqlalchemy import select

from src.adapters import db
from src.adapters.db import flask_db
from src.adapters.sam_gov import BaseSamGovClient, create_sam_gov_client
from src.adapters.sam_gov.models import SamAssistanceListingData, SamAssistanceListingRequest
from src.constants.lookup_constants import JobType
from src.db.models.assistance_listing_models import AssistanceListing
from src.task.ecs_background_task import ecs_background_task
from src.task.task import Task
from src.task.task_blueprint import task_blueprint
from src.util.env_config import PydanticBaseEnvConfig

logger = logging.getLogger(__name__)


@task_blueprint.cli.command(
    "fetch-assistance-listings",
    help="Task to fetch assistance listings from sam.gov and store into our DB",
)
@flask_db.with_db_session()
@ecs_background_task(JobType.FETCH_ASSISTANCE_LISTING)
def fetch_assistance_listings(db_session: db.Session) -> None:
    FetchAssistanceListingsTask(db_session).run()


class FetchAssistanceListingConfig(PydanticBaseEnvConfig):

    page_size: int = Field(100, alias="FETCH_ASSISTANCE_LISTING_PAGE_SIZE")
    max_page_number: int = Field(100, alias="FETCH_ASSISTANCE_LISTING_MAX_PAGE_NUMBER")


class FetchAssistanceListingsTask(Task):
    """
    Task that fetches assistance listings from sam.gov
    and that syncs them to our assistance listing table.
    """

    class Metrics(StrEnum):
        FETCHED_ASSISTANCE_LISTINGS = "fetched_assistance_listings"

        PAGES_FETCHED = "pages_fetched"

        NEW_ASSISTANCE_LISTINGS = "new_assistance_listings"
        UPDATED_ASSISTANCE_LISTINGS = "updated_assistance_listings"
        INACTIVE_ASSISTANCE_LISTINGS = "inactive_assistance_listings"

        TOTAL_ASSISTANCE_LISTINGS = "total_assistance_listings"

    def __init__(
        self,
        db_session: db.Session,
        client: BaseSamGovClient | None = None,
        config: FetchAssistanceListingConfig | None = None,
    ):
        super().__init__(db_session)

        # Use the passed in client, or create one.
        self.client = client if client else create_sam_gov_client()

        if config is None:
            config = FetchAssistanceListingConfig()

        self.config = config

    def run_task(self) -> None:

        with self.db_session.begin():
            sam_assistance_listings = self.fetch_assistance_listings()
            self.sync_assistance_listings(sam_assistance_listings)

    def fetch_assistance_listings(self) -> list[SamAssistanceListingData]:
        """Fetch all assistance listing records from sam.gov, paginating over the results."""

        all_assistance_listings = []

        # Fetch results from sam.gov until we've received all ALN records
        # We have a max page number as a safety net against infinite looping if there is a bug
        # with the logic or sam.gov
        for page_number in range(1, self.config.max_page_number + 1):
            logger.info("Fetching assistance listings", extra={"page_number": page_number})
            request = SamAssistanceListingRequest(
                page_size=self.config.page_size, page_number=page_number
            )
            response = self.client.get_assistance_listings(request)

            assistance_listings = response.assistance_listings_data
            logger.info(
                "Fetched assistance listing records",
                extra={"page_number": page_number, "count": len(assistance_listings)},
            )
            all_assistance_listings.extend(assistance_listings)

            # If we're on the last page, stop processing.
            if response.page_number >= response.total_pages:
                logger.info(
                    "Reached last page",
                    extra={"page_number": page_number, "count": len(assistance_listings)},
                )
                break

        self.increment(self.Metrics.PAGES_FETCHED, page_number)

        if page_number >= self.config.max_page_number:
            raise ValueError(
                "Fetched more than the configured number of pages - exiting in case the loop is stuck."
            )

        logger.info("Finished fetching assistance listings from sam.gov")
        self.increment(self.Metrics.FETCHED_ASSISTANCE_LISTINGS, len(all_assistance_listings))
        return all_assistance_listings

    def sync_assistance_listings(
        self, sam_assistance_listings: list[SamAssistanceListingData]
    ) -> None:
        """Sync assistance listings to the database, inserting, or updating from sam.gov data."""

        # Create a map of ALN data from sam.gov to zip it together with our DB data.
        fetched_assistance_listing_map = {
            aln.assistance_listing_id: aln for aln in sam_assistance_listings
        }

        existing_assistance_listing_map = self.get_existing_assistance_listings()

        # Iterate over all ALN values across both the fetched and DB values
        # We'll handle the behavior of having it in one or both within this loop.
        all_assistance_listing_numbers = (
            fetched_assistance_listing_map.keys() | existing_assistance_listing_map.keys()
        )
        self.increment(self.Metrics.TOTAL_ASSISTANCE_LISTINGS, len(all_assistance_listing_numbers))

        for assistance_listing_number in all_assistance_listing_numbers:
            fetched_aln = fetched_assistance_listing_map.get(assistance_listing_number, None)
            existing_aln = existing_assistance_listing_map.get(assistance_listing_number, None)

            log_extra: dict[str, Any] = {"assistance_listing_number": assistance_listing_number}
            if fetched_aln:
                log_extra |= {
                    "fetched_program_title": fetched_aln.title,
                    "fetched_status": fetched_aln.status,
                    "fetched_published_date": fetched_aln.published_date,
                }

            if existing_aln:
                log_extra |= {
                    "existing_program_title": existing_aln.program_title,
                    "existing_is_active": existing_aln.is_active,
                    "existing_published_date": existing_aln.published_date,
                }

            logger.info("Syncing assistance listing number", extra=log_extra)

            # Update
            if fetched_aln and existing_aln:
                logger.info("Updating existing assistance listing", extra=log_extra)
                self.increment(self.Metrics.UPDATED_ASSISTANCE_LISTINGS)

                existing_aln.is_active = fetched_aln.status == "Active"
                existing_aln.published_date = fetched_aln.published_date
                existing_aln.program_title = fetched_aln.title

            # Insert
            if fetched_aln and not existing_aln:
                logger.info("Creating new assistance listing", extra=log_extra)
                self.increment(self.Metrics.NEW_ASSISTANCE_LISTINGS)
                aln = AssistanceListing(
                    assistance_listing_number=assistance_listing_number,
                    is_active=fetched_aln.status == "Active",
                    published_date=fetched_aln.published_date,
                    program_title=fetched_aln.title,
                )
                self.db_session.add(aln)

            # Didn't fetch it, which means it's inactive
            if not fetched_aln and existing_aln:
                logger.info(
                    "Assistance listing not returned by sam.gov, assuming it is no longer active",
                    extra=log_extra,
                )
                self.increment(self.Metrics.INACTIVE_ASSISTANCE_LISTINGS)
                existing_aln.is_active = False

    def get_existing_assistance_listings(self) -> dict[str, AssistanceListing]:

        assistance_listings = self.db_session.execute(select(AssistanceListing)).scalars()

        assistance_listing_map = {}
        for assistance_listing in assistance_listings:
            assistance_listing_map[assistance_listing.assistance_listing_number] = (
                assistance_listing
            )

        return assistance_listing_map
