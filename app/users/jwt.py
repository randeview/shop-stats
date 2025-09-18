# users/jwt.py
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from app.users.models import User


def make_tokens_for_user(user: User, incoming_device_id: str):
    refresh = RefreshToken.for_user(user)
    refresh["did"] = incoming_device_id
    refresh["token_version"] = user.token_version
    access = refresh.access_token
    access["did"] = incoming_device_id
    access["token_version"] = user.token_version
    return str(refresh), str(access)


class VersionedJWTAuthentication(JWTAuthentication):
    """
    Проверяет, что token_version в токене совпадает с текущим у пользователя.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        token_version = validated_token.get("token_version")
        if token_version is None or token_version != user.token_version:
            raise exceptions.AuthenticationFailed("Token revoked", code="token_revoked")
        return user
