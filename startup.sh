#!/bin/bash

uv run manage.py collectstatic --noinput
uv run manage.py migrate

if [ "$DJANGO_ENVIRONMENT" = "development" ]; then
    echo "Starting Gunicorn with SSL for development..."
    uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --certfile cert.crt --keyfile cert.key
else
    echo "Starting Gunicorn without SSL..."
    uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000
fi