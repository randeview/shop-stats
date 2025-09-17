# users/jwt.py
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def make_tokens_for_user(user: User):
    refresh = RefreshToken.for_user(user)
    refresh["token_version"] = user.token_version
    access = refresh.access_token
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
