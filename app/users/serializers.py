from django.contrib.auth import authenticate
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from app.common.exceptions import DeviceAlreadyRegistered
from app.common.validators import phone_number_validator
from app.users.models import User


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

    def validate_phone_number(self, value: str) -> str:
        # Normalize if you have a normalizer (e.g., strip spaces/+7->8 etc.)
        # value = normalize_phone(value)
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                _("User with this phone number already exists."),
                code="phone_taken",
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        phone = validated_data["phone_number"]
        user = User.objects.create_user(
            username=phone,
            phone_number=phone,
            first_name=validated_data.get("first_name", "") or "",
            last_name=validated_data.get("last_name", "") or "",
            password=validated_data["password"],
            device_id=validated_data["device_id"],
        )
        return user


class LoginInputSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(max_length=128)

    default_error_messages = {
        "invalid_credentials": _("Invalid credentials"),
        "inactive": _("User is inactive"),
    }

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError(
                {"detail": self.error_messages["invalid_credentials"]},
                code="invalid_credentials",
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": self.error_messages["inactive"]},
                code="inactive",
            )

        incoming_device_id = attrs["device_id"]
        current_device_id = getattr(user, "device_id", None)
        if current_device_id and current_device_id != incoming_device_id:
            # Strict: do not allow replacement
            raise DeviceAlreadyRegistered()

        attrs["user"] = user
        return attrs


class TokenPairSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()

    class Meta:
        ref_name = "UserLoginSerializer"


class ProfileOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "phone_number",
            "first_name",
            "last_name",
            "device_id",
            "payment_status",
        )
