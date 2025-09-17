# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # число, которое будет попадать в JWT и позволит инвалидировать старые токены
    token_version = models.PositiveIntegerField(default=1)

    def bump_token_version(self):
        self.token_version = (self.token_version or 0) + 1
        self.save(update_fields=["token_version"])
