FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . .

RUN if [ "$DJANGO_ENVIRONMENT" = "development" ]; then \
        uv sync --extra dev; \
    else \
        uv sync; \
    fi

RUN mkdir -p /app/logs && chmod 777 /app/logs