import pytest
from sqlalchemy.exc import ProgrammingError

from tests.db.models.factories import GrantorOrganizationFactory


def test_grantor_organization_triggers(db_session, enable_factory_create):
    # With no parent, the path is just the org ID
    org = GrantorOrganizationFactory.create()
    assert org.path.path == str(org.grantor_organization_id)

    # With a parent
    org2 = GrantorOrganizationFactory.create(parent_organization=org)
    assert org2.path.path == f"{org.grantor_organization_id}.{org2.grantor_organization_id}"

    # with two parents
    org3 = GrantorOrganizationFactory.create(parent_organization=org2)
    assert (
        org3.path.path
        == f"{org.grantor_organization_id}.{org2.grantor_organization_id}.{org3.grantor_organization_id}"
    )

    # Another org without a parent isn't linked to the above
    new_org = GrantorOrganizationFactory.create()
    assert new_org.path.path == str(new_org.grantor_organization_id)

    # Also create a random other org to show it doesn't get modified by updates below
    random_org = GrantorOrganizationFactory.create()
    assert random_org.path.path == str(random_org.grantor_organization_id)

    # Change the old top-level org to have this new org as a parent
    # Which automatically cascades to each of the children
    org.parent_organization = new_org
    db_session.commit()

    db_session.refresh(org)
    assert org.path.path == f"{new_org.grantor_organization_id}.{org.grantor_organization_id}"

    # Despite not directly touching these, they were reorged
    db_session.refresh(org2)
    assert (
        org2.path.path
        == f"{new_org.grantor_organization_id}.{org.grantor_organization_id}.{org2.grantor_organization_id}"
    )

    db_session.refresh(org3)
    assert (
        org3.path.path
        == f"{new_org.grantor_organization_id}.{org.grantor_organization_id}.{org2.grantor_organization_id}.{org3.grantor_organization_id}"
    )

    # This wasn't changed
    db_session.refresh(random_org)
    assert random_org.path.path == str(random_org.grantor_organization_id)


def test_grantor_organization_trigger_prevents_cycle_on_update(db_session, enable_factory_create):
    org = GrantorOrganizationFactory.create()
    child_org = GrantorOrganizationFactory.create(parent_organization=org)
    org.parent_organization = child_org

    with pytest.raises(ProgrammingError, match="cannot reparent grantor_organization"):
        db_session.commit()


def test_grantor_organization_trigger_prevents_cycle_on_update_multiple_jumps(
    db_session, enable_factory_create
):
    """Same as above test, but shows it works even when not directly connected."""
    org = GrantorOrganizationFactory.create()
    child_org = GrantorOrganizationFactory.create(parent_organization=org)
    child_org2 = GrantorOrganizationFactory.create(parent_organization=child_org)
    org.parent_organization = child_org2

    with pytest.raises(ProgrammingError, match="cannot reparent grantor_organization"):
        db_session.commit()
