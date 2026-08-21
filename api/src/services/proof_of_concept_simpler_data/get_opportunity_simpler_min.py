import logging
from uuid import UUID

from src.adapters import db
from src.adapters.simpler_grants import client as simpler_grants_client_module
from src.adapters.simpler_grants.client import BaseSimplerGrantsClient, SimplerResponseException
from src.adapters.simpler_grants.config import get_config
from src.adapters.simpler_grants.models import SimplerOpportunity
from src.api.route_utils import raise_flask_error

logger = logging.getLogger(__name__)


def get_opportunity_simpler_min(db_session: db.Session, opportunity_id: UUID) -> SimplerOpportunity:
    config = get_config()
    client: BaseSimplerGrantsClient = simpler_grants_client_module.SimplerGrantsClient(config)

    try:
        simpler_response = client.get_opportunity(opportunity_id)
    except SimplerResponseException as e:
        if e.simpler_response_error.status_code == 404:
            raise_flask_error(404, e.simpler_response_error.message)

        logger.exception("Failed to call Simpler Grants API for opportunity")
        raise

    return simpler_response.data
