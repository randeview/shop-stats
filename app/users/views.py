from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.exceptions import DeviceAlreadyRegistered
from ..common.permissions import DeviceBound
from ..common.validators import phone_number_validator
from .jwt import make_tokens_for_user

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    class RegisterSerializer(serializers.ModelSerializer):
        password = serializers.CharField(write_only=True, min_length=6)
        phone_number = serializers.CharField(validators=[phone_number_validator])
        device_id = serializers.CharField(max_length=128)

        class Meta:
            model = User
            fields = (
                "id",
                "phone_number",
                "first_name",
                "last_name",
                "password",
                "device_id",
            )

        def create(self, validated_data):
            phone_number = validated_data["phone_number"]
            if User.objects.filter(username=phone_number).exists():
                raise serializers.ValidationError(
                    "User with this phone number already exists."
                )
            return User.objects.create_user(
                username=phone_number,
                phone_number=phone_number,
                first_name=validated_data.get("first_name", ""),
                last_name=validated_data.get("last_name", ""),
                password=validated_data["password"],
                device_id=validated_data["device_id"],
            )

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    class InputSerializer(serializers.Serializer):
        username = serializers.CharField()
        password = serializers.CharField(write_only=True)
        device_id = serializers.CharField(max_length=128)

        def validate(self, attrs):
            user = authenticate(username=attrs["username"], password=attrs["password"])
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_active:
                raise serializers.ValidationError("User is inactive")
            incoming_device_id = attrs["device_id"]
            current_device_id = getattr(user, "device_id", None)
            if current_device_id and current_device_id != incoming_device_id:
                raise DeviceAlreadyRegistered()
            attrs["user"] = user
            return attrs

    class OutputSerializer(serializers.Serializer):
        refresh = serializers.CharField()
        access = serializers.CharField()

        class Meta:
            ref_name = "UserLoginSerializer"

    @extend_schema(
        request=InputSerializer, responses={status.HTTP_200_OK: OutputSerializer}
    )
    def post(self, request):
        ser = self.InputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]
        incoming_device_id = ser.validated_data["device_id"]
        if not getattr(user, "device_id", None):
            user.device_id = incoming_device_id
            user.save(update_fields=["device_id"])
        user.bump_token_version()
        refresh, access = make_tokens_for_user(user, incoming_device_id)
        return Response(
            {"refresh_token": refresh, "access_token": access},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    def post(self, request):
        user = request.user
        user.bump_token_version()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, DeviceBound]

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = (
                "id",
                "username",
                "phone_number",
                "first_name",
                "last_name",
                "device_id",
            )

    serializer_class = OutputSerializer

    @extend_schema(responses={status.HTTP_200_OK: OutputSerializer})
    def get_object(self):
        return self.request.user
