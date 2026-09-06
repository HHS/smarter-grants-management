from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.db.lookup import Lookup, LookupConfig, LookupRegistry, LookupStr, LookupTable
from src.constants.lookup_constants import (
    ApplicantType,
    ApprovalResponseType,
    ApprovalType,
    CompetitionOpenToApplicant,
    ExternalUserType,
    FundingCategory,
    FundingInstrument,
    GrantorOrganizationAuditEvent,
    GrantorOrganizationType,
    OpportunityAuditEvent,
    OpportunityCategory,
    PartnerAuditEvent,
    Privilege,
    ResourceType,
    UserType,
    WorkflowType,
)
from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable

#######################################################
# LookupConfig mappings
#
# Put all mappings of lookup values to their DB integer
# representations in this section
#######################################################

USER_TYPE_CONFIG: LookupConfig[UserType] = LookupConfig(
    [
        LookupStr(UserType.STANDARD, 1),
        LookupStr(UserType.INTERNAL_FRONTEND, 2),
    ]
)

EXTERNAL_USER_TYPE_CONFIG: LookupConfig[ExternalUserType] = LookupConfig(
    [LookupStr(ExternalUserType.LOGIN_GOV, 1)]
)

PRIVILEGE_CONFIG: LookupConfig[Privilege] = LookupConfig(
    [
        LookupStr(Privilege.VIEW_PARTNER, 1),
        LookupStr(Privilege.UPDATE_PARTNER, 2),
        LookupStr(Privilege.MANAGE_PARTNER_MEMBERS, 3),
        LookupStr(Privilege.VIEW_PROGRAM, 4),
        LookupStr(Privilege.UPDATE_PROGRAM, 5),
        LookupStr(Privilege.INTERNAL_WORKFLOW_EVENT_SEND, 6),
        LookupStr(Privilege.VIEW_GRANTOR_ORGANIZATION, 7),
        LookupStr(Privilege.UPDATE_GRANTOR_ORGANIZATION, 8),
        LookupStr(Privilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS, 9),
        LookupStr(Privilege.UNUSED_PRIVILEGE_102, 10),
        LookupStr(Privilege.UNUSED_PRIVILEGE_103, 11),
    ]
)

RESOURCE_TYPE_CONFIG: LookupConfig[ResourceType] = LookupConfig(
    [
        LookupStr(ResourceType.INTERNAL, 1),
        LookupStr(ResourceType.PARTNER, 2),
        LookupStr(ResourceType.PROGRAM, 3),
        LookupStr(ResourceType.GRANTOR_ORGANIZATION, 4),
        LookupStr(ResourceType.OPPORTUNITY, 5),
        LookupStr(ResourceType.OPPORTUNITY_GROUP, 6),
    ]
)

GRANTOR_ORGANIZATION_TYPE_CONFIG: LookupConfig[GrantorOrganizationType] = LookupConfig(
    [
        LookupStr(GrantorOrganizationType.PROGRAM_OFFICE, 1),
        LookupStr(GrantorOrganizationType.GRANT_OFFICE, 2),
    ]
)

PARTNER_AUDIT_EVENT_CONFIG: LookupConfig[PartnerAuditEvent] = LookupConfig(
    [LookupStr(PartnerAuditEvent.USER_ROLES_MODIFIED, 1)]
)


OPPORTUNITY_CATEGORY_CONFIG: LookupConfig[OpportunityCategory] = LookupConfig(
    [
        LookupStr(OpportunityCategory.DISCRETIONARY, 1),
        LookupStr(OpportunityCategory.MANDATORY, 2),
        LookupStr(OpportunityCategory.CONTINUATION, 3),
        LookupStr(OpportunityCategory.EARMARK, 4),
        LookupStr(OpportunityCategory.OTHER, 5),
    ]
)

