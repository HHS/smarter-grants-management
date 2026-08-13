import json
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime
from enum import StrEnum

from flask import Flask, current_app
from grants_shared.adapters import db
from grants_shared.adapters.aws import SQSConfig
from grants_shared.adapters.aws.sqs_adapter import SQSMessage
from grants_shared.adapters.db import flask_db
from grants_shared.util import datetime_util
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from src.constants.lookup_constants import WorkflowEventProcessingResult
from src.db.models.workflow_models import WorkflowEventHistory
from src.task.sqs_processor import BaseSqsProcessor, SqsProcessorConfig
from src.workflow.event.sqs_message_container import SqsMessageContainer
from src.workflow.event.workflow_event import WorkflowEvent
from src.workflow.handler.event_handler import EventHandler
from src.workflow.registry.workflow_client_registry import init_workflow_client_registry
from src.workflow.workflow_background_task import workflow_transaction
from src.workflow.workflow_errors import NonRetryableWorkflowError, RetryableWorkflowError

logger = logging.getLogger(__name__)


class WorkflowManagerLogEvent(StrEnum):
    """Distinct, queryable event types for workflow manager log records."""

    MAINTENANCE_MODE_SKIP = "maintenance_mode_workflow_processing_skipped"


class WorkflowManagerConfig(SqsProcessorConfig):
    """Config for the workflow manager.

    The env_prefix is what gives the inherited fields their workflow-specific
    env var names: cycle_duration -> WORKFLOW_CYCLE_DURATION and
    maximum_batch_count -> WORKFLOW_MAXIMUM_BATCH_COUNT.
    """

    model_config = SettingsConfigDict(env_prefix="WORKFLOW_")

    # Per-event timeout when processing in parallel. If a thread doesn't
    # return a result within this many seconds, we stop waiting on it,
    # treat the event as failed (message kept on the queue), and move on.
    # The thread itself can't be forcibly killed - the DB transaction
    # opened inside it will roll back when the underlying operation
    # eventually errors or completes.
    event_processing_timeout_sec: int = 30  # WORKFLOW_EVENT_PROCESSING_TIMEOUT_SEC


class WorkflowManager(BaseSqsProcessor):
    """Consume workflow events off SQS and run them through the state machines.

    The poll loop, signal handling, and maintenance-mode idle all live on
    BaseSqsProcessor - what's specific here is turning each message into a
    workflow event and fanning the batch out over a thread pool.
    """

    config: WorkflowManagerConfig

    maintenance_mode_log_event = WorkflowManagerLogEvent.MAINTENANCE_MODE_SKIP

    def __init__(self, config: WorkflowManagerConfig | None = None):
        if config is None:
            config = WorkflowManagerConfig()

        super().__init__(config)

        # Very simple metric for test purposes - the base class tracks batches.
        self.metrics["events_processed"] = 0

    @property
    def queue_url(self) -> str:
        return SQSConfig().workflow_queue_url

    def on_start(self) -> None:
        init_workflow_client_registry()

    def parse_event(self, message: SQSMessage) -> WorkflowEvent:
        try:
            message_body = json.loads(message.body)
            return WorkflowEvent.model_validate(message_body)
        except json.JSONDecodeError as e:
            logger.exception(
                "Failed to parse SQS message body as JSON", extra={"message_id": message.message_id}
            )
            raise ValueError(f"Invalid JSON in SQS message body: {e}") from e
        except ValidationError:
            logger.exception(
                "Failed to validate SQS message as WorkflowEvent",
                extra={"message_id": message.message_id},
            )
            raise

    def parse_sent_timestamp(self, message: SQSMessage) -> datetime:
        """Parse the SQS messages timestamp - defaulting to now on errors"""
        sent_timestamp = message.attributes.get("SentTimestamp", None)
        if sent_timestamp is None:
            logger.warning(
                "SQS message was missing sent timestamp - defaulting to now",
                extra={"message_id": message.message_id},
            )
            return datetime_util.utcnow()

        try:
            return datetime_util.from_timestamp(int(sent_timestamp))
        except Exception:
            logger.exception(
                "Could not convert timestamp from SQS message to datetime - defaulting to now",
                extra={"message_id": message.message_id},
            )
            return datetime_util.utcnow()

    def process_batch(self) -> tuple[list[str], list[str]]:
        """Fetch and process a batch of events from SQS."""
        sqs_containers = self.fetch_messages()
        logger.info("Fetched SQS messages", extra={"message_count": len(sqs_containers)})

        messages_to_delete, messages_to_keep = self._handle_containers(sqs_containers)

        self.delete_messages(messages_to_delete)

        self.metrics["events_processed"] += len(sqs_containers)

        # return messages to delete and messages to keep handles for testing purposes
        logger.info(
            "Processed SQS messages",
            extra={
                "successful_message_count": len(messages_to_delete),
                "failed_message_count": len(messages_to_keep),
            },
        )
        return messages_to_delete, messages_to_keep

    def _handle_containers(
        self, sqs_containers: list[SqsMessageContainer]
    ) -> tuple[list[str], list[str]]:
        """Run each container through handle_event concurrently and classify the results.

        Returns the receipt handles to delete and the receipt handles to keep on the queue.
        Each container is processed on its own thread so IO waits (DB calls, downstream
        services) overlap; the core loop stays single-threaded and waits for every thread
        in this batch to finish before any messages are deleted.
        """
        messages_to_delete: list[str] = []
        messages_to_keep: list[str] = []

        if not sqs_containers:
            return messages_to_delete, messages_to_keep

        app = current_app._get_current_object()  # type: ignore[attr-defined]
        timeout = self.config.event_processing_timeout_sec

        with ThreadPoolExecutor(max_workers=len(sqs_containers)) as executor:
            future_to_container = {
                executor.submit(_handle_event_in_thread, app, container): container
                for container in sqs_containers
            }

            for future, sqs_container in future_to_container.items():
                try:
                    event_result = future.result(timeout=timeout)
                except FuturesTimeoutError:
                    # Python threads can't be forcibly killed - the thread will
                    # keep running until its DB call errors or returns, at which
                    # point the surrounding transaction rolls back. We stop waiting
                    # on it and treat the message as failed.
                    logger.exception(
                        "Workflow event handler exceeded timeout",
                        extra=sqs_container.get_log_extra() | {"timeout_sec": timeout},
                    )
                    event_result = WorkflowEventProcessingResult.GENERAL_ERROR
                except Exception:
                    logger.exception(
                        "Failed to handle current event",
                        extra=sqs_container.get_log_extra(),
                    )
                    event_result = WorkflowEventProcessingResult.GENERAL_ERROR

                if event_result in [
                    WorkflowEventProcessingResult.SUCCESS,
                    WorkflowEventProcessingResult.NON_RETRYABLE_ERROR,
                ]:
                    messages_to_delete.append(sqs_container.receipt_handle)
                else:
                    messages_to_keep.append(sqs_container.receipt_handle)

        return messages_to_delete, messages_to_keep

    def fetch_messages(self) -> list[SqsMessageContainer]:
        containers: list[SqsMessageContainer] = []
        try:
            messages = self.sqs_client.receive_messages(wait_time=self.config.cycle_duration)
        except Exception:
            logger.exception("Failed to fetch messages from SQS")
            return containers

        for message in messages:
            try:
                event = self.parse_event(message)
                history_event = WorkflowEventHistory(
                    # The event ID the caller generated is the primary key, so the
                    # ID handed back by the event API is what finds this row later.
                    workflow_event_history_id=event.event_id,
                    # Round-trip through JSON so UUIDs/datetimes land in the JSONB
                    # column as primitives rather than a serialized string.
                    event_data=json.loads(event.model_dump_json()),
                    sent_at=self.parse_sent_timestamp(message),
                    # This might change if it errors - but default to True
                    is_successfully_processed=True,
                )
                containers.append(
                    SqsMessageContainer(
                        receipt_handle=message.receipt_handle,
                        workflow_event=event,
                        history_event=history_event,
                    )
                )
            except Exception:
                logger.exception("Failed to convert SQS message")
                continue

        return containers

    def delete_messages(self, receipt_handles: list[str]) -> None:
        # Delete messages that were successfully processed or had non-retryable errors
        try:
            delete_result = self.sqs_client.delete_message_batch(receipt_handles)
            if delete_result.failed_deletes:
                logger.error(
                    "Failed to delete messages from SQS queue",
                    extra={"failed_deletes": list(delete_result.failed_deletes)},
                )
        except Exception:
            logger.exception("Failed to delete messages from SQS queue")


