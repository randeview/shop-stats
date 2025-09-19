# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.common.validators import phone_number_validator


class User(AbstractUser):
    class PaymentStatus(models.TextChoices):
        NOT_PAID = "NOT_PAID", _("Not paid")
        PAID = "PAID", _("Paid")

    phone_number = models.CharField(
        _("phone number"),
        max_length=20,
        validators=[phone_number_validator],
        blank=True,
    )
    device_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    payment_status = models.CharField(
        _("payment status"),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.NOT_PAID,
    )
    token_version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def bump_token_version(self):
        self.token_version = (self.token_version or 0) + 1
        self.save(update_fields=["token_version"])

    @property
    def is_paid(self) -> bool:
        return self.payment_status == self.PaymentStatus.PAID
