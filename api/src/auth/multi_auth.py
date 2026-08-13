from apiflask import MultiAuth

from src.auth.api_jwt_auth import api_jwt_auth
from src.auth.api_user_key_auth import api_user_key_auth
from src.db.models.user_models import User, UserApiKey, UserTokenSession


class MultiHttpTokenAuth(MultiAuth):
    def get_user(self) -> User:
        current_user = self.current_user

        if isinstance(current_user, (UserTokenSession, UserApiKey)):
            return current_user.user

        raise Exception(f"Unsupported user type: {type(current_user)}")


# Define the multi auth that supports
# * User JWT auth
# * API User Key Auth
#
# Note that the order defined matters - earlier ones will take precedence in
# the event a user provides us with multiple auth approaches at once, only the first
# relevant one will be used.
# We define the JWT auth first as the frontend will pass us a users JWT
# and the frontend's API key for all user-based requests in order to validate
# with our API gateway that handles rate limiting.
jwt_or_api_user_key_multi_auth = MultiHttpTokenAuth(api_jwt_auth, api_user_key_auth)
