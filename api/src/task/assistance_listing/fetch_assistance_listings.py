import logging

from src.adapters.sam_gov import create_sam_gov_client
from src.adapters.sam_gov.models import SamAssistanceListingRequest
from src.constants.lookup_constants import JobType
from src.task.ecs_background_task import ecs_background_task
from src.task.task_blueprint import task_blueprint

logger = logging.getLogger(__name__)


@task_blueprint.cli.command(
    "fetch-assistance-listings",
    help="Task to fetch assistance listings from sam.gov and store into our DB",
)
@ecs_background_task(JobType.FETCH_ASSISTANCE_LISTING)
def fetch_assistance_listings() -> None:

    # NOTE - this doesn't yet include the logic to write to the DB
    # just has logic to fetch the data to verify it works with real sam.gov
    client = create_sam_gov_client()

    # Just fetch a few for the proof of concept
    result = client.get_assistance_listings(SamAssistanceListingRequest(page_size=5))
    logger.info(result)
