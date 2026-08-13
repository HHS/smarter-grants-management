import logging
import uuid

from grants_shared.adapters import db
from grants_shared.util.env_config import PydanticBaseEnvConfig
from pydantic import Field
from sqlalchemy import select

from src.db.models.resource_models import InternalResource

logger = logging.getLogger(__name__)

INTERNAL_RESOURCE_NAME = "Internal"


class InternalResourceConfig(PydanticBaseEnvConfig):
    # The primary key of the statically defined internal resource record. The field is
    # required and the config is instantiated lazily (only when the internal resource is needed).
    internal_resource_id: uuid.UUID = Field(alias="INTERNAL_RESOURCE_ID")


def get_internal_resource(db_session: db.Session) -> InternalResource:
    """Fetch the statically defined internal resource record.

    Internal roles are checked against this singular resource rather than a null
    resource. This makes internal roles work the same as any other role in that they
    are always checked against a particular resource. Use it like::

        verify_access(user, {Privilege.XYZ}, get_internal_resource(db_session))
    """
    config = InternalResourceConfig()

    internal_resource = db_session.execute(
        select(InternalResource).where(
            InternalResource.internal_resource_id == config.internal_resource_id
        )
    ).scalar_one_or_none()

    if internal_resource is None:
        raise ValueError(
            f"Internal resource {config.internal_resource_id} does not exist - it must be created before it can be used"
        )

    return internal_resource


def create_internal_resource(db_session: db.Session) -> InternalResource:
    """Create the statically defined internal resource record if it does not already exist.

    This is idempotent - if a record with the configured ID already exists, it is returned
    unchanged rather than recreated. Requires resource automation to be set up so the backing
    ``resource`` row is created alongside it.
    """
    config = InternalResourceConfig()

    log_extra = {"internal_resource_id": config.internal_resource_id}

    internal_resource = db_session.execute(
        select(InternalResource).where(
            InternalResource.internal_resource_id == config.internal_resource_id
        )
    ).scalar_one_or_none()

    if internal_resource is not None:
        logger.info("Internal resource already exists, skipping creation", extra=log_extra)
        return internal_resource

    internal_resource = InternalResource(
        internal_resource_id=config.internal_resource_id,
        internal_resource_name=INTERNAL_RESOURCE_NAME,
    )
    db_session.add(internal_resource)

    logger.info("Created internal resource", extra=log_extra)
    return internal_resource
