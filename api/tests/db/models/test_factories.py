import pytest
from sqlalchemy import select

from src.constants.lookup_constants import (
    GrantorOrganizationAuditEvent,
    PartnerAuditEvent,
    UserType,
)
from src.db.models.grantor_organization_models import GrantorOrganizationAudit, PartnerAudit
from src.db.models.user_models import User
from tests.db.models.factories import (
    GrantorOrganizationAuditFactory,
    PartnerAuditFactory,
    ProgramFactory,
    UserFactory,
)


def test_user_factory_build():
    user = UserFactory.build()

    assert user.user_id is not None
    assert user.user_type == UserType.STANDARD

    # Verify we can override values in the factories
    user = UserFactory.build(user_type=UserType.INTERNAL_FRONTEND)
    assert user.user_id is not None
    assert user.user_type == UserType.INTERNAL_FRONTEND


def test_user_factory_create(enable_factory_create, db_session):

    user = UserFactory.create()

    assert user.user_id is not None
    assert user.user_type == UserType.STANDARD

    db_record = db_session.execute(select(User).where(User.user_id == user.user_id)).scalar()
    assert db_record.user_id == user.user_id
    assert db_record.user_type == user.user_type

    # Verify we can override values in the factories
    user = UserFactory.create(user_type=UserType.INTERNAL_FRONTEND)
    assert user.user_id is not None
    assert user.user_type == UserType.INTERNAL_FRONTEND

    db_record = db_session.execute(select(User).where(User.user_id == user.user_id)).scalar()
    assert db_record.user_id == user.user_id
    assert db_record.user_type == user.user_type


def test_factory_create_uninitialized_db_session():
    # DB factory access is disabled from tests unless you add the
    # 'enable_factory_create' fixture.
    with pytest.raises(Exception, match="Factory db_session is not initialized."):
        UserFactory.create()


def test_program_factory(enable_factory_create, db_session):
    program = ProgramFactory.create(has_secondary_partners=True)

    # Make sure when we make a program, only one partner is created
    # and attached in all the correct places
    assert program.partner_id == program.program_office.partner_id
    assert program.partner_id == program.grant_office.partner_id

    # Make sure the secondary partners are different
    for secondary_partner in program.link_secondary_program_partners:
        assert secondary_partner.partner_id != program.partner_id


def test_partner_audit_factory_build():
    audit = PartnerAuditFactory.build()

    assert audit.partner_audit_id is not None
    assert audit.partner_id is not None
    assert audit.user_id is not None
    assert audit.partner_audit_event == PartnerAuditEvent.USER_ROLES_MODIFIED


def test_partner_audit_factory_create(enable_factory_create, db_session):
    audit = PartnerAuditFactory.create()

    assert audit.partner_audit_id is not None
    assert audit.partner_id is not None
    assert audit.user_id is not None
    assert audit.partner_audit_event == PartnerAuditEvent.USER_ROLES_MODIFIED

    db_record = db_session.execute(
        select(PartnerAudit).where(PartnerAudit.partner_audit_id == audit.partner_audit_id)
    ).scalar()
    assert db_record is not None
    assert db_record.partner_audit_event == PartnerAuditEvent.USER_ROLES_MODIFIED


def test_grantor_organization_audit_factory_build():
    audit = GrantorOrganizationAuditFactory.build()

    assert audit.grantor_organization_audit_id is not None
    assert audit.grantor_organization_id is not None
    assert audit.user_id is not None
    assert (
        audit.grantor_organization_audit_event == GrantorOrganizationAuditEvent.USER_ROLES_MODIFIED
    )


def test_grantor_organization_audit_factory_create(enable_factory_create, db_session):
    audit = GrantorOrganizationAuditFactory.create()

    assert audit.grantor_organization_audit_id is not None
    assert audit.grantor_organization_id is not None
    assert audit.user_id is not None
    assert (
        audit.grantor_organization_audit_event == GrantorOrganizationAuditEvent.USER_ROLES_MODIFIED
    )

    db_record = db_session.execute(
        select(GrantorOrganizationAudit).where(
            GrantorOrganizationAudit.grantor_organization_audit_id
            == audit.grantor_organization_audit_id
        )
    ).scalar()
    assert db_record is not None
    assert (
        db_record.grantor_organization_audit_event
        == GrantorOrganizationAuditEvent.USER_ROLES_MODIFIED
    )
