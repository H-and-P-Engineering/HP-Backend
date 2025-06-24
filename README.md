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
🏠 housing_properties/
├── 📱 apps/                     # Domain-specific applications
│   └── 🔐 authentication/       # Authentication & user management
│       ├── 🌐 application/       # Application-specific business rules (use cases)
│       ├── 🗄️ domain/           # Core domain models and interfaces (ports)
│       ├── 🛠️ infrastructure/    # Concrete implementations of domain ports (adapters), ORM models, services
│       ├── 📋 presentation/      # API views and serializers
│       └── ⚡ apps.py            # Authentication AppConfig
├── 🌐 api/                      # API versioning and routing
│   └── 📋 v1/                  # Version 1 API
│       └── authentication.py  # Authentication API endpoints
├── ⚙️ config/                   # Django settings and configuration
│   ├── 🔧 settings/             # Environment-specific settings
│   │   ├── 📋 base.py           # Common settings
│   │   ├── 🔨 development.py    # Development configuration
│   │   ├── 🚀 production.py     # Production configuration
│   │   └── 🧪 test.py           # Testing configuration
│   ├── 🔗 urls.py               # Root URL configuration
│   └── 🌐 wsgi.py               # WSGI configuration
├── 🛠️ core/                     # Shared utilities and base classes
│   ├── 🌐 application/          # Shared application-level components (e.g., base exceptions)
│   ├── 🗄️ domain/               # Shared domain components (currently empty but ready for expansion)
│   ├── 🛠️ infrastructure/        # Shared infrastructure components (e.g., exceptions, logging, templates)
│   ├── 📋 presentation/          # Shared presentation components (e.g., responses, serializers)
├── 📝 logs/                     # Application logs
├── 📄 .env.template             # Environment variables template
├── 🔧 Makefile                  # Common development commands
├── ⚙️ manage.py                 # Django management script
├── 🔍 pre-commit-config.yaml    # Pre-commit configuration
└── 📦 pyproject.toml            # Project dependencies & tools config
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

#### 🗄️ **Base Models**
- 📋 **Abstract base model** (if applicable - currently not explicitly in core, but assumed for common fields if `BaseModel` exists and is used) with common fields like timestamps.
- ⏰ **Automatic timestamps** (`created_at`, `updated_at`).
- 🆔 **UUID7 integration** for public, time-ordered, and globally unique identifiers (seen in `authentication.User`).

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

#### 🔧 **Custom Managers and QuerySets**
- 🧠 **Business logic encapsulation** in `UserManager` methods (e.g., `create_user`, `create_superuser`).
- 🔗 **Chainable QuerySet methods** for database interactions via repositories (e.g., `DjangoUserRepository`).

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