import uuid

from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import Privilege
from src.db.models.grantor_organization_models import GrantorOrganization
from src.db.models.user_models import User


def get_grantor_organization(
    db_session: db.Session, grantor_organization_id: uuid.UUID
) -> GrantorOrganization:
    """Fetch a grantor organization, 404 if not found"""

    grantor_organization = db_session.execute(
        select(GrantorOrganization).where(
            GrantorOrganization.grantor_organization_id == grantor_organization_id
        )
    ).scalar_one_or_none()

    if grantor_organization is None:
        raise_flask_error(
            404, f"Could not find grantor organization with ID {grantor_organization_id}"
        )

    return grantor_organization


def get_grantor_organization_and_verify_access(
    db_session: db.Session, grantor_organization_id: uuid.UUID, user: User
) -> GrantorOrganization:
    """Fetch a grantor organization, 404 if not found, and 403 if the user doesn't have access."""

    grantor_organization = get_grantor_organization(db_session, grantor_organization_id)

    # Verify user can access the grantor organization
    AuthorizationEnforcer(db_session).verify_access(
        user=user,
        required_privileges={Privilege.VIEW_GRANTOR_ORGANIZATION},
        resource=grantor_organization,
    )

    return grantor_organization
