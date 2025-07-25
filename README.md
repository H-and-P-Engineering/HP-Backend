# 🏠 Housing & Properties Backend API

## 🎯 Overview

**Housing & Properties** is a comprehensive marketplace platform backend built with **Django 5** and **Django REST Framework**. The system implements **Clean Architecture** principles with a modular monolith design that's ready to evolve into microservices as needed.

### ⚡ **Core Features**
- 🔐 **Advanced Authentication System** - JWT-based with social auth, email verification, and token blacklisting
- 👤 **Multi-Type User Management** - CLIENT, AGENT, VENDOR, SERVICE_PROVIDER, ADMIN roles
- 🌐 **RESTful API Design** - Consistent, scalable API endpoints with comprehensive documentation
- 🛡️ **Security-First Approach** - Rate limiting, password validation, CSRF protection
- 📧 **Email Verification System** - Secure token-based email verification with templates
- 🔗 **Social Authentication** - Google OAuth2 integration with extensible architecture

---

## 🏗️ Architecture

The project follows **Clean Architecture** principles with clear separation of concerns:

```
🏠 Domain Layer (Business Entities)
    ↑
🌐 Application Layer (Use Cases/Business Rules)
    ↑
🛠️ Infrastructure Layer (Data Access, External Services)
    ↑
📋 Presentation Layer (API Views, Serializers)
```

### 🎯 **Architectural Principles**
- **Domain-Driven Design** with pure business entities
- **Repository Pattern** for data access abstraction
- **Event-Driven Architecture** for loose coupling
- **Interface Segregation** for testability
- **Dependency Inversion** through ports and adapters

---

## 🛠️ Technology Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| 🔧 **Framework** | Django | >=5.2.3 | Core web framework |
| 🌐 **API** | Django REST Framework | >=3.16.0 | RESTful API development |
| 🗄️ **Database** | PostgreSQL/SQLite | Latest | Primary data store |
| 🔐 **Authentication** | JWT (SimpleJWT) | >=5.5.0 | Stateless authentication |
| 📚 **Documentation** | drf-spectacular | >=0.28.0 | OpenAPI/Swagger docs |
| 📚 **Documentation UI** | drf-spectacular-sidecar | >=2025.6.1 | Swagger/ReDoc UI assets |
| 📊 **Logging** | Loguru | >=0.7.3 | Structured logging |
| 🧪 **Testing** | Pytest | >=8.4.0 | Test framework |
| 📦 **Package Manager** | uv | Latest | Ultra-fast dependency management |
| ✨ **Code Quality** | Ruff + pre-commit | Latest | Linting & formatting |
| 🔗 **Social Auth** | drf-social-oauth2 | >=3.1.0 | OAuth2 integration |
| ⚡ **Task Queue** | Celery | >=5.3.1 | Async task processing |
| 💾 **Caching** | Redis | >=6.2.0 | Cache and session storage |
| 🆔 **UUID Generation** | uuid6 | >=2025.0.0 | UUID7 support |
| 🌐 **Environment** | django-environ | >=0.12.0 | Environment variable management |
| 🔧 **Database URL** | dj-database-url | >=3.0.0 | Database configuration |
| 🌐 **CORS** | django-cors-headers | >=4.7.0 | Cross-origin resource sharing |
| 💾 **Redis Integration** | django-redis | >=6.0.0 | Django Redis cache backend |
| 🗄️ **Database** | psycopg2-binary | >=2.9.10 | PostgreSQL adapter |
| 🌐 **Static Files** | whitenoise | >=6.9.0 | Static file serving |
| 🚀 **WSGI Server** | gunicorn | >=23.0.0 | Production server |

### 🧪 **Development Dependencies**
- **django-debug-toolbar** (>=5.2.0) - Debug toolbar for development
- **django-extensions** (>=4.1) - Useful Django extensions
- **faker** (>=37.3.0) - Test data generation
- **pre-commit** (>=4.2.0) - Pre-commit hooks
- **pyopenssl** (>=25.1.0) - SSL support for development
- **pytest** (>=8.4.0) - Testing framework
- **pytest-cov** (>=6.1.1) - Test coverage reporting
- **werkzeug** (>=3.1.3) - WSGI utilities for development