APPLICANT_TYPE_CONFIG: LookupConfig[ApplicantType] = LookupConfig(
    [
        LookupStr(ApplicantType.STATE_GOVERNMENTS, 1),
        LookupStr(ApplicantType.COUNTY_GOVERNMENTS, 2),
        LookupStr(ApplicantType.CITY_OR_TOWNSHIP_GOVERNMENTS, 3),
        LookupStr(ApplicantType.SPECIAL_DISTRICT_GOVERNMENTS, 4),
        LookupStr(ApplicantType.INDEPENDENT_SCHOOL_DISTRICTS, 5),
        LookupStr(ApplicantType.PUBLIC_AND_STATE_INSTITUTIONS_OF_HIGHER_EDUCATION, 6),
        LookupStr(ApplicantType.PRIVATE_INSTITUTIONS_OF_HIGHER_EDUCATION, 7),
        LookupStr(ApplicantType.FEDERALLY_RECOGNIZED_NATIVE_AMERICAN_TRIBAL_GOVERNMENTS, 8),
        LookupStr(ApplicantType.OTHER_NATIVE_AMERICAN_TRIBAL_ORGANIZATIONS, 9),
        LookupStr(ApplicantType.PUBLIC_AND_INDIAN_HOUSING_AUTHORITIES, 10),
        LookupStr(ApplicantType.NONPROFITS_NON_HIGHER_EDUCATION_WITH_501C3, 11),
        LookupStr(ApplicantType.NONPROFITS_NON_HIGHER_EDUCATION_WITHOUT_501C3, 12),
        LookupStr(ApplicantType.INDIVIDUALS, 13),
        LookupStr(ApplicantType.FOR_PROFIT_ORGANIZATIONS_OTHER_THAN_SMALL_BUSINESSES, 14),
        LookupStr(ApplicantType.SMALL_BUSINESSES, 15),
        LookupStr(ApplicantType.OTHER, 16),
        LookupStr(ApplicantType.UNRESTRICTED, 17),
    ]
)

FUNDING_CATEGORY_CONFIG: LookupConfig[FundingCategory] = LookupConfig(
    [
        LookupStr(FundingCategory.RECOVERY_ACT, 1),
        LookupStr(FundingCategory.AGRICULTURE, 2),
        LookupStr(FundingCategory.ARTS, 3),
        LookupStr(FundingCategory.BUSINESS_AND_COMMERCE, 4),
        LookupStr(FundingCategory.COMMUNITY_DEVELOPMENT, 5),
        LookupStr(FundingCategory.CONSUMER_PROTECTION, 6),
        LookupStr(FundingCategory.DISASTER_PREVENTION_AND_RELIEF, 7),
        LookupStr(FundingCategory.EDUCATION, 8),
        LookupStr(FundingCategory.EMPLOYMENT_LABOR_AND_TRAINING, 9),
        LookupStr(FundingCategory.ENERGY, 10),
        LookupStr(FundingCategory.ENVIRONMENT, 11),
        LookupStr(FundingCategory.FOOD_AND_NUTRITION, 12),
        LookupStr(FundingCategory.HEALTH, 13),
        LookupStr(FundingCategory.HOUSING, 14),
        LookupStr(FundingCategory.HUMANITIES, 15),
        LookupStr(FundingCategory.INFRASTRUCTURE_INVESTMENT_AND_JOBS_ACT, 16),
        LookupStr(FundingCategory.INFORMATION_AND_STATISTICS, 17),
        LookupStr(FundingCategory.INCOME_SECURITY_AND_SOCIAL_SERVICES, 18),
        LookupStr(FundingCategory.LAW_JUSTICE_AND_LEGAL_SERVICES, 19),
        LookupStr(FundingCategory.NATURAL_RESOURCES, 20),
        LookupStr(FundingCategory.OPPORTUNITY_ZONE_BENEFITS, 21),
        LookupStr(FundingCategory.REGIONAL_DEVELOPMENT, 22),
        LookupStr(FundingCategory.SCIENCE_TECHNOLOGY_AND_OTHER_RESEARCH_AND_DEVELOPMENT, 23),
        LookupStr(FundingCategory.TRANSPORTATION, 24),
        LookupStr(FundingCategory.AFFORDABLE_CARE_ACT, 25),
        LookupStr(FundingCategory.OTHER, 26),
        LookupStr(FundingCategory.ENERGY_INFRASTRUCTURE_AND_CRITICAL_MINERAL_AND_MATERIALS, 27),
        LookupStr(FundingCategory.RECREATION_AND_TOURISM, 28),
    ]
)

