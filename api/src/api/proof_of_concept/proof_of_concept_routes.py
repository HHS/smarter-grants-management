import logging
from uuid import UUID

from grants_shared.adapters import db
from grants_shared.adapters.db import flask_db
from grants_shared.api import response
from grants_shared.logs.flask_logger import add_extra_data_to_current_request_logs

from src.api.proof_of_concept.proof_of_concept_blueprint import proof_of_concept_blueprint
from src.api.proof_of_concept.proof_of_concept_schemas import OpportunityGetResponseSchema
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.services.proof_of_concept_simpler_data.get_opportunity_simpler_min import (
    get_opportunity_simpler_min,
)

logger = logging.getLogger(__name__)


@proof_of_concept_blueprint.get("/opportunities/<uuid:opportunity_id>")
@proof_of_concept_blueprint.output(OpportunityGetResponseSchema)
@proof_of_concept_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@proof_of_concept_blueprint.doc(
    description="Fetch an opportunity from Simpler Grants as a proof-of-concept of cross-service data transfer. This endpoint requires JWT or API key authentication but has no authorization enforcement.",
    responses={
        200: "Successfully retrieved opportunity from Simpler Grants",
        401: "Authentication required",
        404: "Opportunity not found in Simpler Grants",
    },
)
@flask_db.with_db_session()
def opportunity_get_simpler_min(
    db_session: db.Session, opportunity_id: UUID
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"opportunity_id": opportunity_id})
    logger.info(
        "GET /alpha/proof_of_concept/opportunities/:opportunity_id",
    )

    with db_session.begin():
        opportunity_data_min = get_opportunity_simpler_min(db_session, opportunity_id)

    return response.ApiResponse(message="Success", data=opportunity_data_min)
