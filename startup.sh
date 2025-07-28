#!/bin/bash

uv run manage.py collectstatic --noinput
uv run manage.py migrate
uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --keyfile cert.key --certfile cert.crt