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
| 🔧 **Framework** | Django | 5.2.3+ | Core web framework |
| 🌐 **API** | Django REST Framework | 3.16.0+ | RESTful API development |
| 🗄️ **Database** | PostgreSQL/SQLite | Latest | Primary data store |
| 🔐 **Authentication** | JWT (SimpleJWT) | 5.5.0+ | Stateless authentication |
| 📚 **Documentation** | drf-spectacular | 0.28.0+ | OpenAPI/Swagger docs |
| 📊 **Logging** | Loguru | 0.7.3+ | Structured logging |
| 🧪 **Testing** | Pytest | 8.4.0+ | Test framework |
| 📦 **Package Manager** | uv | Latest | Ultra-fast dependency management |
| ✨ **Code Quality** | Ruff + pre-commit | Latest | Linting & formatting |
| 🔗 **Social Auth** | drf-social-oauth2 | Latest | OAuth2 integration |
| ⚡ **Task Queue** | Celery | 5.4.0+ | Async task processing |
| 💾 **Caching** | Redis | Latest | Cache and session storage |

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
│   │   └── ⚡ apps.py               # App configuration
│   └── 👤 users/                   # User domain
│       ├── 🌐 application/         # User application services
│       ├── 🗄️ domain/              # User domain models & enums
│       ├── 🛠️ infrastructure/      # User data access & Django models
│       └── ⚡ apps.py               # App configuration
├── 🌐 api/                         # API versioning and routing
│   └── 📋 v1/                      # Version 1 API endpoints
├── ⚙️ config/                      # Django configuration
│   ├── 🔧 settings/                # Environment-specific settings
│   │   ├── base.py                 # Common settings
│   │   ├── development.py          # Development configuration
│   │   ├── production.py           # Production configuration
│   │   └── test.py                 # Testing configuration
│   ├── urls.py                     # Root URL configuration
│   ├── wsgi.py                     # WSGI configuration
│   └── asgi.py                     # ASGI configuration
├── 🛠️ core/                        # Shared utilities and base classes
│   ├── 🌐 application/             # Shared application components
│   │   ├── event_bus.py            # Event handling system
│   │   └── exceptions.py           # Business rule exceptions
│   ├── 🗄️ domain/                  # Shared domain components
│   │   └── events.py               # Base domain event
│   ├── 🛠️ infrastructure/          # Shared infrastructure
│   │   ├── exceptions/             # Exception handling framework
│   │   ├── logging/                # Logging configuration
│   │   ├── templates/              # Email templates
│   │   └── celery.py               # Celery configuration
│   └── 📋 presentation/            # Shared presentation components
│       ├── responses.py            # Standard API responses
│       └── serializers.py          # Common serializers
├── 📝 docs/                        # Documentation
├── 📝 logs/                        # Application logs
├── ⚙️ Dockerfile                   # Docker container configuration
├── ⚙️ docker-compose.yml           # Docker Compose setup
├── ⚙️ startup.sh                   # Container startup script
├── 📦 pyproject.toml               # Project dependencies & configuration
├── 📄 .env.template                # Environment variables template
├── 🔧 Makefile                     # Development commands
└── 📦 uv.lock                      # Dependency lock file
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
- **Swagger UI**: `/api/schema/swagger-ui/`
- **ReDoc**: `/api/schema/redoc/`
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

- 🐍 **Python 3.12+** (latest stable version)
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
DJANGO_SECRET_KEY=your_secret_key_here
DJANGO_DEBUG=False
DJANGO_ENVIRONMENT=development

# Database
DJANGO_DATABASE_URL=postgresql://user:password@localhost:5432/housing_properties

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (Example: Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Social Authentication
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_client_secret

# Security
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
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

# Run migrations
make migrate

# Create new migrations
make makemigrations

# Create superuser
make superuser

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Run all checks
make check

# Clean cache and temp files
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
```

### **Production Deployment**
```bash
# Set production environment
echo "DJANGO_ENVIRONMENT=production" >> .env

# Use production settings
docker-compose -f docker-compose.prod.yml up -d

# SSL certificates (if needed)
openssl req -x509 -newkey rsa:4096 -keyout cert.key -out cert.crt -days 365 -nodes
```

---

## 📊 API Documentation

### **Interactive Documentation**
- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
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
    "last_name": "Doe"
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

#### **Authenticated Request**
```bash
curl -X GET http://localhost:8000/api/v1/users/profile/ \
  -H "Authorization: Bearer your_access_token_here"
```

---

## 🔒 Security

### **Production Security Checklist**
- ✅ **HTTPS**: Force SSL in production
- ✅ **Secret Key**: Use strong, random secret key
- ✅ **Debug Mode**: Disabled in production
- ✅ **Database**: Secure database credentials
- ✅ **CORS**: Configure allowed origins
- ✅ **Rate Limiting**: Enable throttling
- ✅ **Security Headers**: XSS, CSRF, clickjacking protection
- ✅ **Email**: Use secure email backend (not console)
- ✅ **Social Auth**: Secure OAuth2 credentials
- ✅ **Logging**: Appropriate log levels

### **Security Headers Applied**
```python
# Automatically applied in production
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
```

---

## 🧪 Testing

### **Running Tests**
```bash
# Run all tests
make test
# or
uv run pytest

# Run with coverage
uv run pytest --cov=apps --cov-report=html

# Run specific test file
uv run pytest tests/test_authentication/

# Run with verbose output
uv run pytest -v
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
- **Connection pooling** with configurable `CONN_MAX_AGE`
- **Query optimization** with select_related/prefetch_related
- **Database indexing** on frequently queried fields
- **Migration strategies** for zero-downtime deployments

### **Caching Strategy**
- **Redis caching** for session data and temporary tokens
- **Template caching** for static content
- **API response caching** for expensive operations
- **Database query caching** for repeated queries

### **Monitoring**
- **Structured logging** with request tracing
- **Performance metrics** via Django admin
- **Error tracking** with detailed stack traces
- **Health check endpoints** for system monitoring

---

## 🔄 Development Workflow

### **Code Quality**
```bash
# Format code with ruff
make format

# Lint code
make lint

# Run pre-commit hooks
pre-commit run --all-files

# Type checking (if using mypy)
mypy apps/
```

### **Git Workflow**
```bash
# Feature development
git checkout -b feature/new-feature
git commit -m "feat: add new feature"
git push origin feature/new-feature

# Code review and merge to main
```

### **Environment Management**
- **Development**: Local SQLite, console email backend
- **Staging**: PostgreSQL, SMTP email, Redis cache
- **Production**: PostgreSQL, secure settings, monitoring

---


## 🤝 Contributing

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### **Code Standards**
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Document new features
- Use conventional commit messages
- Maintain backward compatibility

---

## 📚 Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **DRF Documentation**: https://www.django-rest-framework.org/
- **Clean Architecture**: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- **API Design Best Practices**: https://restfulapi.net/
- **Python Type Hints**: https://docs.python.org/3/library/typing.html

---