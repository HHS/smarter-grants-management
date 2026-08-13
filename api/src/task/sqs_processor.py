import logging
import signal
import sys
import threading
import time
from types import FrameType
from typing import Any

from grants_shared.adapters.aws.sqs_adapter import SQSClient
from grants_shared.api.maintenance_mode import is_maintenance_mode_enabled
from grants_shared.util.env_config import PydanticBaseEnvConfig

logger = logging.getLogger(__name__)


class SqsProcessorConfig(PydanticBaseEnvConfig):
    """Configuration shared by every SQS-consuming task.

    Subclass this and set an ``env_prefix`` so each processor reads its own
    env vars (eg. ``WORKFLOW_CYCLE_DURATION`` rather than ``CYCLE_DURATION``).
    """

    # How long each poll waits for messages to show up, in seconds.
    cycle_duration: int = 10

    # How many batches to poll before exiting.
    # Only used for testing, we have no limit
    # under ordinary circumstances.
    maximum_batch_count: int | None = None


class BaseSqsProcessor:
    """Base class for long-running tasks that consume an SQS queue.

    Owns everything that isn't specific to what's on the queue: the poll loop,
    signal handling, the maintenance-mode idle, and the batch metrics. Subclasses
    supply the queue and the per-batch work::

        class MyProcessor(BaseSqsProcessor):
            @property
            def queue_url(self) -> str:
                return SQSConfig().my_queue_url

            def process_batch(self) -> None:
                ...

        MyProcessor(MyProcessorConfig()).run()
    """

    # Distinct, queryable event value logged when a maintenance window makes this
    # processor idle. Override per processor so log queries can tell them apart.
    maintenance_mode_log_event: str = "maintenance_mode_processing_skipped"

    def __init__(self, config: SqsProcessorConfig):
        self.config = config

        self.sigterm_received = False
        # Set when a shutdown signal is received so the maintenance-mode idle loop
        # can wake immediately rather than waiting out a full sleep interval.
        self._shutdown_event = threading.Event()
        self._register_signal_handlers()

        # Record a few metrics that we'll log when the process exits.
        # Subclasses can add their own keys from process_batch.
        self.metrics: dict[str, Any] = {"batches_processed": 0}

        self.sqs_client = SQSClient(queue_url=self.queue_url)

    @property
    def queue_url(self) -> str:
        """The queue this processor consumes. Implemented by subclasses."""
        raise NotImplementedError

    def process_batch(self) -> Any:
        """Fetch and handle one batch of messages. Implemented by subclasses.

        Whatever this returns is passed through by the caller, which is convenient
        for tests that want to assert on a single batch without running the loop.
        """
        raise NotImplementedError

    def on_start(self) -> None:
        """Hook for one-time setup, run just before the first batch.

        Deliberately called after the maintenance-mode check so a processor that
        is only going to idle doesn't do the setup at all.
        """

    def _register_signal_handlers(self) -> None:
        """Register signal handlers to handle expected
        signals like keyboard interrupts and kill commands.

        This changes the default behavior of "end the program instantly"
        into a more graceful approach. Note that not all signals
        can be caught, and many that indicate hardware faults shouldn't.
        """
        # Make it so if a SIGTERM is received, it doesn't
        # cause the process to instantly exit so we can gracefully
        # exit. SIGTERM is sent by either calling kill on the process ID
        # and is also sent by AWS when it tells an ECS task to scale down.
        # We have 30 seconds to gracefully shutdown before a SIGKILL will be sent.
        # We do not handle SIGKILL and will allow it to kill the process.
        # https://aws.amazon.com/blogs/containers/graceful-shutdowns-with-ecs/
        signal.signal(signal.SIGTERM, self.handle_exit)

        # SIGINT is a keyboard interrupt, if you're running locally and hit CTRL+C.
        signal.signal(signal.SIGINT, self.handle_interrupt)

        # Most other signals indicate either errors or
        # more significant kill signals that we are fine
        # with causing the program to exit instantly as normal.

    def handle_exit(self, signum: int, frame: FrameType | None) -> None:
        logger.info(
            "Received interrupt signal, will allow current processing to complete before exiting."
        )
        self.sigterm_received = True
        self._shutdown_event.set()

    def handle_interrupt(self, signum: int, frame: FrameType | None) -> None:
        logger.info("Received keyboard interrupt, exiting immediately.")
        self._shutdown_event.set()
        sys.exit(0)

    def run(self) -> None:
        """Process batches off the queue until we're told to stop.

        The 'main' loop of an SQS processor.
        """
        if is_maintenance_mode_enabled():
            self._idle_during_maintenance()
            return

        logger.info("Processing SQS messages", extra={"queue_url": self.sqs_client.queue_url})
        self.on_start()

        batch_count = 0
        while True:
            batch_count += 1
            start_time = time.perf_counter()

            self.process_batch()
            self.metrics["batches_processed"] += 1

            end_time = time.perf_counter()
            batch_duration = round(end_time - start_time, 3)
            logger.info("Finished running batch", extra={"batch_duration_sec": batch_duration})

            # If a sigterm signal is received
            # we don't handle it until after
            # processing a batch has finished.
            if self.sigterm_received:
                logger.info("Exiting after receiving SIGTERM.")
                break

            # For the purposes of testing, we can configure a maximum batch
            # count to break the loop after a certain number of iterations
            if (
                self.config.maximum_batch_count is not None
                and batch_count >= self.config.maximum_batch_count
            ):
                logger.info("Exiting after batch limit reached.")
                break

        logger.info("Finished processing SQS messages - exiting process", extra=self.metrics)

    def _idle_during_maintenance(self) -> None:
        """Idle without touching SQS or the DB while maintenance mode is enabled.

        The flag is resolved at task launch and flipped via force-new-deployment,
        so a single check at loop entry is sufficient. We wait for the SIGTERM that
        the redeploy sends rather than returning, which would only have ECS restart
        this task in a loop for the length of the maintenance window.
        """
        logger.info(
            "Skipping SQS processing due to maintenance mode",
            extra={"maintenance_mode_event": self.maintenance_mode_log_event},
        )
        # Block until a shutdown signal wakes us. handle_exit/handle_interrupt set the
        # event, so this returns promptly on SIGTERM instead of waiting out a sleep.
        self._shutdown_event.wait()
        logger.info("Exiting after receiving SIGTERM.")
