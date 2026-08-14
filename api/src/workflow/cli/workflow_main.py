from src.workflow.manager.workflow_manager import WorkflowManager
from src.workflow.workflow_background_task import workflow_background_task
from src.workflow.workflow_blueprint import workflow_blueprint

# Importing the state machine package registers every state machine against the
# WorkflowRegistry, which is what the event handler resolves workflow types through.
import src.workflow.state_machine  # ruff: ignore[unused-import] isort:skip


@workflow_blueprint.cli.command("workflow-main")
@workflow_background_task()
def workflow_main() -> None:
    """Main entry-point of the workflow management."""
    WorkflowManager().run()