---

## 📁 Project Structure

```ini
🏠 housing_properties/
├── 📱 apps/                        # Domain-specific applications
│   ├── 🔐 authentication/          # Authentication & authorization
│   │   ├── 🌐 application/         # Business rules (use cases)
│   │   │   ├── ports.py            # Interfaces for external dependencies
│   │   │   └── rules.py            # Business logic orchestration
│   │   ├── 🗄️ domain/              # Core business entities & events
│   │   │   ├── models.py           # Domain models (dataclasses)
│   │   │   └── events.py           # Domain events
│   │   ├── 🛠️ infrastructure/      # External concerns implementation
│   │   │   ├── factory.py          # Dependency factory (to be replaced with DI)
│   │   │   ├── middleware.py       # Token blacklisting middleware
│   │   │   ├── models.py           # Django ORM models
│   │   │   ├── pipelines.py        # Social authentication pipeline
│   │   │   ├── repositories.py     # Data access implementations
│   │   │   ├── services.py         # External service adapters
│   │   │   └── event_handlers.py   # Domain event handlers
│   │   ├── 📋 presentation/        # API layer
│   │   │   ├── serializers.py      # Request/response serializers
│   │   │   └── views.py            # API endpoints
│   │   ├── 🏭 models/              # Model exports
│   │   │   └── __init__.py         # BlackListedToken export
│   │   └── ⚡ apps.py               # App configuration
│   └── 👤 users/                   # User domain
│       ├── 🌐 application/         # User application services
│       │   └── ports.py            # User repository interfaces
│       ├── 🗄️ domain/              # User domain models & enums
│       │   ├── enums.py            # UserType enum
│       │   ├── events.py           # User domain events
│       │   └── models.py           # User domain model
│       ├── 🛠️ infrastructure/      # User data access & Django models
│       │   ├── managers.py         # Custom user manager
│       │   ├── models.py           # Django User model
│       │   └── repositories.py    # User repository implementation
│       ├── 🏭 models/              # Model exports
│       │   └── __init__.py         # User model export
│       └── ⚡ apps.py               # App configuration
├── 🌐 api/                         # API versioning and routing
│   ├── __init__.py                 # API package init
│   └── 📋 v1/                      # Version 1 API endpoints
│       ├── __init__.py             # V1 URL configuration
│       └── authentication.py      # Authentication endpoints
├── ⚙️ config/                      # Django configuration
│   ├── 🔧 settings/                # Environment-specific settings
│   │   ├── __init__.py             # Environment detection
│   │   ├── base.py                 # Common settings
│   │   ├── development.py          # Development configuration
│   │   ├── production.py           # Production configuration
│   │   └── test.py                 # Testing configuration
│   ├── urls.py                     # Root URL configuration
│   ├── wsgi.py                     # WSGI configuration
│   ├── asgi.py                     # ASGI configuration
│   └── __init__.py                 # Celery app configuration
├── 🛠️ core/                        # Shared utilities and base classes
│   ├── 🌐 application/             # Shared application components
│   │   ├── event_bus.py            # Event handling system
│   │   └── exceptions.py           # Business rule exceptions
│   ├── 🗄️ domain/                  # Shared domain components
│   │   └── events.py               # Base domain event
│   ├── 🛠️ infrastructure/          # Shared infrastructure
│   │   ├── exceptions/             # Exception handling framework
│   │   │   ├── __init__.py         # Exception exports
│   │   │   ├── base.py             # Base exception classes
│   │   │   └── handler.py          # Global exception handler
│   │   ├── logging/                # Logging configuration
│   │   │   └── base.py             # Loguru setup
│   │   ├── templates/              # Email templates
│   │   │   └── verify_email.html   # Email verification template
│   │   └── celery.py               # Celery configuration
│   └── 📋 presentation/            # Shared presentation components
│       ├── responses.py            # Standard API responses
│       └── serializers.py          # Common serializers
├── 📝 docs/                        # Documentation
│   └── authentication.md          # Authentication system docs
├── 📝 logs/                        # Application logs (created at runtime)
├── ⚙️ docker-compose.yml           # Docker Compose configuration
├── ⚙️ Dockerfile                   # Docker container configuration
├── ⚙️ startup.sh                   # Container startup script
├── ⚙️ nginx.conf.example           # Nginx configuration example
├── 📦 pyproject.toml               # Project dependencies & configuration
├── 📦 uv.lock                      # Dependency lock file
├── 📦 requirements.txt             # Generated requirements file
├── 📄 .env.template                # Environment variables template
├── 🔧 Makefile                     # Development commands
├── 🐍 .python-version              # Python version specification
├── 🔧 manage.py                    # Django management script
├── 🚫 .dockerignore                # Docker ignore file
└── 🚫 .gitignore                   # Git ignore file
```

