from sqlalchemy import func, select

from src.db.models.assistance_listing_models import AssistanceListing
from src.services.search.query_to_tsquery import query_to_tsquery
from tests.db.models.factories import AssistanceListingFactory


def fetch_and_validate_results(db_session, query: str, expected_results: list[str]):

    results = (
        db_session.execute(
            select(AssistanceListing)
            .where(
                AssistanceListing.program_title.op("@@")(func.to_tsquery(query_to_tsquery(query)))
            )
            .where(AssistanceListing.assistance_listing_number.startswith("TS.A"))
        )
        .scalars()
        .all()
    )

    assistance_listing_numbers = set(
        [assistance_listing.assistance_listing_number for assistance_listing in results]
    )

    assert assistance_listing_numbers == set(expected_results)


def test_program_title_ts_queries(db_session, enable_factory_create):

    AssistanceListingFactory.create(
        assistance_listing_number="TS.A01", program_title="chemical processing"
    )
    AssistanceListingFactory.create(assistance_listing_number="TS.A02", program_title="chemistry")
    AssistanceListingFactory.create(
        assistance_listing_number="TS.A03", program_title="chemotherapy"
    )
    AssistanceListingFactory.create(assistance_listing_number="TS.A04", program_title="chair")
    AssistanceListingFactory.create(
        assistance_listing_number="TS.A05", program_title="special project"
    )

    fetch_and_validate_results(db_session, "chem*", ["TS.A01", "TS.A02", "TS.A03"])
    fetch_and_validate_results(db_session, "chemistry", ["TS.A02"])
    fetch_and_validate_results(db_session, "chem* AND processing", ["TS.A01"])
    fetch_and_validate_results(db_session, "pro*", ["TS.A01", "TS.A05"])
    fetch_and_validate_results(db_session, "ch*", ["TS.A01", "TS.A02", "TS.A03", "TS.A04"])
    fetch_and_validate_results(db_session, "something else", [])
