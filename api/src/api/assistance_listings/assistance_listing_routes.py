import logging

from src.adapters import db
from src.adapters.db import flask_db
from src.api import response
from src.api.assistance_listings.assistance_listing_blueprint import assistance_listing_blueprint
from src.api.assistance_listings.assistance_listing_schemas import (
    AssistanceListingSearchRequestSchema,
    AssistanceListingSearchResponseSchema,
)
from src.auth.multi_auth import jwt_or_api_user_key_multi_auth
from src.logs.flask_logger import add_extra_data_to_current_request_logs
from src.services.assistance_listings.search_assistance_listings import search_assistance_listings
from src.util.dict_util import flatten_dict

logger = logging.getLogger(__name__)

ALN_SEARCH_DESCRIPTION = """
The query parameter of this endpoint supports a few basic search operations which
query against the assistance listing number and program title.

For querying against the assistance listing number, it automatically handles prefixing,
and searching for `12.` will return all assistance listings that begin with '12.'.

For querying against the program title, there are a few options you have for querying:

* `chemistry` will search for program titles with the word chemistry
* `chem*` will search for words that begin with 'chem' including chemistry and chemical
* `chemistry disease` will search for program titles that contain both words
* `chemistry OR disease` will search for program titles that contain either word
* `-chemistry` will search for program titles that don't contain chemistry

These can be mix and matched like:
* `chem* -act` which will get everything that starts with chem but doesn't contain act
"""


@assistance_listing_blueprint.post("/search")
@assistance_listing_blueprint.input(AssistanceListingSearchRequestSchema)
@assistance_listing_blueprint.output(AssistanceListingSearchResponseSchema)
@assistance_listing_blueprint.auth_required(jwt_or_api_user_key_multi_auth)
@assistance_listing_blueprint.doc(description=ALN_SEARCH_DESCRIPTION, responses=[200, 401])
@flask_db.with_db_session()
def assistance_listing_search(db_session: db.Session, json_data: dict) -> response.ApiResponse:
    add_extra_data_to_current_request_logs(flatten_dict(json_data, prefix="request.body"))
    logger.info("POST /v1/assistance-listings/search")

    with db_session.begin():
        assistance_listings, pagination_info = search_assistance_listings(db_session, json_data)

    return response.ApiResponse(
        message="Success", data=assistance_listings, pagination_info=pagination_info
    )