FUNDING_INSTRUMENT_CONFIG: LookupConfig[FundingInstrument] = LookupConfig(
    [
        LookupStr(FundingInstrument.COOPERATIVE_AGREEMENT, 1),
        LookupStr(FundingInstrument.GRANT, 2),
        LookupStr(FundingInstrument.PROCUREMENT_CONTRACT, 3),
        LookupStr(FundingInstrument.OTHER, 4),
    ]
)

COMPETITION_OPEN_TO_APPLICANT_CONFIG: LookupConfig[CompetitionOpenToApplicant] = LookupConfig(
    [
        LookupStr(CompetitionOpenToApplicant.INDIVIDUAL, 1),
        LookupStr(CompetitionOpenToApplicant.ORGANIZATION, 2),
    ]
)

OPPORTUNITY_AUDIT_EVENT_CONFIG: LookupConfig[OpportunityAuditEvent] = LookupConfig(
    [
        LookupStr(OpportunityAuditEvent.OPPORTUNITY_CREATED, 1),
        LookupStr(OpportunityAuditEvent.OPPORTUNITY_UPDATED, 2),
        LookupStr(OpportunityAuditEvent.OPPORTUNITY_SUMMARY_CREATED, 3),
        LookupStr(OpportunityAuditEvent.OPPORTUNITY_SUMMARY_UPDATED, 4),
        LookupStr(OpportunityAuditEvent.COMPETITION_CREATED, 5),
        LookupStr(OpportunityAuditEvent.COMPETITION_UPDATED, 6),
    ]
)

GRANTOR_ORGANIZATION_AUDIT_EVENT_CONFIG: LookupConfig[GrantorOrganizationAuditEvent] = LookupConfig(
    [LookupStr(GrantorOrganizationAuditEvent.USER_ROLES_MODIFIED, 1)]
)

# Only the values the engine itself needs are seeded here. The find/apply workflow
# and approval types (opportunity_publish, award recommendation review, and so on)
# are deliberately not ported - teams add values as they build real  workflows.
WORKFLOW_TYPE_CONFIG: LookupConfig[WorkflowType] = LookupConfig(
    [
        LookupStr(WorkflowType.BASIC_TEST_WORKFLOW, 1),
        LookupStr(WorkflowType.PROTOTYPE_WORKFLOW, 2),
        LookupStr(WorkflowType.APPROVAL_TEST_WORKFLOW, 3),
        LookupStr(WorkflowType.LIMITED_APPROVAL_TEST_WORKFLOW, 4),
    ]
)

APPROVAL_TYPE_CONFIG: LookupConfig[ApprovalType] = LookupConfig(
    [
        LookupStr(ApprovalType.BASIC_TEST_APPROVAL, 1),
        LookupStr(ApprovalType.SECONDARY_TEST_APPROVAL, 2),
    ]
)

APPROVAL_RESPONSE_TYPE_CONFIG: LookupConfig[ApprovalResponseType] = LookupConfig(
    [
        LookupStr(ApprovalResponseType.APPROVED, 1),
        LookupStr(ApprovalResponseType.DECLINED, 2),
        LookupStr(ApprovalResponseType.REQUIRES_MODIFICATION, 3),
    ]
)

#######################################################
# GrantorLookupTable
#
# Base table that all lookup tables are derived from
#######################################################


class GrantorLookupTable(LookupTable, GrantorSchemaTable):
    """
    Base lookup table class that includes the GrantorSchemasTable as well
    so that the tables end up in the grantor schema.
    """

    __abstract__ = True


#######################################################
# Lookup Tables
#
# Put all lookup table definitions in this section and
# connect them to the lookup configurations defined above
#######################################################


@LookupRegistry.register_lookup(USER_TYPE_CONFIG)
class LkUserType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_user_type"

    user_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkUserType:
        return LkUserType(user_type_id=lookup.lookup_val, description=lookup.get_description())


