import logging
import uuid

import click
import grants_shared.logs
from grants_shared.adapters import db
from grants_shared.adapters.db import PostgresDBClient
from grants_shared.util.local import error_if_not_local

import tests.db.models.factories as f
from src.db.resource_automation.resource_automation import setup_resource_automation
from tests.lib.seed_data_utils import UserBuilder

logger = logging.getLogger(__name__)


@click.command()
def seed_local_db() -> None:
    with grants_shared.logs.init("seed_local_db"):
        logger.info("Running seed script for local DB")
        error_if_not_local()

        db_client = PostgresDBClient()

        setup_resource_automation()

        with db_client.get_session() as db_session:
            f._db_session = db_session
            run_seed_logic(db_session)


def run_seed_logic(db_session: db.Session) -> None:
    create_users(db_session)

    create_programs()

    # Commit anything remaining that wasn't made with factories
    db_session.commit()


def create_users(db_session: db.Session) -> None:
    logger.info("Creating users")

    # Create a few basic users with JWT auth setup
    UserBuilder(
        user_id=uuid.UUID("700135e1-ae1c-4ae5-a953-bc298f98ab7e"),
        db_session=db_session,
        scenario_name="Basic JWT User",
    ).with_oauth_login("basic_jwt_user").with_jwt_auth().build()

    UserBuilder(
        user_id=uuid.UUID("78cf92a5-3114-4e56-891c-04bfaf25c74f"),
        db_session=db_session,
        scenario_name="Another JWT User",
    ).with_oauth_login("another_jwt_user").with_jwt_auth().build()

    # Create users with API key auth setup
    UserBuilder(
        user_id=uuid.UUID("a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"),
        db_session=db_session,
        scenario_name="API Key User",
    ).with_oauth_login("api_key_user").with_api_key("local-dev-api-key-1").build()

    UserBuilder(
        user_id=uuid.UUID("b2c3d4e5-f6a7-4b5c-9d0e-1f2a3b4c5d6e"),
        db_session=db_session,
        scenario_name="Another API Key User",
    ).with_oauth_login("another_api_key_user").with_api_key("local-dev-api-key-2").build()

    UserBuilder(
        user_id=uuid.UUID("c3d4e5f6-a7b8-4c5d-9e0f-1a2b3c4d5e6f"),
        db_session=db_session,
        scenario_name="Opportunity User - For Simpler Grants Communication",
    ).with_oauth_login("opportunity_user").with_api_key("local-grants-mgmt-api-key").build()

def create_programs() -> None:
    # Create a few programs just to have something to work with.
    # Later work will add more specific scenarios
    logger.info("Creating programs")
    f.ProgramFactory.create_batch(size=5)
