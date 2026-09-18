import logging

from src.api import response
from src.api.forms.form_blueprint import form_blueprint
from src.api.forms.form_schemas import FormListResponseSchema
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.services.forms.list_forms import list_forms

logger = logging.getLogger(__name__)


@form_blueprint.post("/list")
@form_blueprint.output(FormListResponseSchema)
@form_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
def forms_list() -> response.ApiResponse:
    logger.info("POST /v1/forms/list")

    forms = list_forms()

    return response.ApiResponse(message="Success", data=forms)
