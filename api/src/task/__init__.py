from src.task.task_blueprint import task_blueprint

# import any of the other files so they get initialized and attached to the blueprint
import src.task.dummy_task  # noqa: F401 isort:skip
import src.task.workflow_queue_task  # noqa: F401 isort:skip

__all__ = ["task_blueprint"]
