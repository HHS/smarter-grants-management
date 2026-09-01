from typing import TypeVar

from src.adapters.db.lookup import Lookup
from src.db.models.base import Base

L = TypeVar("L", bound="LookupTable")


class LookupTable(Base):
    __abstract__ = True

    @classmethod
    def from_lookup(cls: type[L], lookup: Lookup) -> L:
        raise NotImplementedError(f"from_lookup must be implemented by {cls.__name__}")
