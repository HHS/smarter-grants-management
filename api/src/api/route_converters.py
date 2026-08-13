"""Custom URL converters for route path parameters."""

import re
from enum import StrEnum

from werkzeug.routing import BaseConverter, ValidationError


def build_enum_converter(enum_cls: type[StrEnum]) -> type[BaseConverter]:
    """Build a URL converter that accepts only the values of a StrEnum.

    Register the result on the app's url_map, then use it in a route rule::

        app.url_map.converters["resource_type"] = build_enum_converter(MgmtResourceType)

        @blueprint.post("/<resource_type:resource_type>/...")
        def handler(resource_type: MgmtResourceType) -> ...:

    The value arrives at the handler already converted to the enum member. A path
    segment that isn't one of the values doesn't match the rule at all, so it 404s
    rather than reaching the handler.
    """

    class Converter(BaseConverter):
        regex = "(?:" + "|".join(re.escape(member.value) for member in enum_cls) + ")"

        def to_python(self, value: str) -> StrEnum:
            try:
                return enum_cls(value)
            except ValueError as e:
                # The regex above already restricts the path segment to the enum's
                # values - werkzeug treats it as "no match",
                # which surfaces as a 404.
                raise ValidationError() from e

        def to_url(self, value: StrEnum) -> str:
            return value.value

    return Converter
