from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class HasPaidService(BasePermission):
    message = "Service not paid"

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.payment_status)


class DeviceBound(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated:
            header_did = request.headers.get("X-Device-ID")
            if not user.device_id or header_did != user.device_id:
                raise AuthenticationFailed("Invalid device.")
        return True