@LookupRegistry.register_lookup(EXTERNAL_USER_TYPE_CONFIG)
class LkExternalUserType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_external_user_type"

    external_user_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkExternalUserType:
        return LkExternalUserType(
            external_user_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(PRIVILEGE_CONFIG)
class LkPrivilege(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_privilege"

    privilege_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkPrivilege:
        return LkPrivilege(privilege_id=lookup.lookup_val, description=lookup.get_description())


@LookupRegistry.register_lookup(RESOURCE_TYPE_CONFIG)
class LkResourceType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_resource_type"

    resource_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkResourceType:
        return LkResourceType(
            resource_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(GRANTOR_ORGANIZATION_TYPE_CONFIG)
class LkGrantorOrganizationType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_grantor_organization_type"

    grantor_organization_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkGrantorOrganizationType:
        return LkGrantorOrganizationType(
            grantor_organization_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(OPPORTUNITY_CATEGORY_CONFIG)
class LkOpportunityCategory(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_opportunity_category"
    opportunity_category_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkOpportunityCategory:
        return LkOpportunityCategory(
            opportunity_category_id=lookup.lookup_val,
            description=lookup.get_description(),
        )


@LookupRegistry.register_lookup(APPLICANT_TYPE_CONFIG)
class LkApplicantType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_applicant_type"
    applicant_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkApplicantType:
        return LkApplicantType(
            applicant_type_id=lookup.lookup_val,
            description=lookup.get_description(),
        )


@LookupRegistry.register_lookup(FUNDING_CATEGORY_CONFIG)
class LkFundingCategory(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_funding_category"
    funding_category_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkFundingCategory:
        return LkFundingCategory(
            funding_category_id=lookup.lookup_val,
            description=lookup.get_description(),
        )


@LookupRegistry.register_lookup(FUNDING_INSTRUMENT_CONFIG)
class LkFundingInstrument(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_funding_instrument"
    funding_instrument_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkFundingInstrument:
        return LkFundingInstrument(
            funding_instrument_id=lookup.lookup_val,
            description=lookup.get_description(),
        )


@LookupRegistry.register_lookup(COMPETITION_OPEN_TO_APPLICANT_CONFIG)
class LkCompetitionOpenToApplicant(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_competition_open_to_applicant"
    competition_open_to_applicant_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkCompetitionOpenToApplicant:
        return LkCompetitionOpenToApplicant(
            competition_open_to_applicant_id=lookup.lookup_val,
            description=lookup.get_description(),
        )


@LookupRegistry.register_lookup(OPPORTUNITY_AUDIT_EVENT_CONFIG)
class LkOpportunityAuditEvent(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_opportunity_audit_event"
    opportunity_audit_event_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkOpportunityAuditEvent:
        return LkOpportunityAuditEvent(
            opportunity_audit_event_id=lookup.lookup_val,
            description=lookup.get_description(),
        )


@LookupRegistry.register_lookup(PARTNER_AUDIT_EVENT_CONFIG)
class LkPartnerAuditEvent(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_partner_audit_event"

    partner_audit_event_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkPartnerAuditEvent:
        return LkPartnerAuditEvent(
            partner_audit_event_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(GRANTOR_ORGANIZATION_AUDIT_EVENT_CONFIG)
class LkGrantorOrganizationAuditEvent(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_grantor_organization_audit_event"

    grantor_organization_audit_event_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkGrantorOrganizationAuditEvent:
        return LkGrantorOrganizationAuditEvent(
            grantor_organization_audit_event_id=lookup.lookup_val,
            description=lookup.get_description(),
        )


@LookupRegistry.register_lookup(WORKFLOW_TYPE_CONFIG)
class LkWorkflowType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_workflow_type"

    workflow_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkWorkflowType:
        return LkWorkflowType(
            workflow_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(APPROVAL_TYPE_CONFIG)
class LkApprovalType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_approval_type"

    approval_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkApprovalType:
        return LkApprovalType(
            approval_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(APPROVAL_RESPONSE_TYPE_CONFIG)
class LkApprovalResponseType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_approval_response_type"

    approval_response_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkApprovalResponseType:
        return LkApprovalResponseType(
            approval_response_type_id=lookup.lookup_val, description=lookup.get_description()
        )
