from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

ENVIRONMENT = env.str("DJANGO_ENVIRONMENT", default="development")

if ENVIRONMENT == "production":
    from config.settings.production import *
elif ENVIRONMENT == "test":
    from config.settings.test import *
else:
    from config.settings.development import *
