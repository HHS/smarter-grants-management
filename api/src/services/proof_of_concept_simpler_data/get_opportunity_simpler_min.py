from uuid import UUID

from grants_shared.adapters import db

from src.adapters.simpler_grants import client as simpler_grants_client_module
from src.adapters.simpler_grants.client import BaseSimplerGrantsClient
from src.adapters.simpler_grants.config import get_config
from src.adapters.simpler_grants.models import SimplerOpportunity


def get_opportunity_simpler_min(db_session: db.Session, opportunity_id: UUID) -> SimplerOpportunity:
    config = get_config()
    client: BaseSimplerGrantsClient = simpler_grants_client_module.SimplerGrantsClient(config)

    simpler_response = client.get_opportunity(opportunity_id)

    return simpler_response.data
