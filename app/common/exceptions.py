from rest_framework import status
from rest_framework.exceptions import APIException


class DeviceAlreadyRegistered(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Account already registered on another device."
    default_code = "device_conflict"
