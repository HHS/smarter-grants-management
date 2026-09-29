from enum import StrEnum

from pydantic import BaseModel


class StrSearchFilter(BaseModel):
    # str | StrEnum keeps Pydantic from converting
    # something that is a StrEnum to just a string
    # helping preserve the type where relevant like
    # when we do a SQLAlchemy where clause
    one_of: list[str | StrEnum] | None = None
