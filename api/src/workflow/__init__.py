from src.workflow.workflow_blueprint import workflow_blueprint

# import the CLI modules so their commands get attached to the blueprint
import src.workflow.cli.workflow_main  # noqa: F401 isort:skip

__all__ = ["workflow_blueprint"]
