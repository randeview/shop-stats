# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.common.validators import phone_number_validator


class User(AbstractUser):
    # число, которое будет попадать в JWT и позволит инвалидировать старые токены
    token_version = models.PositiveIntegerField(default=1)
    phone_number = models.CharField(
        _("phone number"),
        max_length=20,
        validators=[phone_number_validator],
        blank=True,
    )

    def bump_token_version(self):
        self.token_version = (self.token_version or 0) + 1
        self.save(update_fields=["token_version"])
