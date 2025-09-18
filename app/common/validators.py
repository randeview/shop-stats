from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

phone_number_validator = RegexValidator(
    regex=r"^\+[7]\d{10}$",
    message=_(
        "Wrong phone_number format, it should start with '+' sign and "
        "has 11 digits. Example: '+77777777777'"
    ),
)
