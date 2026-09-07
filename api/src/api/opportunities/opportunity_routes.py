import logging
import uuid

from src.adapters import db
from src.adapters.db import flask_db
from src.api import response
from src.api.opportunities.opportunity_blueprint import opportunity_blueprint
from src.api.opportunities.opportunity_schemas import (
    CompetitionCreateRequestSchema,
    CompetitionInstructionCreateRequestSchema,
    CompetitionInstructionDeleteResponseSchema,
    CompetitionInstructionResponseSchema,
    CompetitionResponseSchema,
    CompetitionUpdateRequestSchema,
    OpportunityAttachmentCreateRequestSchema,
    OpportunityAttachmentDeleteResponseSchema,
    OpportunityAttachmentResponseSchema,
    OpportunityCreateRequestSchema,
    OpportunityListRequestSchema,
    OpportunityListResponseSchema,
    OpportunityResponseSchema,
    OpportunitySummaryCreateRequestSchema,
    OpportunitySummaryResponseSchema,
    OpportunitySummaryUpdateRequestSchema,
    OpportunityUpdateRequestSchema,
)
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.logs.flask_logger import add_extra_data_to_current_request_logs
from src.services.opportunities.competition_instructions import (
    delete_competition_instruction,
    upload_competition_instruction,
)
from src.services.opportunities.competitions import create_competition, update_competition
from src.services.opportunities.create_opportunity import create_opportunity
from src.services.opportunities.get_opportunity import (
    get_opportunity,
    get_opportunity_and_verify_access,
)
from src.services.opportunities.list_opportunities import list_opportunities
from src.services.opportunities.opportunity_attachments import (
    create_opportunity_attachment_from_pending_file,
    delete_opportunity_attachment,
)
from src.services.opportunities.opportunity_summaries import (
    create_opportunity_summary,
    update_opportunity_summary,
)
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


@opportunity_blueprint.post("/<uuid:opportunity_id>/summaries")
@opportunity_blueprint.input(OpportunitySummaryCreateRequestSchema, location="json")
@opportunity_blueprint.output(OpportunitySummaryResponseSchema)
@opportunity_blueprint.doc(
    summary="Create an Opportunity Summary",
    responses=[200, 401, 403, 404, 422],
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def opportunity_summary_create(
    db_session: db.Session,
    opportunity_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"opportunity_id": opportunity_id})
    logger.info("POST /v1/opportunities/:opportunity_id/summaries")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        opportunity_summary = create_opportunity_summary(
            db_session,
            opportunity_id,
            json_data,
            user,
        )

    return response.ApiResponse(message="Success", data=opportunity_summary)


