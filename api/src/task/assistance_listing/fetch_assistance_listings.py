import logging
from enum import StrEnum

from sqlalchemy import select

from src.adapters import db
from src.adapters.db import flask_db
from src.adapters.sam_gov import create_sam_gov_client, SamGovClient
from src.adapters.sam_gov.models import SamAssistanceListingRequest, SamAssistanceListingData
from src.constants.lookup_constants import JobType
from src.task.ecs_background_task import ecs_background_task
from src.task.task import Task
from src.task.task_blueprint import task_blueprint

logger = logging.getLogger(__name__)


@task_blueprint.cli.command(
    "fetch-assistance-listings",
    help="Task to fetch assistance listings from sam.gov and store into our DB",
)
@flask_db.with_db_session()
@ecs_background_task(JobType.FETCH_ASSISTANCE_LISTING)
def fetch_assistance_listings(db_session: db.Session) -> None:
    FetchAssistanceListingsTask(db_session).run()


class FetchAssistanceListingsTask(Task):

    class Metrics(StrEnum):
        FETCHED_ASSISTANCE_LISTINGS = "fetched_assistance_listings"

        NEW_ASSISTANCE_LISTINGS = "new_assistance_listings"
        UPDATED_ASSISTANCE_LISTINGS = "updated_assistance_listings"
        INACTIVE_ASSISTANCE_LISTINGS = "inactive_assistance_listings"

    def __init__(self, db_session: db.Session, client: SamGovClient | None = None):
        super().__init__(db_session)

        # Use the passed in client, or create one.
        self.client = client if client else create_sam_gov_client()

    def run_task(self) -> None:

        with self.db_session.begin():
            sam_assistance_listings = self.fetch_assistance_listings()
            self.sync_assistance_listings(sam_assistance_listings)

    def fetch_assistance_listings(self) -> list[SamAssistanceListingData]:

        # TODO - move this to a config
        PAGE_SIZE = 100
        MAX_PAGE_NUMBER = 100

        all_assistance_listings = []

        for page_number in range(1, MAX_PAGE_NUMBER):
            logger.info("Fetching assistance listings", extra={"page_number": page_number})
            request = SamAssistanceListingRequest(page_size=PAGE_SIZE, page_number=page_number)
            response = self.client.get_assistance_listings(request)

            assistance_listings = response.assistance_listings_data
            logger.info("Fetched assistance listing records", extra={"page_number": page_number, "count": len(assistance_listings)})
            all_assistance_listings.extend(assistance_listings)

            # If we're on the last page, stop processing.
            if response.page_number >= response.total_pages:
                logger.info("Reached last page", extra={"page_number": page_number, "count": len(assistance_listings)})
                break

        if page_number >= MAX_PAGE_NUMBER:
            logger.error("TODO - something here")

        logger.info("Finished fetching assistance listings from sam.gov")
        self.increment(self.Metrics.FETCHED_ASSISTANCE_LISTINGS, len(all_assistance_listings))
        return all_assistance_listings

    def sync_assistance_listings(self, sam_assistance_listings: list[SamAssistanceListingData]) -> None:
        fetched_assistance_listing_map = {aln.assistance_listing_id: aln for aln in sam_assistance_listings}

        existing_assistance_listing_map = self.get_existing_assistance_listings()

        # Iterate over all ALN values across both the fetched and DB values
        # We'll handle the behavior of having it in one or both within this loop.
        for assistance_listing_number in fetched_assistance_listing_map.keys() | existing_assistance_listing_map.keys():
            log_extra = {"assistance_listing_number": assistance_listing_number}
            logger.info("Syncing assistance listing number", extra=log_extra)

            # TODO - add these to the log_extra as well
            fetched_aln = fetched_assistance_listing_map[assistance_listing_number]
            existing_aln = existing_assistance_listing_map[assistance_listing_number]

            # Update
            if fetched_aln and existing_aln:
                logger.info("Updating existing assistance listing", extra=log_extra)
                self.increment(self.Metrics.UPDATED_ASSISTANCE_LISTINGS)
                pass

            # Insert
            if fetched_aln and not existing_aln:
                logger.info("Creating new assistance listing", extra=log_extra)
                self.increment(self.Metrics.NEW_ASSISTANCE_LISTINGS)
                aln = AssistanceListing() # TODO
                self.db_session.add(aln)

            # Didn't fetch it, which means it's inactive
            if not fetched_aln and existing_aln:
                logger.info("Assistance listing not returned by sam.gov, assuming it is no longer active", extra=log_extra)
                self.increment(self.Metrics.INACTIVE_ASSISTANCE_LISTINGS)
                existing_aln.is_active = False



    def get_existing_assistance_listings(self) -> dict[str, AssistanceListing]:

        assistance_listings = self.db_session.execute(select(AssistanceListing)).scalars()

        assistance_listing_map = {}
        for assistance_listing in assistance_listings:
            assistance_listing_map[assistance_listing.assistance_listing_number] = assistance_listing

        return assistance_listing_map