---

## ✅ Implemented Features

### 🔐 **Authentication System**

#### **🎫 JWT Token Management**
- **Access Tokens**: Short-lived (30 minutes) for API authentication
- **Refresh Tokens**: Long-lived (24 hours) for token renewal
- **Token Blacklisting**: Secure logout with token invalidation
- **Custom Claims**: User type and email for frontend authorization

#### **👤 Multi-User Type System**
- **CLIENT** - Property seekers and buyers
- **AGENT** - Licensed real estate professionals  
- **VENDOR** - Service providers and contractors
- **SERVICE_PROVIDER** - Additional service providers
- **ADMIN** - Platform administrators

#### **📧 Email Verification**
- **Secure token generation** using `secrets.token_urlsafe(32)`
- **Cache-based storage** with automatic expiration (15 minutes)
- **Template-based emails** with customizable verification links
- **Protection against** brute-force and replay attacks

#### **🔗 Social Authentication**
- **Google OAuth2** integration with extensible architecture
- **Automatic user creation** or account linking
- **Custom pipeline** for handling user type selection
- **Seamless JWT integration** for unified authentication

### 🌐 **API Endpoints**

#### **Authentication Endpoints**
```http
POST   /api/v1/authentication/register/                     # User registration
POST   /api/v1/authentication/login/                        # User login  
POST   /api/v1/authentication/logout/                       # User logout
PUT    /api/v1/authentication/update-user-type/             # Update user type
POST   /api/v1/authentication/verify-email/request/         # Request verification
POST   /api/v1/authentication/verify-email/{uuid}/{token}/  # Verify email
GET    /api/v1/authentication/social/begin/{backend}/       # Start social auth
GET    /api/v1/authentication/social/complete/{backend}/    # Complete social auth
```

#### **API Documentation**
- **Swagger UI**: `/api/docs/swagger/`
- **ReDoc**: `/api/docs/redoc/`
- **OpenAPI Schema**: `/api/schema/`

### 🛡️ **Security Features**

#### **Password Security**
- **Complex validation**: Uppercase, lowercase, digit, special character
- **Minimum length**: 8 characters
- **No spaces allowed**: Prevents copy-paste errors
- **Secure hashing**: Django's Argon2 password hasher

#### **Rate Limiting**
- **Anonymous users**: 5 requests/minute
- **Authenticated users**: 10 requests/minute
- **Per-endpoint control**: Configurable throttling
- **IP-based protection**: Additional security layer

#### **Security Headers**
- **CSRF Protection**: Built-in Django CSRF middleware
- **CORS Configuration**: Configurable allowed origins
- **Security Middleware**: XSS, clickjacking protection
- **HTTPS Enforcement**: Production security settings

### 🏗️ **Infrastructure Features**

#### **Exception Handling**
- **Centralized error handling** with consistent API responses
- **Security-aware messages** to prevent information leakage
- **Detailed logging** for debugging while hiding internals
- **Custom business exceptions** for domain-specific errors

