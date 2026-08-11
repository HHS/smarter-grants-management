from apiflask import APIBlueprint

# No HTTP routes hang off this yet - it exists so the workflow CLI commands have a
# home (`flask workflow workflow-main`). The workflow event API adds routes to it.
workflow_blueprint = APIBlueprint("workflow", __name__, enable_openapi=False, cli_group="workflow")
