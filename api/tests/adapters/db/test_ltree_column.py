import uuid

import pytest
from sqlalchemy import UUID, select
from sqlalchemy.exc import ProgrammingError, StatementError
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters import db
from src.adapters.db.ltree_column import Ltree, LtreeType
from src.db.models import metadata
from src.db.models.grantor_schema_table import GrantorSchemaTable
from tests.test_utils import db_testing


class LtreeTestTable(GrantorSchemaTable):
    __tablename__ = "ltree_test_table"

    ltree_test_table_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    path: Mapped[Ltree | None] = mapped_column(LtreeType)


############
# Fixtures
############


@pytest.fixture(scope="module")
def isolated_db(monkeypatch_module) -> db.PostgresDBClient:
    """
    Create an isolated Postgres db that only contains the above table.

    Scoped to module, so all below tests run in the same schema with the same data.
    """
    with db_testing.create_isolated_db(
        monkeypatch_module, f"test_ltree_{uuid.uuid4().int}_"
    ) as db_client:
        metadata.create_all(bind=db_client._engine, tables=[LtreeTestTable.__table__])
        # Skipping the sync that normally occurs to do in tests below
        yield db_client


@pytest.fixture
def isolated_db_session(isolated_db):
    with isolated_db.get_session() as session:
        yield session


############
# Validation
############


def validate_descendants(db_session, path: str, expected_results: list[LtreeTestTable]) -> None:
    results = db_session.execute(
        select(LtreeTestTable).where(LtreeTestTable.path.descendant_of(path))
    ).scalars()

    result_ids = {result.ltree_test_table_id for result in results}
    expected_ids = {expected.ltree_test_table_id for expected in expected_results}

    assert result_ids == expected_ids, f"Results differ for descendant path query {path}"


def validate_ancestors(db_session, path: str, expected_results: list[LtreeTestTable]) -> None:
    results = db_session.execute(
        select(LtreeTestTable).where(LtreeTestTable.path.ancestor_of(path))
    ).scalars()

    result_ids = {result.ltree_test_table_id for result in results}
    expected_ids = {expected.ltree_test_table_id for expected in expected_results}

    assert result_ids == expected_ids, f"Results differ for ancestor path query {path}"


def validate_lquery(db_session, query: str, expected_results: list[LtreeTestTable]) -> None:
    results = db_session.execute(
        select(LtreeTestTable).where(LtreeTestTable.path.lquery(query))
    ).scalars()

    result_ids = {result.ltree_test_table_id for result in results}
    expected_ids = {expected.ltree_test_table_id for expected in expected_results}

    assert result_ids == expected_ids, f"Results differ for lquery {query}"


def validate_ltxtquery(db_session, query: str, expected_results: list[LtreeTestTable]) -> None:
    results = db_session.execute(
        select(LtreeTestTable).where(LtreeTestTable.path.ltxtquery(query))
    ).scalars()

    result_ids = {result.ltree_test_table_id for result in results}
    expected_ids = {expected.ltree_test_table_id for expected in expected_results}

    assert result_ids == expected_ids, f"Results differ for ltxtquery {query}"


############
# Tests
############


@pytest.mark.parametrize("path", ["x.y.z", "X.y.Z", "a", "a-b-c.x-y-z"])
def test_valid_ltree_paths(path):
    assert Ltree(path).path == path


@pytest.mark.parametrize("path", ["this has spaces", "!#@$%#$&^$*&(^(^&&%$^$%^", ""])
def test_invalid_ltree_paths(path):
    with pytest.raises(ValueError, match="is not a valid ltree path"):
        Ltree(path)


