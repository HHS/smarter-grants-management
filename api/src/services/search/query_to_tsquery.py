import re

_TOKEN_RE = re.compile(r"\S+")
_WORD_RE = re.compile(r"\w+", re.UNICODE)


def query_to_tsquery(query: str | None) -> str | None:
    """
    Converts a query string that a user might pass in to one that is safe to
    use with a to_tsquery Postgres query.

    Example::

        my_query = "dog* -cat"
        updated_query = query_to_tsquery(my_query) # "dog:* & !cat"

        results = (
            db_session.execute(
                select(ExampleTable)
                .where(
                    ExampleTable.example_column.op("@@")(func.to_tsquery(updated_query))
                )
            )
            .scalars()
            .all()
        )

    See: https://www.postgresql.org/docs/current/textsearch-controls.html
    """
    if query is None:
        return None

    # split on any word boundaries
    raw_terms = _TOKEN_RE.findall(query.strip())
    if not raw_terms:
        return None

    parts: list[str] = []
    pending_or = False

    for term in raw_terms:
        # AND is the default behavior, so skip that term
        if term.upper() == "AND":
            continue

        # If the term is OR, we'll concatenate the term together with |
        if term.upper() == "OR":
            pending_or = True
            continue

        # Negation is passed in as "-", but Postgres needs
        # ! for the prefix, so flag the term, and trim that out.
        negate = term.startswith("-")
        if negate:
            term = term[1:]

        # Filter out anything that isn't words (eg. drop a word that is just random symbols)
        # If a word has random symbols in it, they get dropped here, but the word is retained.
        # eg. do%#^%^%$&g -> dog
        words = _WORD_RE.findall(term)
        if not words:
            continue
        word = "".join(words)

        # If the term ended with a *, add it back as :* for prefix matching
        clause = f"{word}:*" if term.endswith("*") else word

        # Add negation if calculated earlier
        if negate:
            clause = f"!{clause}"

        # Add | or & for concatenating parts together.
        if parts:
            op = "|" if pending_or else "&"
            parts.append(op)

        parts.append(clause)
        pending_or = False

    return " ".join(parts)