#### **Logging System**
- **Structured logging** with Loguru integration
- **Automatic log rotation** (10MB files, 10-day retention)
- **Environment-specific levels** via `DJANGO_LOGGING_LEVEL`
- **Performance monitoring** and audit trails

#### **Event System**
- **Domain events** for loose coupling between components
- **Async processing** with Celery for email sending
- **Event handlers** for cross-cutting concerns
- **Extensible architecture** for future business events

---

## 🚀 Getting Started

### 📋 **Prerequisites**

- 🐍 **Python 3.12+** (specified in `.python-version`)
- 🗄️ **PostgreSQL 14+** (recommended for production)
- ⚡ **Redis 6+** (for caching and Celery)
- 📦 **uv** (ultra-fast package manager)

### 🔧 **Quick Setup**

#### 1. **Repository Setup**
```bash
git clone <repository-url>
cd housing_properties
```

#### 2. **Environment Setup**
```bash
# Create virtual environment with Python 3.12
uv venv --python 3.12

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

#### 3. **Dependencies Installation**
```bash
# Install all project dependencies
make install
# or manually:
uv sync
```

#### 4. **Environment Configuration**
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your settings
nano .env  # or your preferred editor
```

**Critical Environment Variables:**
```env
# Django Core
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ENVIRONMENT=development
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Database
DJANGO_DATABASE_URL=postgresql://user:password@localhost:5432/housing_properties
DATABASE_CONN_MAX_AGE=600

# Redis/Cache
DJANGO_CACHE_TIMEOUT=600
DJANGO_CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache

# Email Configuration
DEFAULT_FROM_EMAIL=noreply@housingandproperties.com
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Authentication & Verification
DJANGO_VERIFICATION_TOKEN_EXPIRY=15
FROM_DOMAIN=http://127.0.0.1:8000

# Social Authentication
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_client_secret

# Security & CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Logging
DJANGO_LOGGING_LEVEL=INFO

# Celery (for async tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### 5. **Database Setup**
```bash
# Create and run migrations
make migrate
# or manually:
uv run manage.py migrate
```

#### 6. **Create Superuser**
```bash
make superuser
# or manually:
uv run manage.py createsuperuser
```

#### 7. **Start Development Server**
```bash
make run
# or manually:
uv run manage.py runserver

# Server available at: http://localhost:8000
```

### 🔧 **Development Commands**

```bash
# Install dependencies
make install

# Run development server
make run

# Run with SSL certificate (for HTTPS testing)
make run-cert

# Run migrations
make migrate

# Create new migrations
make migrations

# Create superuser
make superuser

# Clean cache and temporary files
make clean
```

---

## 🐳 Docker Deployment

### **Development with Docker**
```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f web

# Execute commands in container
docker-compose exec web uv run manage.py shell
docker-compose exec web uv run manage.py createsuperuser

# Stop services
docker-compose down
```

### **Docker Services**
The `docker-compose.yml` includes:
- **web**: Django application server
- **celery**: Background task worker
- **Shared volumes**: Static files, media files, application code

### **Production Deployment**
```bash
# Set production environment
echo "DJANGO_ENVIRONMENT=production" >> .env

# Update settings for production
# Configure PostgreSQL, Redis, and SMTP settings

# Build and deploy
docker-compose up -d

# Collect static files
docker-compose exec web uv run manage.py collectstatic --noinput

# Run migrations
docker-compose exec web uv run manage.py migrate
```

---

## 📊 API Documentation

### **Interactive Documentation**
- **Swagger UI**: http://localhost:8000/api/docs/swagger/
- **ReDoc**: http://localhost:8000/api/docs/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### **Authentication Examples**

#### **User Registration**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "user_type": "CLIENT"
  }'
```

