import uuid

from grants_shared.adapters import db

from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import MgmtPrivilege, MgmtResourceType
from src.db.models.user_models import MgmtUser
from src.services.resources.get_resource import get_resource


def check_user_can_access(
    db_session: db.Session,
    user: MgmtUser,
    resource_type: MgmtResourceType,
    resource_id: uuid.UUID,
    privileges: set[MgmtPrivilege],
) -> None:
    resource = get_resource(db_session, resource_type, resource_id)

    AuthorizationEnforcer(db_session).verify_access(
        user=user,
        required_privileges=privileges,
        resource=resource,
    )
