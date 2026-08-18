import pytest

from src.constants.lookup_constants import ResourceType
from tests.db.models.factories import (
    GrantorOrganizationFactory,
    InternalResourceFactory,
    PartnerFactory,
    ProgramFactory,
    ResourceFactory,
)


@pytest.mark.parametrize(
    "factory_cls",
    [InternalResourceFactory, PartnerFactory, GrantorOrganizationFactory, ProgramFactory],
)
def test_concrete_resource(enable_factory_create, factory_cls):
    """Every resource-backed table is reachable from its resource row."""
    entity = factory_cls.create()

    concrete_resource = entity.resource.concrete_resource

    assert concrete_resource is entity
    assert concrete_resource.get_resource_id() == entity.get_resource_id()
    assert concrete_resource.get_resource_type() == entity.resource.resource_type


def test_concrete_resource_type_without_a_table(enable_factory_create):
    """A resource type that has no table yet errors rather than resolving to nothing."""
    resource = ResourceFactory.create(resource_type=ResourceType.OPPORTUNITY)

    with pytest.raises(ValueError, match="has no table behind it"):
        assert resource.concrete_resource


def test_concrete_resource_missing_row(enable_factory_create):
    """A resource whose concrete row never got created errors rather than returning None."""
    resource = ResourceFactory.create(resource_type=ResourceType.PARTNER)

    with pytest.raises(ValueError, match="has no partner row behind it"):
        assert resource.concrete_resource
