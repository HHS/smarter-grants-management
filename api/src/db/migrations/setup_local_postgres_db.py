import logging

import grants_shared.adapters.db as db
import grants_shared.logs
import sqlalchemy
from grants_shared.adapters.db import PostgresDBClient
from grants_shared.util.local import error_if_not_local
from sqlalchemy import select

from src.auth.internal_resource import create_internal_resource
from src.constants.schema import Schemas
from src.db.models.user_models import User
from src.db.resource_automation.resource_automation import setup_resource_automation
from src.workflow.config.workflow_service_config import WorkflowServiceConfig

logger = logging.getLogger(__name__)


def setup_local_postgres_db() -> None:
    with grants_shared.logs.init(__package__):
        error_if_not_local()

        db_client = PostgresDBClient()

        with db_client.get_connection() as conn, conn.begin():
            for schema in Schemas:
                _create_schema(conn, schema)


def _create_schema(conn: db.Connection, schema_name: str) -> None:
    logger.info("Creating schema %s if it does not already exist", schema_name)
    conn.execute(sqlalchemy.schema.CreateSchema(schema_name, if_not_exists=True))


def setup_internal_resource() -> None:
    """Create the statically defined internal resource record for local development.

    This runs after migrations (unlike schema creation above, which must run before)
    since it needs the resource tables to exist. It always runs as part of `make init-db`
    and is idempotent, so an existing record is left untouched.
    """
    with grants_shared.logs.init(__package__):
        error_if_not_local()

        db_client = PostgresDBClient()
        setup_resource_automation()

        with db_client.get_session() as db_session, db_session.begin():
            create_internal_resource(db_session)


def setup_internal_workflow_user() -> None:
    """Create the statically defined internal workflow user for local development.

    Same shape as setup_internal_resource above - runs after migrations as part of
    `make init-db` and is idempotent. Without it, any workflow that takes an automatic
    state transition fails at commit time on the audit record's user foreign key.
    """
    with grants_shared.logs.init(__package__):
        error_if_not_local()

        db_client = PostgresDBClient()

        with db_client.get_session() as db_session, db_session.begin():
            _create_internal_workflow_user(db_session)


def _create_internal_workflow_user(db_session: db.Session) -> User:
    """Create the user that automatic (engine-driven) state transitions are audited against.

    Idempotent - if a user with the configured ID already exists, it is returned
    unchanged rather than recreated.

    The user is deliberately a plain standard user holding no roles: it exists only so
    audit rows for engine-driven transitions have a valid foreign key target, and it is
    never authenticated as or authorized against anything. Lives here rather than in
    src/workflow because creating it is only ever a local-setup concern - nothing at
    runtime needs to.
    """
    config = WorkflowServiceConfig()

    log_extra = {"user_id": config.workflow_service_internal_user_id}

    workflow_user = db_session.execute(
        select(User).where(User.user_id == config.workflow_service_internal_user_id)
    ).scalar_one_or_none()

    if workflow_user is not None:
        logger.info("Internal workflow user already exists, skipping creation", extra=log_extra)
        return workflow_user

    workflow_user = User(user_id=config.workflow_service_internal_user_id)
    db_session.add(workflow_user)

    logger.info("Created internal workflow user", extra=log_extra)
    return workflow_user
