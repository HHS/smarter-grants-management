import logging
from uuid import UUID

from grants_shared.api import response
from grants_shared.api.route_utils import raise_flask_error

from src.adapters.simpler_grants import client as simpler_grants_client_module
from src.adapters.simpler_grants.client import BaseSimplerGrantsClient, SimplerResponseException
from src.adapters.simpler_grants.config import get_config
from src.api.proof_of_concept.proof_of_concept_blueprint import proof_of_concept_blueprint
from src.api.proof_of_concept.proof_of_concept_schemas import OpportunityGetResponseSchema
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth

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
        500: "Error communicating with Simpler Grants",
    },
)
def get_opportunity(opportunity_id: UUID) -> response.ApiResponse:
    logger.info(
        "GET /alpha/proof_of_concept/opportunities/:opportunity_id",
        extra={"opportunity_id": str(opportunity_id)},
    )

    config = get_config()
    client: BaseSimplerGrantsClient = simpler_grants_client_module.SimplerGrantsClient(config)

    try:
        simpler_response = client.get_opportunity(opportunity_id)

        return response.ApiResponse(
            message="Success",
            status_code=200,
            data={
                "opportunity_id": simpler_response.data.opportunity_id,
                "opportunity_title": simpler_response.data.opportunity_title,
                "opportunity_status": simpler_response.data.opportunity_status,
                "summary": (
                    {"post_date": simpler_response.data.summary.post_date}
                    if simpler_response.data.summary
                    else None
                ),
            },
        )

    except SimplerResponseException as e:
        logger.error(
            "Error fetching opportunity from Simpler Grants",
            extra={
                "opportunity_id": str(opportunity_id),
                "status_code": e.simpler_response_error.status_code,
                "error_message": e.simpler_response_error.message,
            },
        )
        raise_flask_error(
            e.simpler_response_error.status_code,
            e.simpler_response_error.message,
        )

    except Exception:
        logger.exception(
            "Unexpected error fetching opportunity from Simpler Grants",
            extra={"opportunity_id": str(opportunity_id)},
        )
        raise_flask_error(500, "An unexpected error occurred while fetching the opportunity")
