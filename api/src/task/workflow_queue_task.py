import logging
import signal
import sys
import threading
from enum import StrEnum
from types import FrameType

from grants_shared.adapters.aws import SQSConfig
from grants_shared.adapters.aws.sqs_adapter import SQSClient, SQSMessage
from grants_shared.api.maintenance_mode import is_maintenance_mode_enabled
from grants_shared.util.env_config import PydanticBaseEnvConfig

from src.task.task_blueprint import task_blueprint
from src.task.workflow_background_task import workflow_background_task

logger = logging.getLogger(__name__)


class WorkflowQueueListenerLogEvent(StrEnum):
    """Distinct, queryable event types for workflow queue listener log records."""

    MAINTENANCE_MODE_SKIP = "maintenance_mode_workflow_processing_skipped"


class WorkflowQueueListenerConfig(PydanticBaseEnvConfig):

    # How long each poll waits for messages to show up, in seconds.
    workflow_cycle_duration: int = 10  # WORKFLOW_CYCLE_DURATION

    # How many batches to poll before exiting.
    # Only used for testing, we have no limit
    # under ordinary circumstances.
    workflow_maximum_batch_count: int | None = None  # WORKFLOW_MAXIMUM_BATCH_COUNT


class WorkflowQueueListener:
    """A placeholder consumer for the workflow queue.

    This exists so the local loop (something puts a message on the queue ->
    a background task picks it up) works before any workflow code is copied
    over, which lets each subsequent piece be tested locally as it lands.

    It does not process anything - it logs what arrives and deletes it so the
    queue drains. The workflow manager copied from simpler-grants-gov replaces
    this outright, at which point this module goes away.
    """

    def __init__(self, config: WorkflowQueueListenerConfig | None = None):
        if config is None:
            config = WorkflowQueueListenerConfig()
        self.config = config

        self.sqs_config = SQSConfig()
        self.sqs_client = SQSClient(queue_url=self.sqs_config.workflow_queue_url)

        self.sigterm_received = False
        # Set when a shutdown signal is received so the maintenance-mode idle loop
        # can wake immediately rather than waiting out a full sleep interval.
        self._shutdown_event = threading.Event()
        self._register_signal_handlers()

    def _register_signal_handlers(self) -> None:
        """Shut down between batches rather than mid-poll.

        AWS sends a SIGTERM when it scales an ECS task down and gives us 30
        seconds before following up with a SIGKILL, which we don't handle.
        """
        signal.signal(signal.SIGTERM, self.handle_exit)

        # SIGINT is a keyboard interrupt, if you're running locally and hit CTRL+C.
        signal.signal(signal.SIGINT, self.handle_interrupt)

    def handle_exit(self, signum: int, frame: FrameType | None) -> None:
        logger.info(
            "Received interrupt signal, will allow the current batch to complete before exiting."
        )
        self.sigterm_received = True
        self._shutdown_event.set()

    def handle_interrupt(self, signum: int, frame: FrameType | None) -> None:
        logger.info("Received keyboard interrupt, exiting immediately.")
        self._shutdown_event.set()
        sys.exit(0)

    def listen(self) -> None:
        """Poll the workflow queue until we're told to stop."""
        if is_maintenance_mode_enabled():
            self._idle_during_maintenance()
            return

        logger.info(
            "Listening for workflow queue messages",
            extra={"queue_url": self.sqs_client.queue_url},
        )

        batch_count = 0
        while True:
            batch_count += 1
            self.process_batch()

            # A sigterm received mid-batch isn't handled
            # until after that batch has finished.
            if self.sigterm_received:
                logger.info("Exiting after receiving SIGTERM.")
                break

            # For the purposes of testing, we can configure a maximum batch
            # count to break the loop after a certain number of iterations
            if (
                self.config.workflow_maximum_batch_count is not None
                and batch_count >= self.config.workflow_maximum_batch_count
            ):
                logger.info("Exiting after batch limit reached.")
                break

    def _idle_during_maintenance(self) -> None:
        """Idle without touching SQS while maintenance mode is enabled.

        The flag is resolved at task launch and flipped via force-new-deployment,
        so a single check at loop entry is sufficient. We wait for the SIGTERM that
        the redeploy sends rather than returning, which would only have ECS restart
        this task in a loop for the length of the maintenance window.
        """
        logger.info(
            "Skipping workflow processing due to maintenance mode",
            extra={"maintenance_mode_event": WorkflowQueueListenerLogEvent.MAINTENANCE_MODE_SKIP},
        )
        self._shutdown_event.wait()
        logger.info("Exiting after receiving SIGTERM.")

    def process_batch(self) -> list[SQSMessage]:
        """Fetch a batch of messages, log them, and take them off the queue.

        Returns the messages it handled for test purposes.
        """
        messages = self.sqs_client.receive_messages(wait_time=self.config.workflow_cycle_duration)
        logger.info("Fetched SQS messages", extra={"message_count": len(messages)})

        for message in messages:
            logger.info("Received workflow queue message", extra=_get_log_extra(message))
            # Nothing parses the body yet, so keep it out of the ordinary logs
            # rather than assuming anything about what a caller put on the queue.
            logger.debug(
                "Workflow queue message body",
                extra=_get_log_extra(message) | {"message_body": message.body},
            )

        self.sqs_client.delete_message_batch([message.receipt_handle for message in messages])

        return messages


def _get_log_extra(message: SQSMessage) -> dict:
    return {"message_id": message.message_id, "message_body_length": len(message.body)}


@task_blueprint.cli.command(
    "workflow-queue-listener",
    help="Consume messages off the workflow queue - a placeholder until the workflow manager lands",
)
@workflow_background_task("workflow-queue-listener")
def workflow_queue_listener() -> None:
    WorkflowQueueListener().listen()