def _handle_event_in_thread(
    app: Flask, sqs_container: SqsMessageContainer
) -> WorkflowEventProcessingResult:
    # handle_event's @with_db_session decorator pulls the DB client off
    # current_app, which is per-thread. Push the app context here so the
    # decorator can find it from inside the worker thread.
    with app.app_context():
        return handle_event(sqs_container)


@flask_db.with_db_session()
def handle_event(
    db_session: db.Session, sqs_container: SqsMessageContainer
) -> WorkflowEventProcessingResult:
    """Handle an SQS event"""
    with workflow_transaction(sqs_container.workflow_event.event_type):
        logger.info(
            "Processing event",
            extra=sqs_container.get_log_extra(),
        )

        return _handle_event(db_session, sqs_container)


def _handle_event(
    db_session: db.Session, sqs_container: SqsMessageContainer
) -> WorkflowEventProcessingResult:
    """
    Handle the SQS event:

    * DB session management - any errors will rollback all changes
                              except non-retryable ones which only
                              persist their history event.
    * Logging / metrics inclusion
    * Error handling of the various cases
    """

    log_extra = sqs_container.get_log_extra()
    result = WorkflowEventProcessingResult.SUCCESS
    error: Exception | None = None

    try:
        with db_session.begin():
            db_session.add(sqs_container.history_event)
            EventHandler(db_session, sqs_container).process()

    except NonRetryableWorkflowError as e:
        if db_session.is_active:
            db_session.rollback()

        with db_session.begin():
            sqs_container.history_event.is_successfully_processed = False
            db_session.add(sqs_container.history_event)
        logger.warning(
            "Encountered non-retryable workflow error while processing event",
            exc_info=True,
            extra=log_extra,
        )
        result = WorkflowEventProcessingResult.NON_RETRYABLE_ERROR
        error = e

    except RetryableWorkflowError as e:
        logger.warning(
            "Encountered retryable workflow error while processing event",
            exc_info=True,
            extra=log_extra,
        )
        result = WorkflowEventProcessingResult.RETRYABLE_ERROR
        error = e

    except Exception as e:
        # log specific error for any other exception
        logger.exception("Unexpected error processing workflow event", extra=log_extra)
        result = WorkflowEventProcessingResult.GENERAL_ERROR
        error = e

    # Add whatever to the log extra that was added to the metric context
    # Even if the above errored, there could be a bit more info we pull out
    log_extra |= sqs_container.workflow_metric_context.log_extra
    log_extra |= sqs_container.workflow_metric_context.metrics

    log_extra |= {
        "event_result": result,
        "event_lifecycle_duration_sec": (
            datetime_util.utcnow() - sqs_container.history_event.sent_at
        ).total_seconds(),
    }

    if error is not None:
        log_extra["error_cls"] = error.__class__.__name__

    # This log is one that we'll tie into heavily for metrics
    logger.info("Finished handling event", extra=log_extra)

    return result
