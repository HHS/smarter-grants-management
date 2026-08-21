import logging

from sqlalchemy import text

from src.adapters import db
from src.adapters.db import flask_db
from src.task.ecs_background_task import ecs_background_task
from src.task.task_blueprint import task_blueprint

logger = logging.getLogger(__name__)


@task_blueprint.cli.command(
    "dummy-task",
    help="A dummy task we'll later delete - just needed to confirm we've set things up properly",
)
@flask_db.with_db_session()
@ecs_background_task("dummy_task")
def dummy_task(db_session: db.Session) -> None:
    logger.info("Starting dummy task")

    # Just a very basic sanity check that the DB connection works
    with db_session.begin():
        if db_session.scalar(text("SELECT 1 AS healthy")) != 1:
            raise Exception("Connection to Postgres DB failure")
