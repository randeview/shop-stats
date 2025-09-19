from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView

from app.common.exceptions import DeviceRegisteredAnotherUser
from app.common.permissions import DeviceBound
from app.users.jwt import make_tokens_for_user
from app.users.serializers import (
    LoginInputSerializer,
    ProfileOutputSerializer,
    RegisterSerializer,
    TokenPairSerializer,
)

User = get_user_model()


@extend_schema(
    tags=["auth"],
    summary=_("User registration"),
    request=RegisterSerializer,
    responses={
        status.HTTP_201_CREATED: RegisterSerializer,
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(description=_("Validation error")),
    },
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [throttling.AnonRateThrottle]


@extend_schema(
    tags=["auth"],
    summary=_("User login"),
    request=LoginInputSerializer,
    responses={status.HTTP_200_OK: TokenPairSerializer},
)
class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    throttle_classes = [throttling.AnonRateThrottle]

    def post(self, request):
        ser = LoginInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        user = ser.validated_data["user"]
        incoming_device_id = ser.validated_data["device_id"]

        if not getattr(user, "device_id", None):
            if User.objects.filter(device_id=incoming_device_id).exists():
                raise DeviceRegisteredAnotherUser()
            user.device_id = incoming_device_id
            user.save(update_fields=["device_id"])

        # Token bump (invalidate previous token versions if you use that pattern)
        user.bump_token_version()

        # Include device_id in JWT claims (enforced by permission/middleware)
        refresh, access = make_tokens_for_user(user, incoming_device_id)

        out = TokenPairSerializer({"refresh": refresh, "access": access})
        return Response(out.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["auth"],
    summary=_("User logout (invalidate tokens)"),
    responses={
        status.HTTP_204_NO_CONTENT: OpenApiResponse(description=_("No content"))
    },
)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated, DeviceBound]

    def post(self, request):
        request.user.bump_token_version()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["auth"],
    summary=_("User profile"),
    responses={status.HTTP_200_OK: ProfileOutputSerializer},
)
class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, DeviceBound]
    serializer_class = ProfileOutputSerializer

    def get_object(self):
        return self.request.user
