import re
from typing import Any

from sqlalchemy import Operators, types
from sqlalchemy.dialects.postgresql.base import PGTypeCompiler, ischema_names
from sqlalchemy.sql import expression

path_matcher = re.compile(r"^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$")


class Ltree:
    """
    Basic class for representing an ltree path. Validates that the path
    is valid, and is expected to be used by the LtreeType below.

    This is a heavily simplified approach from the sqlalchemy_utils library
    https://github.com/kvesteri/sqlalchemy-utils/blob/master/sqlalchemy_utils/types/ltree.py
    """

    def __init__(self, path: str):
        if path_matcher.match(path) is None:
            raise ValueError(f"'{path}' is not a valid ltree path.")

        self.path = path

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path!r})"


class LtreeType(types.Concatenable, types.UserDefinedType):
    """
    A custom SQLAlchemy column type for interacting with Postgres ltree columns
    https://www.postgresql.org/docs/current/ltree.html

    This can be used by defining a column like so::

        class MyExampleTable(GrantorSchemaTable, TimestampMixin):
            __tablename__ = "my_example_table"

            my_example_table_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

            path: Mapped[Ltree | None] = mapped_column(LtreeType)

    The `comparator_factory` defined below implements several comparison
    functions that allow you to use the various ltree comparison and query functions.


    This is based on the approach from the sqlalchemy_utils library
    https://github.com/kvesteri/sqlalchemy-utils/blob/master/sqlalchemy_utils/types/ltree.py

    """

    cache_ok = True

    __visit__name__ = "LTREE"

    class comparator_factory(types.Concatenable.Comparator):
        """
        This comparator factory allows us to have additional comparison
        operations on columns of this type

        For example, the ancestor_of function allows you to do::

            db_session.execute(
                select(ExampleTable).where(
                    ExampleTable.path.ancestor_of(Ltree("X.Y.Z"))
                )
            )
            ```

        See: https://docs.sqlalchemy.org/en/21/core/custom_types.html#redefining-and-creating-new-operators
        See: https://www.postgresql.org/docs/current/ltree.html

        """

        def ancestor_of(self, other: Ltree) -> Operators:
            """
            Compartor function to do an ancestor query against an ltree column

            Renders similar to "... where path @> 'Top.Science'"
            """
            return self.op("@>")(other)

        def descendant_of(self, other: Ltree) -> Operators:
            """
            Compartor function to do a descendant query against an ltree column

            Renders similar to "... where path <@ 'Top.Science'"
            """
            return self.op("<@")(other)

        def lquery(self, other: str) -> Operators:
            """
            Compartor function to do an LQuery filter against an ltree column

            Renders similar to "... where path ~ '*.Astronomy.*'"
            """
            return self.op("~")(expression.cast(other, LQUERY))

        def ltxtquery(self, other: str) -> Operators:
            """
            Compartor function to do a full text search query against an ltree column

            Renders similar to "... where path @ 'Astro*% & !pictures@'"
            """
            return self.op("@")(expression.cast(other, LTXTQUERY))

    def get_col_spec(self, **kwargs: Any) -> str:
        """Get the column name when rendering SQL"""
        return "LTREE"

    def bind_processor(self, dialect: Any) -> Any:
        """Handle conversion from Python->SQL"""

        def process(value: Any) -> str | None:
            if value is None:
                return None

            if isinstance(value, str):
                value = Ltree(value)

            if isinstance(value, Ltree):
                return value.path

            err_msg = f"Cannot convert value of type {type(value)} to ltree column."
            raise ValueError(err_msg)

        return process

    def result_processor(self, dialect: Any, coltype: Any) -> Any:
        """Handle conversion from SQL->Python"""

        def process(value: Any) -> Ltree | None:
            if value:
                return Ltree(value)

            return None

        return process


# Everything below here is needed to tell SQLAlchemy how to render and connect internals together.


class LQUERY(types.TypeEngine):
    """Postgresql LQUERY type."""

    __visit_name__ = "LQUERY"


class LTXTQUERY(types.TypeEngine):
    """Postgresql LTXTQUERY type."""

    __visit_name__ = "LTXTQUERY"


ischema_names["ltree"] = LtreeType
ischema_names["lquery"] = LQUERY
ischema_names["ltxtquery"] = LTXTQUERY


def visit_LTREE(self: PGTypeCompiler, type_: Any, **kw: Any) -> str:
    return "LTREE"


def visit_LQUERY(self: PGTypeCompiler, type_: Any, **kw: Any) -> str:
    return "LQUERY"


def visit_LTXTQUERY(self: PGTypeCompiler, type_: Any, **kw: Any) -> str:
    return "LTXTQUERY"


PGTypeCompiler.visit_LTREE = visit_LTREE  # type: ignore[attr-defined]
PGTypeCompiler.visit_LQUERY = visit_LQUERY  # type: ignore[attr-defined]
PGTypeCompiler.visit_LTXTQUERY = visit_LTXTQUERY  # type: ignore[attr-defined]