@opportunity_blueprint.put("/<uuid:opportunity_id>/summaries/<uuid:opportunity_summary_id>")
@opportunity_blueprint.input(OpportunitySummaryUpdateRequestSchema, location="json")
@opportunity_blueprint.output(OpportunitySummaryResponseSchema)
@opportunity_blueprint.doc(
    summary="Update an Opportunity Summary",
    responses=[200, 401, 403, 404, 422],
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def opportunity_summary_update(
    db_session: db.Session,
    opportunity_id: uuid.UUID,
    opportunity_summary_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs(
        {
            "opportunity_id": opportunity_id,
            "opportunity_summary_id": opportunity_summary_id,
        }
    )
    logger.info("PUT /v1/opportunities/:opportunity_id/summaries/:opportunity_summary_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        opportunity_summary = update_opportunity_summary(
            db_session,
            opportunity_id,
            opportunity_summary_id,
            json_data,
            user,
        )

    return response.ApiResponse(message="Success", data=opportunity_summary)


@opportunity_blueprint.post("/<uuid:opportunity_id>/attachments")
@opportunity_blueprint.input(OpportunityAttachmentCreateRequestSchema, location="json")
@opportunity_blueprint.output(OpportunityAttachmentResponseSchema)
@opportunity_blueprint.doc(
    summary="Create an Opportunity Attachment",
    responses=[200, 401, 403, 404, 422],
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def opportunity_attachment_create(
    db_session: db.Session,
    opportunity_id: uuid.UUID,
    json_data: dict,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"opportunity_id": opportunity_id})
    logger.info("POST /v1/opportunities/:opportunity_id/attachments")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)

        attachment = create_opportunity_attachment_from_pending_file(
            db_session,
            user,
            opportunity_id,
            json_data["pending_file_id"],
        )

    return response.ApiResponse(message="Success", data=attachment)


@opportunity_blueprint.delete("/<uuid:opportunity_id>/attachments/<uuid:opportunity_attachment_id>")
@opportunity_blueprint.output(OpportunityAttachmentDeleteResponseSchema)
@opportunity_blueprint.doc(
    summary="Delete an Opportunity Attachment",
    responses=[200, 401, 403, 404],
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def opportunity_attachment_delete(
    db_session: db.Session,
    opportunity_id: uuid.UUID,
    opportunity_attachment_id: uuid.UUID,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs(
        {
            "opportunity_id": opportunity_id,
            "opportunity_attachment_id": opportunity_attachment_id,
        }
    )
    logger.info("DELETE /v1/opportunities/:opportunity_id/attachments/:opportunity_attachment_id")

    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)

        delete_opportunity_attachment(
            db_session,
            user,
            opportunity_id,
            opportunity_attachment_id,
        )

    return response.ApiResponse(message="Attachment successfully deleted")


@opportunity_blueprint.post("/<uuid:opportunity_id>/competitions")
@opportunity_blueprint.input(CompetitionCreateRequestSchema, location="json")
@opportunity_blueprint.output(CompetitionResponseSchema)
@opportunity_blueprint.doc(summary="Create a Competition", responses=[200, 401, 403, 404, 422])
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def competition_create(
    db_session: db.Session, opportunity_id: uuid.UUID, json_data: dict
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs({"opportunity_id": opportunity_id})
    logger.info("POST /v1/opportunities/:opportunity_id/competitions")
    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        competition = create_competition(db_session, user, opportunity_id, json_data)
    return response.ApiResponse(message="Success", data=competition)


@opportunity_blueprint.put("/<uuid:opportunity_id>/competitions/<uuid:competition_id>")
@opportunity_blueprint.input(CompetitionUpdateRequestSchema, location="json")
@opportunity_blueprint.output(CompetitionResponseSchema)
@opportunity_blueprint.doc(summary="Update a Competition", responses=[200, 401, 403, 404, 422])
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def competition_update(
    db_session: db.Session, opportunity_id: uuid.UUID, competition_id: uuid.UUID, json_data: dict
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs(
        {"opportunity_id": opportunity_id, "competition_id": competition_id}
    )
    logger.info("PUT /v1/opportunities/:opportunity_id/competitions/:competition_id")
    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        competition = update_competition(
            db_session, user, opportunity_id, competition_id, json_data
        )
    return response.ApiResponse(message="Success", data=competition)


@opportunity_blueprint.post(
    "/<uuid:opportunity_id>/competitions/<uuid:competition_id>/instructions"
)
@opportunity_blueprint.input(CompetitionInstructionCreateRequestSchema, location="json")
@opportunity_blueprint.output(CompetitionInstructionResponseSchema)
@opportunity_blueprint.doc(
    summary="Upload a Competition Instruction", responses=[200, 401, 403, 404, 422]
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def competition_instruction_create(
    db_session: db.Session, opportunity_id: uuid.UUID, competition_id: uuid.UUID, json_data: dict
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs(
        {"opportunity_id": opportunity_id, "competition_id": competition_id}
    )
    logger.info("POST /v1/opportunities/:opportunity_id/competitions/:competition_id/instructions")
    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        instruction = upload_competition_instruction(
            db_session, user, opportunity_id, competition_id, json_data["pending_file_id"]
        )
    return response.ApiResponse(message="Success", data=instruction)


@opportunity_blueprint.delete(
    "/<uuid:opportunity_id>/competitions/<uuid:competition_id>/instructions/<uuid:competition_instruction_id>"
)
@opportunity_blueprint.output(CompetitionInstructionDeleteResponseSchema)
@opportunity_blueprint.doc(
    summary="Delete a Competition Instruction", responses=[200, 401, 403, 404]
)
@opportunity_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@flask_db.with_db_session()
def competition_instruction_delete(
    db_session: db.Session,
    opportunity_id: uuid.UUID,
    competition_id: uuid.UUID,
    competition_instruction_id: uuid.UUID,
) -> response.ApiResponse:
    add_extra_data_to_current_request_logs(
        {
            "opportunity_id": opportunity_id,
            "competition_id": competition_id,
            "competition_instruction_id": competition_instruction_id,
        }
    )
    logger.info(
        "DELETE /v1/opportunities/:opportunity_id/competitions/:competition_id/instructions/:competition_instruction_id"
    )
    with db_session.begin():
        user = jwt_or_api_user_key_multi_auth.get_user()
        db_session.add(user)
        delete_competition_instruction(
            db_session, user, opportunity_id, competition_id, competition_instruction_id
        )
    return response.ApiResponse(message="Instruction successfully deleted")
