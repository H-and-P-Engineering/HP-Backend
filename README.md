# 🏠 Housing & Properties Backend Documentation

## 🎯 Overview

This is the **backend API** for the **Housing & Properties marketplace platform**. Built with **Django 5** and **Django REST Framework**, it provides a **robust, scalable API** for managing various functionalities, starting with comprehensive user authentication.

### ⚡ **Core Philosophy**
- 🏗️ **Modular monolith** architecture with clear domain boundaries
- 🔄 **Evolution-ready** design for future microservices transition
- 🛡️ **Security-first** approach with enterprise-grade authentication
- 📈 **Performance-optimized** for high-scale operations

---

## 🏗️ Architecture

The project follows a **modular monolith architecture** with clear domain boundaries, designed to evolve into **microservices** as needed. It strictly adheres to **Clean Architecture** principles.

### 🛠️ **Key Technologies**

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| 🔧 **Framework** | Django | Latest | Core web framework |
| 🌐 **API** | Django REST Framework | Latest | RESTful API development |
| 🗄️ **Database** | PostgreSQL | Latest | Primary data store |
| 🔐 **Authentication** | JWT (simplejwt) | Latest | Stateless authentication |
| 📚 **Documentation** | drf-spectacular | Latest | Swagger/ReDoc integration |
| 📊 **Logging** | Loguru | Latest | Structured logging |
| 🧪 **Testing** | Pytest | Latest | Test framework |
| 📦 **Package Management** | uv | Latest | Fast dependency management |
| ✨ **Code Quality** | Ruff + pre-commit | Latest | Linting & formatting |

---

## 📁 Project Structure

```ini
🏠 housing_&_properties/
├── 📱 apps/                      # Domain-specific applications
│   └── 🔐 authentication/        # Authentication & user management
│       ├── 🌐 application/       # Application-specific business rules (use cases)
│       ├── 🗄️ domain/            # Core domain models and interfaces (ports)
│       ├── 🛠️ infrastructure/    # Concrete implementations of domain ports (adapters), ORM models, services
│       ├── 📋 presentation/      # API views and serializers
│       └── ⚡ apps.py             # Authentication AppConfig
├── 🌐 api/                       # API versioning and routing
│   └── 📋 v1/                    # Version 1 API
│       └── authentication.py     # Authentication API endpoints
├── ⚙️ config/                    # Django settings and configuration
│   ├── 🔧 settings/              # Environment-specific settings
│   │   ├── 📋 base.py            # Common settings
│   │   ├── 🔨 development.py     # Development configuration
│   │   ├── 🚀 production.py      # Production configuration
│   │   └── 🧪 test.py            # Testing configuration
│   ├── 🔗 urls.py                # Root URL configuration
│   └── 🌐 wsgi.py                # WSGI configuration
├── 🛠️ core/                      # Shared utilities and base classes
│   ├── 🌐 application/           # Shared application-level components (e.g., base exceptions)
│   ├── 🗄️ domain/                # Shared domain components (currently empty but ready for expansion)
│   ├── 🛠️ infrastructure/        # Shared infrastructure components (e.g., exceptions, logging, templates)
│   ├── 📋 presentation/          # Shared presentation components (e.g., responses, serializers)
├── 📝 logs/                      # Application logs
├── 📄 .env.template              # Environment variables template
├── 🔧 Makefile                   # Common development commands
├── ⚙️ manage.py                  # Django management script
└── 📦 pyproject.toml             # Project dependencies & tools config
├── ⚙️ startup.sh                 # startup script for dockerised service
├── ⚙️ nginx.conf.example         # Sample nginx configuration
├── ⚙️ Dockerfile                
├── ⚙️ docker-compose.yml              
```

---

## ✅ Implemented Features

### 🏗️ **Core Infrastructure**

#### ⚙️ **Settings Management**
- 🔧 **Modular configuration** for different environments (development, production, test).
- 🌍 **Environment-specific settings** loaded via `django-environ`.
- 🔒 **Secure configuration** by loading sensitive data from environment variables.

#### ❌ **Exception Handling**
- 🎯 **Custom exception handler** (`core.infrastructure.exceptions.handler.hp_exception_handler`) ensuring consistent API error responses.
- 📋 **Standardized error format** across all endpoints (`success: false`, `message`, `error: {detail}`, `status_code`).
- 🔍 **Detailed error tracking and logging** for unexpected server errors (e.g., `TypeError`, `AttributeError`) with full tracebacks for developers.
- 🛡️ **Security-aware error messages**, avoiding exposure of sensitive internal system details to users.

#### 📊 **Logging System**
- ⚡ **Integrated Loguru** for structured, human-readable, and machine-parsable logs.
- 🔄 **Automatic file rotation** (e.g., 10MB per file, 10 days retention) to manage log file sizes.
- 📈 **Performance monitoring** and audit trails enabled through configurable logging levels.
- 🎯 **Environment-specific logging levels** controlled by `DJANGO_LOGGING_LEVEL` environment variable.