def test_queries(isolated_db_session):
    """
    This test copies the example from the Postgres docs at
    https://www.postgresql.org/docs/current/ltree.html

    and verifies we produce the same results. It adds a
    few additional tests as well.
    """

    top = LtreeTestTable(path=Ltree("Top"))
    science = LtreeTestTable(path=Ltree("Top.Science"))
    science_astronomy = LtreeTestTable(path=Ltree("Top.Science.Astronomy"))
    science_astronomy_astrophysics = LtreeTestTable(
        path=Ltree("Top.Science.Astronomy.Astrophysics")
    )
    science_astronomy_cosmology = LtreeTestTable(path=Ltree("Top.Science.Astronomy.Cosmology"))
    hobbies = LtreeTestTable(path=Ltree("Top.Hobbies"))
    hobbies_amateurastronomy = LtreeTestTable(path=Ltree("Top.Hobbies.Amateurs_Astronomy"))
    collections = LtreeTestTable(path=Ltree("Top.Collections"))
    collections_pictures = LtreeTestTable(path=Ltree("Top.Collections.Pictures"))
    collections_pictures_astronomy = LtreeTestTable(
        path=Ltree("Top.Collections.Pictures.Astronomy")
    )
    collections_pictures_astronomy_stars = LtreeTestTable(
        path=Ltree("Top.Collections.Pictures.Astronomy.Stars")
    )
    collections_pictures_astronomy_galaxies = LtreeTestTable(
        path=Ltree("Top.Collections.Pictures.Astronomy.Galaxies")
    )
    collections_pictures_astronomy_astronauts = LtreeTestTable(
        path=Ltree("Top.Collections.Pictures.Astronomy.Astronauts")
    )

    all_records = [
        top,
        science,
        science_astronomy,
        science_astronomy_astrophysics,
        science_astronomy_cosmology,
        hobbies,
        hobbies_amateurastronomy,
        collections,
        collections_pictures,
        collections_pictures_astronomy,
        collections_pictures_astronomy_astronauts,
        collections_pictures_astronomy_galaxies,
        collections_pictures_astronomy_stars,
    ]
    isolated_db_session.add_all(all_records)

    isolated_db_session.commit()

    # Descendants
    validate_descendants(isolated_db_session, "Top", all_records)
    validate_descendants(
        isolated_db_session,
        "Top.Science",
        [science, science_astronomy, science_astronomy_astrophysics, science_astronomy_cosmology],
    )
    validate_descendants(isolated_db_session, "Top.Hobbies", [hobbies, hobbies_amateurastronomy])
    validate_descendants(
        isolated_db_session,
        "Top.Collections",
        [
            collections,
            collections_pictures,
            collections_pictures_astronomy,
            collections_pictures_astronomy_astronauts,
            collections_pictures_astronomy_galaxies,
            collections_pictures_astronomy_stars,
        ],
    )
    validate_descendants(isolated_db_session, "Not-a-value.a.b", [])

    # Ancestors
    validate_ancestors(isolated_db_session, "Top", [top])
    validate_ancestors(isolated_db_session, "Top.Science", [top, science])
    validate_ancestors(
        isolated_db_session,
        "Top.Collections.Pictures.Astronomy.Galaxies",
        [
            top,
            collections,
            collections_pictures,
            collections_pictures_astronomy,
            collections_pictures_astronomy_galaxies,
        ],
    )
    validate_ancestors(isolated_db_session, "X.Y.Z", [])

    # LQuery
    validate_lquery(
        isolated_db_session,
        "*.Astronomy.*",
        [
            science_astronomy,
            science_astronomy_astrophysics,
            science_astronomy_cosmology,
            collections_pictures_astronomy,
            collections_pictures_astronomy_astronauts,
            collections_pictures_astronomy_galaxies,
            collections_pictures_astronomy_stars,
        ],
    )
    validate_lquery(
        isolated_db_session,
        "*.!pictures@.Astronomy.*",
        [science_astronomy, science_astronomy_astrophysics, science_astronomy_cosmology],
    )
    validate_lquery(isolated_db_session, "Top.*", all_records)
    validate_lquery(
        isolated_db_session,
        "*.Astronomy.Astro*",
        [science_astronomy_astrophysics, collections_pictures_astronomy_astronauts],
    )

    # Ltxtquery
    validate_ltxtquery(
        isolated_db_session,
        "Astro*% & !pictures@",
        [
            science_astronomy,
            science_astronomy_astrophysics,
            science_astronomy_cosmology,
            hobbies_amateurastronomy,
        ],
    )
    validate_ltxtquery(
        isolated_db_session,
        "Astro* & !pictures@",
        [science_astronomy, science_astronomy_astrophysics, science_astronomy_cosmology],
    )
    validate_ltxtquery(isolated_db_session, "Astrodynamics* & !pictures@", [])
    validate_ltxtquery(
        isolated_db_session,
        "Astro* & !pictures@ & !cosmology@",
        [science_astronomy, science_astronomy_astrophysics],
    )


def test_dashes_in_path(isolated_db_session):
    uuid1 = uuid.uuid4()
    uuid2 = uuid.uuid4()
    record = LtreeTestTable(path=Ltree(f"{uuid1}.{uuid2}"))
    isolated_db_session.add(record)
    isolated_db_session.commit()

    validate_descendants(isolated_db_session, str(uuid1), [record])
    validate_lquery(isolated_db_session, f"{uuid1}.*", [record])
    validate_lquery(isolated_db_session, f"*.{uuid2}", [record])


def test_null_path(isolated_db_session):
    """Test that null paths convert to/from the DB as expected"""

    record = LtreeTestTable(path=None)
    isolated_db_session.add(record)
    isolated_db_session.commit()

    isolated_db_session.expire_all()

    isolated_db_session.refresh(record)

    assert record.path is None


@pytest.mark.parametrize("path", [45, "spaces are bad", "!@#%%"])
def test_invalid_descendant_ancestor_queries(isolated_db_session, path):

    with pytest.raises(StatementError):
        isolated_db_session.execute(
            select(LtreeTestTable).where(LtreeTestTable.path.descendant_of(path))
        )

    with pytest.raises(StatementError):
        isolated_db_session.execute(
            select(LtreeTestTable).where(LtreeTestTable.path.ancestor_of(path))
        )


def test_invalid_lquery(isolated_db_session):
    with pytest.raises(ProgrammingError):
        isolated_db_session.execute(
            select(LtreeTestTable).where(LtreeTestTable.path.lquery("invalid query"))
        )


def test_invalid_ltxtquery(isolated_db_session):
    with pytest.raises(ProgrammingError):
        isolated_db_session.execute(
            select(LtreeTestTable).where(LtreeTestTable.path.ltxtquery("!@#$@%$#^%"))
        )
