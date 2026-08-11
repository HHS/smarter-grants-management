import logging

from grants_shared.adapters import db
from sqlalchemy import select

from src.db.models.user_models import MgmtUser
from src.workflow.config.workflow_service_config import WorkflowServiceConfig

logger = logging.getLogger(__name__)


def create_internal_workflow_user(db_session: db.Session) -> MgmtUser:
    """Create the statically defined user that automatic state transitions are audited against.

    This is idempotent - if a user with the configured ID already exists, it is returned
    unchanged rather than recreated.

    The user is deliberately a plain standard user holding no roles: in v1 it exists
    only so audit rows for engine-driven transitions have a valid FK target, and it is
    never authenticated as or authorized against anything.
    """
    config = WorkflowServiceConfig()

    log_extra = {"mgmt_user_id": config.workflow_service_internal_user_id}

    workflow_user = db_session.execute(
        select(MgmtUser).where(MgmtUser.mgmt_user_id == config.workflow_service_internal_user_id)
    ).scalar_one_or_none()

    if workflow_user is not None:
        logger.info("Internal workflow user already exists, skipping creation", extra=log_extra)
        return workflow_user

    workflow_user = MgmtUser(mgmt_user_id=config.workflow_service_internal_user_id)
    db_session.add(workflow_user)

    logger.info("Created internal workflow user", extra=log_extra)
    return workflow_user
