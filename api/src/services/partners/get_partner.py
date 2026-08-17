import uuid

from grants_shared.adapters import db
from grants_shared.api.route_utils import raise_flask_error
from sqlalchemy import select

from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import Privilege
from src.db.models.grantor_organization_models import Partner
from src.db.models.user_models import User


def get_partner(db_session: db.Session, partner_id: uuid.UUID) -> Partner:
    """Fetch a partner, 404 if not found"""

    partner = db_session.execute(
        select(Partner).where(Partner.partner_id == partner_id)
    ).scalar_one_or_none()

    if partner is None:
        raise_flask_error(404, f"Could not find partner with ID {partner_id}")

    return partner


def get_partner_and_verify_access(
    db_session: db.Session, partner_id: uuid.UUID, user: User
) -> Partner:
    """Fetch a partner, 404 if not found, and 403 if the user doesn't have access."""

    partner = get_partner(db_session, partner_id)

    # Verify user can access the partner
    AuthorizationEnforcer(db_session).verify_access(
        user=user, required_privileges={Privilege.VIEW_PARTNER}, resource=partner
    )

    return partner
