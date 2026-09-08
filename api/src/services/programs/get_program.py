import uuid

from sqlalchemy import select

from src.adapters import db
from src.api.route_utils import raise_flask_error
from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import Privilege
from src.db.models.grantor_organization_models import Program
from src.db.models.user_models import User


def get_program(db_session: db.Session, program_id: uuid.UUID) -> Program:
    """Fetch a program, 404 if not found"""

    program = db_session.execute(
        select(Program).where(Program.program_id == program_id)
    ).scalar_one_or_none()

    if program is None:
        raise_flask_error(404, f"Could not find program with ID {program_id}")

    return program


def get_program_and_verify_access(
    db_session: db.Session, program_id: uuid.UUID, user: User
) -> Program:
    """Fetch a program, 404 if not found, and 403 if the user doesn't have access."""

    program = get_program(db_session, program_id)

    # Verify user can access the program
    AuthorizationEnforcer(db_session).verify_access(
        user=user, required_privileges={Privilege.VIEW_PROGRAM}, resource=program
    )

    return program