#### **User Login**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### **Email Verification Request**
```bash
curl -X POST http://localhost:8000/api/v1/authentication/verify-email/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

#### **Social Authentication**
```bash
# Start Google OAuth flow
curl -X GET "http://localhost:8000/api/v1/authentication/social/begin/google-oauth2/?user_type=CLIENT"
```

#### **Authenticated Request**
```bash
curl -X PUT http://localhost:8000/api/v1/authentication/update-user-type/ \
  -H "Authorization: Bearer your_access_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "user_type": "AGENT"
  }'
```

---

## 🔒 Security

### **Production Security Checklist**
- ✅ **HTTPS**: Force SSL in production (`SECURE_SSL_REDIRECT = True`)
- ✅ **Secret Key**: Use strong, random secret key
- ✅ **Debug Mode**: Disabled in production (`DJANGO_DEBUG = False`)
- ✅ **Database**: Secure database credentials
- ✅ **CORS**: Configure allowed origins
- ✅ **Rate Limiting**: Enable throttling (5/min anon, 10/min auth)
- ✅ **Security Headers**: XSS, CSRF, clickjacking protection
- ✅ **Email**: Use secure email backend (not console)
- ✅ **Social Auth**: Secure OAuth2 credentials
- ✅ **Logging**: Appropriate log levels (`DJANGO_LOGGING_LEVEL`)

### **Security Headers Applied**
```python
# Automatically applied in production
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## 🧪 Testing

### **Running Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest tests/test_authentication/

# Run with verbose output
pytest -v
```

### **Test Structure**
```
tests/
├── conftest.py                 # Test configuration
├── test_authentication/        # Authentication tests
│   ├── test_rules.py           # Business logic tests
│   ├── test_api.py             # API endpoint tests
│   └── test_services.py        # Service tests
└── test_users/                 # User tests
    ├── test_models.py          # Model tests
    └── test_repositories.py    # Repository tests
```

---

## 📈 Performance & Monitoring

### **Database Optimization**
- **Connection pooling** with configurable `DATABASE_CONN_MAX_AGE`
- **Query optimization** with select_related/prefetch_related
- **Database indexing** on frequently queried fields
- **UUID7 usage** for better database performance (time-ordered)

### **Caching Strategy**
- **Redis caching** for session data and temporary tokens
- **Template caching** for static content
- **Configurable timeout** via `DJANGO_CACHE_TIMEOUT`
- **Different backends** for dev (LocMem) vs prod (Redis)

### **Monitoring**
- **Structured logging** with Loguru and request tracing
- **Log rotation** (10MB files, 10-day retention)
- **Performance metrics** via Django admin
- **Error tracking** with detailed stack traces
- **Health check endpoints** for system monitoring

---

## 🔄 Development Workflow

### **Code Quality**
```bash
# Format code with ruff (via pre-commit)
make clean  # Includes code formatting

# Install pre-commit hooks
make install  # Includes pre-commit installation

# Run pre-commit hooks manually
pre-commit run --all-files
```

### **Git Workflow**
```bash
# Feature development
git checkout -b feature/new-feature
git commit -m "feat: add new feature"
git push origin feature/new-feature

# Pre-commit hooks will run automatically
```

### **Environment Management**
- **Development**: Local SQLite, console email backend, LocMem cache
- **Production**: PostgreSQL, SMTP email, Redis cache, security headers
- **Testing**: In-memory database, test-specific settings

---

## 🤝 Contributing

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Submit a pull request

### **Code Standards**
- Follow PEP 8 style guidelines (enforced by pre-commit)
- Write comprehensive tests
- Document new features
- Use conventional commit messages
- Maintain backward compatibility
- Follow Clean Architecture principles

---

## 📚 Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **DRF Documentation**: https://www.django-rest-framework.org/
- **Clean Architecture**: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- **API Design Best Practices**: https://restfulapi.net/
- **Python Type Hints**: https://docs.python.org/3/library/typing.html
- **Loguru Documentation**: https://loguru.readthedocs.io/
- **Celery Documentation**: https://docs.celeryproject.org/
- **UV Package Manager**: https://github.com/astral-sh/uv

---