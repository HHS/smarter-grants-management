import uuid

from sqlalchemy import select

from src.constants.lookup_constants import GrantorOrganizationType, ResourceType
from src.db.models.grantor_organization_models import GrantorOrganization, Partner, Program
from src.db.models.resource_models import InternalResource, Resource
from tests.db.models.factories import (
    GrantorOrganizationFactory,
    InternalResourceFactory,
    PartnerFactory,
    ProgramFactory,
)


def test_resource_automation_with_defaults(db_session):

    partner = Partner(partner_name="My example partner")
    db_session.add(partner)

    organization_1 = GrantorOrganization(
        organization_name="organization1",
        partner=partner,
        grantor_organization_type=GrantorOrganizationType.PROGRAM_OFFICE,
    )
    db_session.add(organization_1)

    organization_2 = GrantorOrganization(
        organization_name="organization2",
        partner=partner,
        grantor_organization_type=GrantorOrganizationType.GRANT_OFFICE,
    )
    db_session.add(organization_2)

    program = Program(
        program_name="my example program",
        partner=partner,
        program_office=organization_1,
        grant_office=organization_2,
    )
    db_session.add(program)

    internal_resource = InternalResource(internal_resource_name="My example internal resource")
    db_session.add(internal_resource)

    db_session.commit()

    assert partner.partner_id is not None
    assert partner.resource.resource_id == partner.partner_id
    assert partner.resource.resource_type == ResourceType.PARTNER

    assert organization_1.grantor_organization_id is not None
    assert organization_1.resource.resource_id == organization_1.grantor_organization_id
    assert organization_1.resource.resource_type == ResourceType.GRANTOR_ORGANIZATION

    assert organization_2.grantor_organization_id is not None
    assert organization_2.resource.resource_id == organization_2.grantor_organization_id
    assert organization_2.resource.resource_type == ResourceType.GRANTOR_ORGANIZATION

    assert program.program_id is not None
    assert program.resource.resource_id == program.program_id
    assert program.resource.resource_type == ResourceType.PROGRAM

    assert internal_resource.internal_resource_id is not None
    assert internal_resource.resource.resource_id == internal_resource.internal_resource_id
    assert internal_resource.resource.resource_type == ResourceType.INTERNAL


def test_resource_automation_with_set_ids(db_session):

    partner = Partner(partner_id=uuid.uuid4(), partner_name="My example partner")
    db_session.add(partner)

    organization_1 = GrantorOrganization(
        grantor_organization_id=uuid.uuid4(),
        organization_name="organization1",
        partner=partner,
        grantor_organization_type=GrantorOrganizationType.PROGRAM_OFFICE,
    )
    db_session.add(organization_1)

    organization_2 = GrantorOrganization(
        grantor_organization_id=uuid.uuid4(),
        organization_name="organization2",
        partner=partner,
        grantor_organization_type=GrantorOrganizationType.GRANT_OFFICE,
    )
    db_session.add(organization_2)

    program = Program(
        program_id=uuid.uuid4(),
        program_name="my example program",
        partner=partner,
        program_office=organization_1,
        grant_office=organization_2,
    )
    db_session.add(program)

    internal_resource = InternalResource(
        internal_resource_id=uuid.uuid4(),
        internal_resource_name="My example internal resource",
    )
    db_session.add(internal_resource)

    db_session.commit()

    assert partner.partner_id is not None
    assert partner.resource.resource_id == partner.partner_id
    assert partner.resource.resource_type == ResourceType.PARTNER

    assert organization_1.grantor_organization_id is not None
    assert organization_1.resource.resource_id == organization_1.grantor_organization_id
    assert organization_1.resource.resource_type == ResourceType.GRANTOR_ORGANIZATION

    assert organization_2.grantor_organization_id is not None
    assert organization_2.resource.resource_id == organization_2.grantor_organization_id
    assert organization_2.resource.resource_type == ResourceType.GRANTOR_ORGANIZATION

    assert program.program_id is not None
    assert program.resource.resource_id == program.program_id
    assert program.resource.resource_type == ResourceType.PROGRAM

    assert internal_resource.internal_resource_id is not None
    assert internal_resource.resource.resource_id == internal_resource.internal_resource_id
    assert internal_resource.resource.resource_type == ResourceType.INTERNAL


def test_resource_automation_does_not_change_resource_on_change(db_session, enable_factory_create):

    partner = PartnerFactory.create()
    partner.partner_name = "my new partner name"

    organization = GrantorOrganizationFactory.create()
    organization.organization_name = "my new organization name"

    program = ProgramFactory.create()
    program.program_name = "my new program name"

    internal_resource_id = uuid.uuid4()
    internal_resource = InternalResourceFactory.create(internal_resource_id=internal_resource_id)
    internal_resource.internal_resource_name = "New internal resource name"

    db_session.commit()

    db_session.refresh(partner)
    assert partner.partner_name == "my new partner name"

    db_session.refresh(organization)
    assert organization.organization_name == "my new organization name"

    db_session.refresh(program)
    assert program.program_name == "my new program name"

    db_session.refresh(internal_resource)
    assert internal_resource.internal_resource_id == internal_resource_id
    assert internal_resource.resource.resource_id == internal_resource_id
    assert internal_resource.internal_resource_name == "New internal resource name"


def test_resource_automation_when_deleting_resource(db_session, enable_factory_create):
    partner = PartnerFactory.create()
    organization = GrantorOrganizationFactory.create()
    program = ProgramFactory.create()
    internal_resource = InternalResourceFactory.create()

    db_session.delete(partner)
    db_session.delete(organization)
    db_session.delete(program)
    db_session.delete(internal_resource)
    db_session.commit()

    resources = db_session.execute(
        select(Resource).where(
            Resource.resource_id.in_(
                [
                    partner.partner_id,
                    organization.grantor_organization_id,
                    program.program_id,
                    internal_resource.internal_resource_id,
                ]
            )
        )
    ).all()
    assert len(resources) == 0
