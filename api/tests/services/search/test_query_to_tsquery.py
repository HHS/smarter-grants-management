from sqlalchemy import func, select

from src.services.search.query_to_tsquery import query_to_tsquery


def convert_and_validate(db_session, query, expected_query):
    assert query_to_tsquery(query) == expected_query

    if expected_query is None:
        return

    # Make sure that all of the queries that come out of this are valid
    # This'll do a "select to_tsquery('<whatever'>)
    db_session.execute(select(func.to_tsquery(expected_query)))


def test_query_to_tsquery(db_session):
    # All empty/none end up None
    convert_and_validate(db_session, None, None)
    convert_and_validate(db_session, "", None)
    convert_and_validate(db_session, "   ", None)
    convert_and_validate(db_session, " \t \n  ", None)

    # Basic & prefix
    convert_and_validate(db_session, "dog", "dog")
    convert_and_validate(db_session, "dog*", "dog:*")
    convert_and_validate(db_session, "dog:*", "dog:*")

    # AND support
    convert_and_validate(db_session, "dog cat", "dog & cat")
    convert_and_validate(db_session, "dog AND cat", "dog & cat")

    # OR support
    convert_and_validate(db_session, "dog or cat", "dog | cat")
    convert_and_validate(db_session, "dog OR cat", "dog | cat")

    # Filtering out junk characters
    convert_and_validate(db_session, "dog %%@#$@%#$^ cat", "dog & cat")
    convert_and_validate(db_session, "dog bi@#@#@#@#rd cat", "dog & bird & cat")

    # Quotes aren't handled special, just stripped out
    convert_and_validate(db_session, '"dog cat"', "dog & cat")

    # Mixed
    convert_and_validate(db_session, "-dog* cat", "!dog:* & cat")
    convert_and_validate(db_session, "dog -%%@#$fish@%#$^ cat", "dog & !fish & cat")