#### 📚 **API Documentation**
- 📖 **Swagger UI** for interactive API exploration via `drf-spectacular`.
- 📋 **ReDoc** for comprehensive API documentation via `drf-spectacular`.
- 🔄 **Auto-generated** from code annotations (`@extend_schema`) for up-to-date documentation.
- 🎯 **Version-aware documentation** for API `/api/v1/`.

---

### 👤 **Authentication Domain**

#### 🔐 **Custom User Model**
**Advanced Features:**
- 📧 **Email-based authentication** (`USERNAME_FIELD = "email"`, no username required).
- 🆔 **UUID7 for public identifiers** (time-ordered, globally unique, `uuid` field).
- 👥 **Multiple user types** support (`UserType` enum and `user_type` field):
  - 👤 **CLIENT** - property seekers and buyers
  - 🏢 **AGENT** - licensed real estate professionals
  - 🛠️ **VENDOR** - service providers and contractors
  - 👑 **ADMIN** - platform administrators
- ✅ **Email verification** tracking (`is_email_verified` field).
- 🔒 **Security-first design** with comprehensive password validation.

*Note: User profiles (AgentProfile, VendorProfile, ClientProfile) are conceptually described in the documentation but are not currently implemented as separate Django models or domain models in the provided codebase. This is a future enhancement.*

#### 🔧 **Custom Managers**
- 🧠 **Business logic encapsulation** in `UserManager` methods (e.g., `create_user`, `create_superuser`).

#### 🔗 **Social Authentication**
- 🔵 **Google OAuth2** integration using `drf-social-oauth2` and `python-social-auth`.
- 🏗️ **Extensible architecture** designed for adding additional social providers.
- 🔄 **Seamless user creation** and profile setup for new social users via `get_or_create_social`.
- 🛡️ **Security-compliant implementation** for OAuth2 flows.

#### 🎫 **Token Management System**
- Uses `djangorestframework-simplejwt` for **JSON Web Tokens (JWT)** for stateless authentication.
- **Access Tokens**: Short-lived, for API requests.
- **Refresh Tokens**: Long-lived, for obtaining new access tokens.
- **Token Blacklisting**: Implemented via `BlacklistedToken` model and `TokenBlacklistMiddleware` to invalidate tokens on logout.
- **Configurable Lifetimes**: Token validity periods are configurable in `settings.py`.

---

## 🚀 Getting Started

### 📋 **Prerequisites**

- 🐍 **Python 3.12+** (latest stable version)
- 🗄️ **PostgreSQL** (primary database, recommended for production)
- ⚡ **uv** (ultra-fast package management)

### 🔧 **Installation Process**

#### 1. 📥 **Repository Setup**
```bash
# Clone the repository
git clone <repository-url>
cd housing_properties
```

#### 2. 🐍 **Environment Setup**
```bash
# Create virtual environment with Python 3.12
uv venv --python 3.12

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

#### 3. 📦 **Dependencies Installation**
```bash
# Install all project dependencies
make install
```

#### 4. 🗄️ **Database Configuration**
```bash
# Create PostgreSQL database
createdb housing_properties

# Configure database connection in .env
# Example for PostgreSQL: DATABASE_URL=postgres://user:password@localhost:5432/housing_properties
```

#### 5. ⚙️ **Environment Configuration**
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your specific settings
# Ensure the following critical variables are set for production:
# - DJANGO_SECRET_KEY: A long, random string.
# - DJANGO_DATABASE_URL: Your production database connection string.
# - CORS_ALLOWED_ORIGINS: Comma-separated list of allowed origins (e.g., http://your-frontend.com).
# - EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD: For sending emails.
# - DEFAULT_FROM_EMAIL: The email address for outgoing emails.
# - FROM_DOMAIN: Your API's public domain (e.g., https://api.your-domain.com) for link generation.
# - SOCIAL_AUTH_GOOGLE_OAUTH2_KEY, SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET: Your Google OAuth credentials.
nano .env  # or your preferred editor
```

#### 6. 🔄 **Database Migration**
```bash
# Apply database migrations
make migrate
```

#### 7. 👑 **Admin User Creation**
```bash
# Create superuser for admin access
make superuser
```

#### 8. 🚀 **Development Server**
```bash
# Start development server
make run

# Server will be available at http://localhost:8000
```

--- 

## 🐳 Deployment and Running with Docker Compose

This section outlines how to containerize and run the Housing & Properties backend application using Docker and Docker Compose, leveraging external cloud services for the database and caching.

### Prerequisites

Before proceeding, ensure you have the following installed on your system:

*   **Docker**: Install Docker Engine for Linux ([Official instructions](https://docs.docker.com/engine/install/))
*   **Docker Compose**: On Linux, you may need to install Docker Compose separately. See [Install Docker Compose](https://docs.docker.com/compose/install/) for instructions.

### 1. Project Structure for Docker

Ensure your project root directory (HP-Backend/) contains the following files:

*   `Dockerfile`
*   `docker-compose.yml`
*   `startup.sh` (Startup script with conditional SSL support)
*   `.env` (This file should NOT be committed to version control)
*   `pyproject.toml` (uv package management)

### 2. Docker Configuration Files

#### `Dockerfile`
```dockerfile
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY . .
RUN chmod +x /app/startup.sh
RUN uv sync
```

#### `docker-compose.yml`
```yaml
services:
  web:
    build: .
    command: ./startup.sh
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env

volumes:
  static_volume:
  media_volume: 
```

#### `startup.sh`
```bash
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
```

### 3. Configure the `.env` File

The `.env` file holds critical environment variables for your application, including sensitive credentials for external services. Create a file named `.env` in the root of your `HP-Backend` directory with the following structure. **Remember to replace all placeholder values with your actual credentials and configurations.**

```dotenv
# Django Core Settings
DJANGO_SECRET_KEY=your_django_secret_key
DJANGO_DEBUG=False
DJANGO_ENVIRONMENT=production  # Set to 'development' for SSL/HTTPS in local development
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,<your_domain_if_any>

# External PostgreSQL Database (Azure PostgreSQL Example)
# Ensure your Django settings are configured to read this DATABASE_URL
DJANGO_DATABASE_URL=postgresql://your_database_user:your_database_password@your_azure_postgresql_host.postgres.database.azure.com:5432/your_database_name

DATABASE_CONN_MAX_AGE=600

# External Redis Cache (Upstash Redis Example)
# Ensure your Django settings are configured to read this REDIS_URL
REDIS_URL=rediss://default:your_upstash_redis_password@your_upstash_redis_host:6379

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,<your_frontend_url>

# Email Settings (Gmail SMTP Example)
DEFAULT_FROM_EMAIL=noreply@housingandproperties.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_gmail_username@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password # Use an App Password for security

# Authentication and Token Settings
DJANGO_VERIFICATION_TOKEN_EXPIRY=15 # minutes
FROM_DOMAIN=http://127.0.0.1:8000 # Your backend API URL (use https:// for production)

# Cache Settings
DJANGO_CACHE_TIMEOUT=15 # seconds (general cache timeout)
DJANGO_CACHE_BACKEND=django.core.cache.backends.redis.RedisCache

# Logging Level
DJANGO_LOGGING_LEVEL=INFO

# Google OAuth2 Credentials (if used)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_oauth2_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_oauth2_client_secret
```

### 4. SSL Certificate Setup (Development Only)

If you're running in development mode (`DJANGO_ENVIRONMENT=development`), you'll need SSL certificates for HTTPS:

```bash
# Generate self-signed certificates for local development
openssl req -x509 -newkey rsa:4096 -keyout cert.key -out cert.crt -days 365 -nodes
```

**Note:** For production deployments, use proper SSL certificates from a Certificate Authority or let your reverse proxy (nginx, CloudFlare, etc.) handle SSL termination.

### 5. Build and Run the Application

Navigate to your `HP-Backend` root directory in the terminal and execute the following command:

```bash
docker-compose up --build
```

**Explanation of the command:**

*   `docker-compose up`: Starts the services defined in your `docker-compose.yml` file.
*   `--build`: Ensures that the Docker image is rebuilt before starting the container.

This command will:

1.  **Build the Docker image** using the optimized Dockerfile with `uv` package manager
2.  **Start the container** and execute the startup script (`startup.sh`)
3.  **Inside the container**, the startup script will:
    *   Run `uv run manage.py collectstatic --noinput`: Gathers all static files
    *   Run `uv run manage.py migrate`: Applies any pending database migrations
    *   **Conditionally start Gunicorn**:
        - **Development**: `uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --certfile cert.crt --keyfile cert.key` (with SSL)
        - **Production**: `uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000` (without SSL)

### 6. Accessing the Application

Once Docker Compose has finished starting up, your Django application will be accessible at:

- **Development mode** (`DJANGO_ENVIRONMENT=development`): `https://localhost:8000` (SSL enabled)
- **Production mode**: `http://localhost:8000` (SSL handled by reverse proxy)

### 7. Development vs Production Modes

The application automatically adapts based on the `DJANGO_ENVIRONMENT` variable:

| Environment | SSL | URL | Use Case |
|-------------|-----|-----|----------|
| `development` | ✅ Built-in SSL | `https://localhost:8000` | Local development with HTTPS |
| `production` | ❌ External SSL | `http://localhost:8000` | Production with reverse proxy SSL |

### 8. Container Management

**Common Docker Compose commands:**

```bash
# Start in detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build

# Execute commands inside the running container
docker-compose exec web uv run manage.py shell
docker-compose exec web uv run manage.py createsuperuser
```