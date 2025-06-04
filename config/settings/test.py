"""Test settings for Housing & Properties project."""

from .base import *  # noqa

# Test Database
DATABASES = {
    "default": dj_database_url.config(  # noqa
        default="sqlite:///test_db.sqlite3",
        conn_health_checks=True,
    )
}

# Disable migrations during tests
MIGRATION_MODULES = {
    app: None
    for app in INSTALLED_APPS  # noqa
    if app.startswith("apps.")
}
