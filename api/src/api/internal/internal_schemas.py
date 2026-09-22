from src.api.schemas.extension import Schema, fields
from src.api.schemas.response_schema import AbstractResponseSchema


class ApiJwtSchema(Schema):
    jwt_token = fields.String(
        metadata={"description": "JWT token that can be used to authenticate the user"}
    )


class ApiJwtResponseSchema(AbstractResponseSchema):
    data = fields.Nested(ApiJwtSchema())
