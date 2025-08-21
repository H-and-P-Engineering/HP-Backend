#!/bin/bash

if [ "$DJANGO_ENVIRONMENT" = "development" ]; then
    echo "Development environment detected, installing dev dependencies..."
    uv sync --extra dev
else
    echo "Production environment, using base dependencies only"
    uv sync
fi

uv run manage.py collectstatic --noinput
uv run manage.py migrate
uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --keyfile cert.key --certfile cert.crt --timeout 60 --workers 3