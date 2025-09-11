import re

from django.contrib.auth.hashers import check_password, make_password
from rest_framework.serializers import ValidationError


def hash_password(password: str) -> str:
    return make_password(password)


def password_check(raw_password: str, hashed_password: str) -> bool:
    return check_password(raw_password, hashed_password)


def validate_password_value(password: str) -> str:
    if " " in password:
        raise ValidationError("Password must not contain spaces.")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")

    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")

    if not re.search(r"[!@#$%^&*(),.?\"\'{}|<>]", password):
        raise ValidationError("Password must contain at least one special character.")

    return password
