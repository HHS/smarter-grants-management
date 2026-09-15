import dataclasses

from src.constants.lookup_constants import FormFamily


@dataclasses.dataclass
class Form:
    form_id: int
    agency_code: str
    name: str
    short_name: str
    version: str
    form_family: list[FormFamily]

SF424 = Form(
    form_id=713,
    agency_code="Grants.gov",
    name="Application for Federal Assistance (SF-424)",
    short_name="SF424",
    version="4.0",
    form_family=[FormFamily.SF_424]
)

SF424_RR = Form(
    form_id=768,
    agency_code="Grants.gov",
    name="SF424 (R & R)",
    short_name="RR_SF424",
    version="5.0",
    form_family=[FormFamily.RR]
)

SF424A = Form(
    form_id=241,
    agency_code="Grants.gov",
    name="Budget Information for Non-Construction Programs (SF-424A)",
    short_name="SF424A",
    version="1.0",
    form_family=[FormFamily.SF_424, FormFamily.SF_424_INDIVIDUAL, FormFamily.SF_424_MANDATORY, FormFamily.SF_424_SHORT_ORGANIZATION, FormFamily.RR]
)

PROJECT_ABSTRACT_SUMMARY = Form(
    form_id=591,
    agency_code="Grants.gov",
    name="Project Abstract Summary",
    short_name="Project_AbstractSummary",
    version="2.0",
    form_family=[FormFamily.SF_424, FormFamily.SF_424_MANDATORY, FormFamily.SF_424_SHORT_ORGANIZATION, FormFamily.RR]
)

LOBBYING_FORM = Form(
    form_id=255,
    agency_code="Grants.gov",
    name="Grants.gov Lobbying Form",
    short_name="GG_LobbyingForm",
    version="1.1",
    form_family=[FormFamily.SF_424, FormFamily.SF_424_MANDATORY, FormFamily.SF_424_SHORT_ORGANIZATION, FormFamily.RR]
)

ALL_FORMS = [SF424, SF424_RR, SF424A, PROJECT_ABSTRACT_SUMMARY, LOBBYING_FORM]

def list_forms() -> list[Form]:
    """Get forms, for now this just returns a static list until we build something better."""
    return ALL_FORMS