import logging
import uuid

from src.adapters import db
from src.adapters.db import flask_db
from src.api import response
from src.api.opportunities.opportunity_blueprint import opportunity_blueprint
from src.api.opportunities.opportunity_schemas import (
    OpportunityCreateRequestSchema,
    OpportunityListRequestSchema,
    OpportunityListResponseSchema,
    OpportunityResponseSchema,
    OpportunityUpdateRequestSchema,
)
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.logs.flask_logger import add_extra_data_to_current_request_logs
from src.services.opportunities.create_opportunity import create_opportunity
from src.services.opportunities.get_opportunity import (
    get_opportunity,
    get_opportunity_and_verify_access,
)
from src.services.opportunities.list_opportunities import list_opportunities
from src.services.opportunities.update_opportunity import update_opportunity

logger = logging.getLogger(__name__)


@opportunity_blueprint.post("")
@opportunity_blueprint.input(OpportunityCreateRequestSchema, location="json")
@opportunity_blueprint.output(OpportunityResponseSchema)
@opportunity_blueprint.doc(
    summary="Create an Opportunity",
    responses=[200, 401, 403, 404, 422],
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def opportunity_create(db_session: db.Session, json_data: dict) -> response.ApiResponse:
    logger.info("POST /v1/opportunities")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)

        opportunity = create_opportunity(db_session, user, json_data)
        opportunity = get_opportunity(db_session, opportunity.opportunity_id)

    return response.ApiResponse(message="Success", data=opportunity)


@opportunity_blueprint.get("/<uuid:opportunity_id>")
@opportunity_blueprint.output(OpportunityResponseSchema)
@opportunity_blueprint.doc(
    summary="Fetch an Opportunity",
    responses=[200, 401, 403, 404],
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def opportunity_get(db_session: db.Session, opportunity_id: uuid.UUID) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"opportunity_id": opportunity_id})
    logger.info("GET /v1/opportunities/:opportunity_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        opportunity = get_opportunity_and_verify_access(db_session, opportunity_id, user)

    return response.ApiResponse(message="Success", data=opportunity)


@opportunity_blueprint.put("/<uuid:opportunity_id>")
@opportunity_blueprint.input(OpportunityUpdateRequestSchema, location="json")
@opportunity_blueprint.output(OpportunityResponseSchema)
@opportunity_blueprint.doc(
    summary="Update an Opportunity",
    responses=[200, 401, 403, 404, 422],
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def opportunity_update(
    db_session: db.Session,
    opportunity_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"opportunity_id": opportunity_id})
    logger.info("PUT /v1/opportunities/:opportunity_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)

        update_opportunity(
            db_session,
            user,
            opportunity_id,
            json_data,
        )
        opportunity = get_opportunity(db_session, opportunity_id)

    return response.ApiResponse(message="Success", data=opportunity)


@opportunity_blueprint.post("/list")
@opportunity_blueprint.input(OpportunityListRequestSchema, location="json")
@opportunity_blueprint.output(OpportunityListResponseSchema)
@opportunity_blueprint.doc(
    summary="List Opportunities",
    responses=[200, 401, 403, 422],
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def opportunity_list(db_session: db.Session, json_data: dict) -> response.ApiResponse:
    logger.info("POST /v1/opportunities/list")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        opportunities, pagination_info = list_opportunities(db_session, user, json_data)

    return response.ApiResponse(
        message="Success",
        data=opportunities,
        pagination_info=pagination_info,
    )
