import pytest

from src.db.models.grantor_organization_models import Program
from src.db.models.user_models import User
from src.workflow.workflow_background_task import _init_newrelic_app
from tests.db.models.factories import ProgramFactory, UserFactory

# The real state machines register themselves when src/workflow/state_machine is
# imported. Import the test-only ones here so they're registered for every workflow
# test rather than only the modules that happen to reference them directly.
import tests.workflow.state_machine.test_state_machines  # noqa: F401 isort:skip


@pytest.fixture(scope="session", autouse=True)
def init_new_relic_app():
    """Setup the new relic app to be initialized so the transaction logic
    won't error when running tests. This won't actually connect to New Relic.

    Outside of tests the workflow_background_task decorator does this, but that only
    runs for the CLI entry-point - anything calling into the manager directly needs it
    set up here or workflow_transaction raises.
    """
    _init_newrelic_app()


@pytest.fixture
def workflow_user(monkeypatch, enable_factory_create) -> User:
    """The internal user that automatic (engine-driven) state transitions are audited against.

    Points WORKFLOW_SERVICE_INTERNAL_USER_ID at a user that actually exists in the
    test schema - the audit record for an automatic transition sets the user ID
    without a lookup, so a missing user only surfaces as a foreign key error at
    commit time.
    """
    user = UserFactory.create()
    monkeypatch.setenv("WORKFLOW_SERVICE_INTERNAL_USER_ID", str(user.user_id))
    return user


@pytest.fixture(autouse=True)
def workflow_user_init(workflow_user):
    """Make the internal workflow user available to every workflow test."""


@pytest.fixture
def program(enable_factory_create) -> Program:
    """A program, which is what the prototype workflow attaches to.

    Programs are resource-backed, so the resource row the workflow points at is
    created for us by the resource automation flush hook.
    """
    return ProgramFactory.create()
