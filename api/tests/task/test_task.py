import logging
from typing import Any

import pytest
from sqlalchemy.exc import InvalidRequestError

from src.constants.lookup_constants import JobStatus
from src.task.task import Task


class SimpleTask(Task):
    """Test implementation of Task"""

    def __init__(self, db_session, metrics_to_add: dict[str, Any] | None = None):
        super().__init__(db_session)
        self.metrics_to_add = metrics_to_add if metrics_to_add else {}

    def run_task(self) -> None:
        self.set_metrics(self.metrics_to_add)


class FailingTask(Task):
    """Test implementation that fails during run_task"""

    def run_task(self) -> None:
        raise ValueError("Task failed")


class DBFailingTask(Task):
    """Test implementation that fails during DB operation"""

    def run_task(self) -> None:
        # Simulate DB operation failing
        raise InvalidRequestError("DB Error", None, None)


def test_task_handles_general_error(db_session):
    """Test that task properly handles non-DB errors and rolls back session"""
    task = FailingTask(db_session)

    with pytest.raises(ValueError):
        task.run()

    # Verify job was created and updated to failed status
    assert task.job is not None
    assert task.job.job_status == JobStatus.FAILED

    # Verify session is still usable
    db_session.begin()  # Start a new transaction
    assert db_session.is_active  # Session should be active with new transaction


def test_task_handles_db_error(db_session):
    """Test that task properly handles DB errors"""
    task = DBFailingTask(db_session)

    with pytest.raises(InvalidRequestError):
        task.run()

    # Verify session was rolled back and is usable
    db_session.begin()  # Start a new transaction
    assert db_session.is_active  # Session should be active with new transaction


def test_successful_task_completion(db_session):
    """Test that task completes successfully and updates job status"""
    task = SimpleTask(db_session)
    task.run()

    assert task.job is not None
    assert task.job.job_status == JobStatus.COMPLETED
    assert "task_duration_sec" in task.metrics

    # Verify session is still usable by starting a new transaction
    db_session.begin()  # Start a new transaction
    assert db_session.is_active  # Session should be active with new transaction

def test_task_log_metrics_small_count(db_session, caplog):
    caplog.set_level(logging.INFO)

    metrics_to_set = {f"filler_metric_{i}": i for i in range(35)}

    SimpleTask(db_session, metrics_to_add=metrics_to_set).run()

    # Make sure the warning complaining about the problem is NOT logged
    assert "A large number of metrics is being added for this task" not in caplog.messages

    # Should only have logged once
    records = [
        record for record in caplog.records if record.message.startswith("Completed SimpleTask")
    ]
    assert len(records) == 1

    # Verify the number of metrics is what we passed in
    assert len([k for k in records[0].__dict__ if k.startswith("filler_metric_")]) == 35
    assert records[0].task_class == "SimpleTask"

def test_task_log_metrics_large_count(db_session, caplog):
    caplog.set_level(logging.INFO)

    metrics_to_set = {f"filler_metric_{i}": i for i in range(250)}

    SimpleTask(db_session, metrics_to_add=metrics_to_set).run()

    # Make sure the warning complaining about the problem is logged
    assert (
        "A large number of metrics are being added for this task - batching them together"
        in caplog.messages
    )

    # Want to make sure there are at least 3 batches of logs for this
    records = [
        record for record in caplog.records if record.message.startswith("Completed SimpleTask")
    ]
    assert len(records) == 3

    # Make sure there are two records with 100 records, and one with 50
    record_counts = []
    for record in records:
        record_counts.append(len([k for k in record.__dict__ if k.startswith("filler_metric_")]))

        # Make sure task_class is always set
        assert record.task_class == "SimpleTask"

    assert record_counts == [100, 100, 50]
