from uuid import UUID

from grants_shared.adapters import db

from src.adapters.simpler_grants import client as simpler_grants_client_module
from src.adapters.simpler_grants.client import BaseSimplerGrantsClient
from src.adapters.simpler_grants.config import get_config


def get_opportunity_simpler_min(db_session: db.Session, opportunity_id: UUID) -> dict:
    config = get_config()
    client: BaseSimplerGrantsClient = simpler_grants_client_module.SimplerGrantsClient(config)

    simpler_response = client.get_opportunity(opportunity_id)

    return {
        "opportunity_id": simpler_response.data.opportunity_id,
        "opportunity_title": simpler_response.data.opportunity_title,
        "opportunity_status": simpler_response.data.opportunity_status,
        "summary": (
            {"post_date": simpler_response.data.summary.post_date}
            if simpler_response.data.summary
            else None
        ),
    }
