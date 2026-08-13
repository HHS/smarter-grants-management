import uuid
from typing import Any

from grants_shared.adapters.db.type_decorators.postgres_type_decorators import LookupColumn
from grants_shared.db.models.auth_base_models import (
    BaseLinkExternalUser,
    BaseLoginGovState,
    BaseUser,
    BaseUserApiKey,
    BaseUserTokenSession,
)
from grants_shared.db.models.base import TimestampMixin
from sqlalchemy import UUID, ForeignKey, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants.lookup_constants import ExternalUserType, UserType
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import LkExternalUserType, LkUserType


class User(BaseUser, GrantorSchemaTable, TimestampMixin):
    __tablename__ = "user"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    user_type: Mapped[UserType | None] = mapped_column(
        "user_type_id",
        LookupColumn(LkUserType),
        ForeignKey(LkUserType.user_type_id),
        default=UserType.STANDARD,
    )

    linked_login_gov_external_user: Mapped[LinkExternalUser | None] = relationship(
        "LinkExternalUser",
        primaryjoin=lambda: and_(
            LinkExternalUser.user_id == User.user_id,
            LinkExternalUser.external_user_type == ExternalUserType.LOGIN_GOV,
        ),
        uselist=False,
        viewonly=True,
    )

    api_keys: Mapped[list[UserApiKey]] = relationship(
        "UserApiKey",
        back_populates="user",
        uselist=True,
        cascade="all, delete-orphan",
    )

    @property
    def email(self) -> str | None:
        if self.linked_login_gov_external_user is not None:
            return self.linked_login_gov_external_user.email
        return None


class LinkExternalUser(BaseLinkExternalUser, GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_external_user"

    link_external_user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    external_user_type: Mapped[ExternalUserType] = mapped_column(
        "external_user_type_id",
        LookupColumn(LkExternalUserType),
        ForeignKey(LkExternalUserType.external_user_type_id),
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(User.user_id), index=True)
    user: Mapped[User] = relationship(User)

    # Columns defined in base table
    # external_user_id
    # email


class UserTokenSession(BaseUserTokenSession, GrantorSchemaTable, TimestampMixin):
    __tablename__ = "user_token_session"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(User.user_id), primary_key=True)
    user: Mapped[User] = relationship(User)

    token_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    # Columns defined in base table:
    # expires_at
    # is_valid

    def get_log_extra(self) -> dict[str, Any]:
        """Get logging info"""
        return {
            "auth.token_id": self.token_id,
            "auth.user_id": self.user_id,
        }


class LoginGovState(BaseLoginGovState, GrantorSchemaTable, TimestampMixin):
    """Table used to store temporary state during the OAuth login flow"""

    __tablename__ = "login_gov_state"

    login_gov_state_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)

    # nonce in base table


class UserApiKey(BaseUserApiKey, GrantorSchemaTable, TimestampMixin):
    """API Key table for user authentication to the API"""

    __tablename__ = "user_api_key"

    api_key_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(User.user_id), index=True)

    user: Mapped[User] = relationship(User, back_populates="api_keys", uselist=False)

    # Defined in base table
    # key_name
    # key_id
    # last_used
    # is_active

    def get_log_extra(self) -> dict[str, Any]:
        """Get logging info"""
        return {
            "auth.api_key_id": self.api_key_id,
            "auth.user_id": self.user_id,
        }
