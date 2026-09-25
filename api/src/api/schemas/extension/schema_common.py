import dataclasses
import typing


@dataclasses.dataclass
class MarshmallowErrorContainer:
    key: str
    message: str

    value: typing.Any | None = None

    metadata: dict | None = None
