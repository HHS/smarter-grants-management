import abc
import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.adapters import db
from src.constants.lookup_constants import ExternalUserType
from src.db.models.auth_base_models import (
    BaseLinkExternalUser,
    BaseLoginGovState,
    BaseUser,
    BaseUserApiKey,
    BaseUserTokenSession,
)
from src.db.models.user_models import (
    LinkExternalUser,
    LoginGovState,
    User,
    UserApiKey,
    UserTokenSession,
)


# Type parameters bind the abstract models to concrete tables so handlers avoid casting.
# Multi-letter names (rather than the usual single letter) since there are five.
class AbstractAuthHandler[
    USER: BaseUser,
    LINK_EXTERNAL: BaseLinkExternalUser,
    LOGIN_GOV_STATE: BaseLoginGovState,
    USER_API_KEY: BaseUserApiKey,
    USER_TOKEN_SESSION: BaseUserTokenSession,
](abc.ABC, metaclass=abc.ABCMeta):
    """Defines the DB interactions the auth flow relies on, in terms of abstract models.

    Concrete implementations supply the actual queries and object construction against
    real tables, binding the type parameters to their concrete models.
    """

    def __init__(self, db_session: db.Session):
        self.db_session = db_session

    # --- User token sessions ---

    @abc.abstractmethod
    def create_token_session(
        self, user: USER, token_id: uuid.UUID, expires_at: datetime
    ) -> USER_TOKEN_SESSION: ...

    @abc.abstractmethod
    def get_token_session_by_token_id(self, token_id: str) -> USER_TOKEN_SESSION | None: ...

    # --- API keys ---

    @abc.abstractmethod
    def get_api_key_by_key_id(self, key_id: str) -> USER_API_KEY | None: ...

    @abc.abstractmethod
    def create_api_key(self, user_id: uuid.UUID, key_name: str, key_id: str) -> USER_API_KEY: ...

    @abc.abstractmethod
    def list_api_keys_for_user(self, user_id: uuid.UUID) -> Sequence[USER_API_KEY]: ...

    @abc.abstractmethod
    def get_api_key_for_user(
        self, user_id: uuid.UUID, api_key_id: uuid.UUID
    ) -> USER_API_KEY | None: ...

    # --- login.gov state ---

    @abc.abstractmethod
    def create_login_gov_state(self, state_id: uuid.UUID, nonce: uuid.UUID) -> LOGIN_GOV_STATE: ...

    @abc.abstractmethod
    def get_login_gov_state(self, state_id: str) -> LOGIN_GOV_STATE | None: ...

    # --- External user link / user creation ---

    @abc.abstractmethod
    def get_link_external_user(self, external_user_id: str) -> LINK_EXTERNAL | None: ...

    @abc.abstractmethod
    def create_user_with_external_link(self, external_user_id: str) -> LINK_EXTERNAL: ...

    @abc.abstractmethod
    def get_user_for_external_link(self, external_user: LINK_EXTERNAL) -> USER: ...


class AuthHandler(
    AbstractAuthHandler[User, LinkExternalUser, LoginGovState, UserApiKey, UserTokenSession]
):
    """Concrete auth handler backed by the grants management user tables."""

    # --- User token sessions ---

    def create_token_session(
        self, user: User, token_id: uuid.UUID, expires_at: datetime
    ) -> UserTokenSession:
        user_token_session = UserTokenSession(user=user, token_id=token_id, expires_at=expires_at)
        self.db_session.add(user_token_session)
        return user_token_session

    def get_token_session_by_token_id(self, token_id: str) -> UserTokenSession | None:
        return self.db_session.execute(
            select(UserTokenSession)
            .where(UserTokenSession.token_id == token_id)
            .options(selectinload(UserTokenSession.user))
        ).scalar()

    # --- API keys ---

    def get_api_key_by_key_id(self, key_id: str) -> UserApiKey | None:
        return self.db_session.execute(
            select(UserApiKey)
            .where(UserApiKey.key_id == key_id)
            .options(selectinload(UserApiKey.user))
        ).scalar_one_or_none()

    def create_api_key(self, user_id: uuid.UUID, key_name: str, key_id: str) -> UserApiKey:
        api_key = UserApiKey(
            api_key_id=uuid.uuid4(),
            user_id=user_id,
            key_name=key_name,
            key_id=key_id,
            is_active=True,
        )
        self.db_session.add(api_key)
        return api_key

    def list_api_keys_for_user(self, user_id: uuid.UUID) -> Sequence[UserApiKey]:
        result = self.db_session.execute(
            select(UserApiKey)
            .where(UserApiKey.user_id == user_id)
            .order_by(UserApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    def get_api_key_for_user(self, user_id: uuid.UUID, api_key_id: uuid.UUID) -> UserApiKey | None:
        return self.db_session.execute(
            select(UserApiKey).filter(
                UserApiKey.api_key_id == api_key_id,
                UserApiKey.user_id == user_id,
            )
        ).scalar_one_or_none()

    # --- login.gov state ---

    def create_login_gov_state(self, state_id: uuid.UUID, nonce: uuid.UUID) -> LoginGovState:
        login_gov_state = LoginGovState(login_gov_state_id=state_id, nonce=nonce)
        self.db_session.add(login_gov_state)
        return login_gov_state

    def get_login_gov_state(self, state_id: str) -> LoginGovState | None:
        return self.db_session.execute(
            select(LoginGovState).where(LoginGovState.login_gov_state_id == state_id)
        ).scalar_one_or_none()

    # --- External user link / user creation ---

    def get_link_external_user(self, external_user_id: str) -> LinkExternalUser | None:
        return self.db_session.execute(
            select(LinkExternalUser)
            .where(LinkExternalUser.external_user_id == external_user_id)
            # We only support login.gov right now, so this does nothing, but let's
            # be explicit just in case.
            .where(LinkExternalUser.external_user_type == ExternalUserType.LOGIN_GOV)
            .options(selectinload(LinkExternalUser.user))
        ).scalar()

    def create_user_with_external_link(self, external_user_id: str) -> LinkExternalUser:
        user = User()
        self.db_session.add(user)

        external_user = LinkExternalUser(
            user=user,
            external_user_type=ExternalUserType.LOGIN_GOV,
            external_user_id=external_user_id,
            # note we set other params in the calling method to also handle updates
        )
        self.db_session.add(external_user)

        return external_user

    def get_user_for_external_link(self, external_user: LinkExternalUser) -> User:
        return external_user.user
