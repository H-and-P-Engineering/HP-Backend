# Housing & Properties Backend Documentation

## Overview

This is the backend API for the Housing & Properties marketplace platform. Built with Django 5 and Django REST Framework, it provides a robust, scalable API for managing property listings, transactions, messaging, and more.

## Architecture

The project follows a modular monolith architecture with clear domain boundaries, designed to evolve into microservices as needed.

### Key Technologies

- **Framework**: Django 5.0
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: JWT
- **Documentation**: drf-spectacular (Swagger/ReDoc)
- **Logging**: Loguru
- **Testing**: Pytest

## Project Structure

```ini
housing_properties/
├── apps/                # Domain-specific applications
├── api/                 # API versioning and routing
├── config/              # Django settings and configuration
├── core/                # Shared utilities and base classes
├── docs/                # Documentation
├── tests/               # Test suite
└── manage.py
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- uv (for package management)

### Installation

1. Clone the repository
2. Create a virtual environment:
   `uv venv --python 3.12`
3. Install dependencies:
   `make install`
4. Copy `.env.template` to `.env` and configure
5. Run migrations:
   `make migrate`
6. Create superuser:
   `make superuser`
7. Run server:
   `make run`

### API Documentation

Once the server is running, you can access:
- Swagger UI: http://localhost:8000/api/docs/swagger/
- ReDoc: http://localhost:8000/api/docs/redoc/

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Write comprehensive docstrings
- Keep functions focused and clear

### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Use factories for test data
- Run tests with:
  `make test`
- Run tests with coverage:
  `make test-coverage`

### Linting & Formatting

- Lint code:
  `make lint`
- Format code:
  `make format`

### Cleaning

- Remove Python cache and test artifacts:
  `make clean`

## Deployment

[To be documented]
