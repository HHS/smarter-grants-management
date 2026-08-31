import logging
import uuid
from typing import Self

from sqlalchemy import select

import src.adapters.db as db
import tests.db.models.factories as factories
from src.auth.api_jwt_auth import ApiJwtConfig, create_jwt_for_user
from src.auth.internal_resource import get_internal_resource
from src.constants.lookup_constants import Privilege, ResourceType
from src.db.models.resource_models import ResourceUser
from src.db.models.user_models import User

logger = logging.getLogger(__name__)


class UserBuilder:
    """Builder class for setting up a user for local development"""

    def __init__(self, user_id: uuid.UUID, db_session: db.Session, scenario_name: str) -> None:
        self.user: User = db_session.merge(factories.UserFactory.build(user_id=user_id), load=True)
        self.db_session = db_session
        self.scenario_name = scenario_name

        self.link_external_id = None
        self.api_key_id = None
        self.jwt_token = None
        self.internal_privileges: list[Privilege] = []

    def with_oauth_login(self, external_user_id: str) -> Self:
        """Add an oauth login record that you can use to login as a user

        For example, if you passed in "my_example_user", you could
        manually login to that user by typing "my_example_user" into
        the Mock OAuth login page.
        """
        external_user = self.user.linked_login_gov_external_user
        if external_user is None:
            external_user = factories.LinkExternalUserFactory.build(user=self.user)

        external_user.external_user_id = external_user_id
        self.db_session.add(external_user)

        self.link_external_id = external_user_id
        return self

    def with_jwt_auth(self, token_expiration_minutes: int = 60 * 24 * 365 * 30) -> Self:
        """Add API jwt auth to the user. By default it will expire 30 years in the future for easier development."""
        config = ApiJwtConfig(API_JWT_TOKEN_EXPIRATION_MINUTES=token_expiration_minutes)
        token, _ = create_jwt_for_user(
            self.user, self.db_session, config=config, email=self.user.email
        )
        self.jwt_token = token
        return self

    def with_api_key(self, key_id: str, key_name: str = "Local Development Key") -> Self:
        """Add an API key to the user for X-API-Key authentication.

        For example, if you passed in "my_test_key", you could authenticate
        by passing X-API-Key: my_test_key in your request headers.
        """
        # Check if we previously setup this API key
        user_api_key = None
        for key in self.user.api_keys:
            if key.key_id == key_id:
                user_api_key = key
                break

        if user_api_key is None:
            user_api_key = factories.UserApiKeyFactory.build(user=self.user)

        user_api_key.key_id = key_id
        user_api_key.key_name = key_name
        user_api_key.is_active = True

        self.db_session.add(user_api_key)

        self.api_key_id = key_id
        return self

    def with_internal_privileges(
        self, role_id: uuid.UUID, privileges: list[Privilege], role_name: str
    ) -> Self:
        """Grant the user a role on the internal resource carrying the given privileges."""
        internal_resource = get_internal_resource(self.db_session)

        role = self.db_session.merge(
            factories.RoleFactory.build(
                role_id=role_id,
                role_name=role_name,
                privileges=privileges,
                resource_types=[ResourceType.INTERNAL],
            ),
            load=True,
        )

        # Reuse the user's existing connection to the internal resource if it has one -
        # a user gets at most one per resource.
        resource_user = self.db_session.execute(
            select(ResourceUser).where(
                ResourceUser.resource_id == internal_resource.get_resource_id(),
                ResourceUser.user_id == self.user.user_id,
            )
        ).scalar_one_or_none()

        if resource_user is None:
            resource_user = factories.ResourceUserFactory.build(
                resource=internal_resource.resource, user=self.user
            )
            self.db_session.add(resource_user)

        if role not in resource_user.roles:
            self.db_session.add(
                factories.ResourceUserRoleFactory.build(resource_user=resource_user, role=role)
            )

        self.internal_privileges = privileges
        return self

    def build(self) -> User:
        log_msg = f"Updating {self.scenario_name}:"
        if self.link_external_id:
            log_msg += f" '{self.link_external_id}'"
        if self.jwt_token:
            log_msg += f" with X-MGMT-Token: '{self.jwt_token}'"
        if self.api_key_id:
            log_msg += f" with X-API-Key: '{self.api_key_id}'"
        if self.internal_privileges:
            log_msg += f" with internal privileges: {[p.value for p in self.internal_privileges]}"
        logger.info(log_msg)
        return self.user
