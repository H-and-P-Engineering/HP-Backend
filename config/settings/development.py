from config.settings.base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

INSTALLED_APPS.extend(["debug_toolbar", "django_extensions"])

MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
