from django.contrib.auth.hashers import check_password, make_password


def hash_password(password: str) -> str:
    return make_password(password)


def password_check(raw_password: str, hashed_password: str) -> bool:
    return check_password(raw_password, hashed_password)
