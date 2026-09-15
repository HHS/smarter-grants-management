from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.db.models.assistance_listing_models import AssistanceListing


def get_assistance_listing(db_session: db.Session, assist_list_nbr: str) -> AssistanceListing:
    stmt = (
        select(AssistanceListing)
        .where(AssistanceListing.assistance_listing_number == assist_list_nbr)
        .where(AssistanceListing.is_active.is_(True))
    )
    record = db_session.execute(stmt).scalar_one_or_none()

    if record is None:
        raise_flask_error(
            404, message=f"Could not find Assistance Listing Number {assist_list_nbr}"
        )

    return record
