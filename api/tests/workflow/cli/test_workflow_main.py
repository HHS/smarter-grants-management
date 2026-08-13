def test_workflow_main_command_is_registered(cli_runner):
    """`flask workflow workflow-main` is what the workflow ECS task runs.

    Asserted here because a missing blueprint registration or CLI import wouldn't
    show up anywhere else until the deployed task failed to start.
    """
    result = cli_runner.invoke(args=["workflow", "--help"])

    assert result.exit_code == 0, result.output
    assert "workflow-main" in result.output


def test_placeholder_queue_listener_command_is_gone(cli_runner):
    """The placeholder consumer the workflow manager replaced is no longer available."""
    result = cli_runner.invoke(args=["task", "--help"])

    assert result.exit_code == 0, result.output
    assert "workflow-queue-listener" not in result.output
