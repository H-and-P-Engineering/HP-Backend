# Housing & Properties Backend API - Developer Guide

A comprehensive Django-based marketplace platform implementing Clean Architecture principles for real estate and property management.

## 📋 Table of Contents

1. [🏗️ Architecture Overview](#️-architecture-overview)
2. [🚀 Quick Start](#-quick-start)
3. [🔐 Authentication API](#-authentication-api)
4. [👤 User Management API](#-user-management-api)
5. [🏢 Business Verification API](#-business-verification-api)
6. [⚙️ Configuration](#️-configuration)
8. [🚀 Deployment](#-deployment)
9. [🔧 Development Workflow](#-development-workflow)

---

## 🏗️ Architecture Overview

### 🎯 Core Principles

This project follows **Clean Architecture** with clear separation of concerns:

```
📁 Domain Layer (Business Entities)
    ↑
📁 Application Layer (Use Cases/Business Rules)
    ↑
📁 Infrastructure Layer (Data Access, External Services)
    ↑
📁 Presentation Layer (API Views, Serializers)
```

### 🏢 Project Structure

```
housing_properties/
├── 📁 api/                     # API routing & versioning
│   └── v1/                     # Version 1 endpoints
├── 📁 app/                     # Core application
│   ├── application/            # Business rules & use cases
│   ├── domain/                # Business entities & events
│   ├── infrastructure/        # External integrations
│   ├── presentation/          # API views & serializers
│   └── core/                  # Shared utilities
├── 📁 config/                 # Django configuration
│   └── settings/              # Environment settings
└── 📁 docs/                   # Documentation
```

### 🎨 Key Features

- **🔐 JWT Authentication** with social login support
- **✉️ Email Verification** system
- **🏢 Business Verification** with external provider integration
- **👥 Multi-type User Management** (CLIENT, AGENT, VENDOR, SERVICE_PROVIDER, ADMIN)
- **⚡ Event-driven Architecture** with Celery
- **📄 OpenAPI Documentation** with Swagger UI

### 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | Django | >=5.2.3 |
| **API** | Django REST Framework | >=3.16.0 |
| **Authentication** | JWT (SimpleJWT) | >=5.5.0 |
| **Database** | PostgreSQL/SQLite | Latest |
| **Task Queue** | Celery + Redis | >=5.3.1 |
| **Documentation** | drf-spectacular | >=0.28.0 |
| **Package Manager** | uv | Latest |

---

## 🚀 Quick Start

### 📋 Prerequisites

- Python 3.12+
- PostgreSQL 14+ (recommended for production)
- Redis 6+ (for caching and Celery)
- uv (package manager)

### 🔧 Installation

1. **Clone and setup environment**
```bash
git clone <repository-url>
cd housing_properties
uv venv --python 3.12
source .venv/bin/activate  # Linux/macOS
```

2. **Install dependencies**
```bash
make install
# or: uv sync
```

3. **Environment configuration**
```bash
cp .env.template .env
# Edit .env with your settings
```

4. **Database setup**
```bash
make migrate
make superuser
```

5. **Start development server**
```bash
make run
```

### 🐳 Docker Setup (Alternative)

```bash
docker-compose up --build
docker-compose exec web uv run manage.py createsuperuser
```

### 📚 API Documentation

- **Swagger UI**: https://localhost:8000/api/docs/swagger/
- **ReDoc**: https://localhost:8000/api/docs/redoc/
- **OpenAPI Schema**: https://localhost:8000/api/schema/

---

## 🔐 Authentication API

### 3.1. 📝 User Registration

- **🔗 Endpoint:** `/api/v1/authentication/register/`
- **📡 HTTP Method:** `POST`
- **📝 Description:** Register a new user with email verification
- **🔐 Authentication:** Not Required

**📤 Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "user_type": "BUYER"
}
```

**✅ Success Response (Status: 201 Created):**
```json
{
  "success": true,
  "message": "Registration successful. Check your email for a verification link.",
  "data": {
    "user": {
      "id": "uuid-here",
      "email": "user@example.com",
      "user_type": "BUYER",
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "+1234567890",
      "is_email_verified": false,
      "is_new": true
    }
  },
  "status_code": 201
}
```

### 3.2. 🔑 User Login

- **🔗 Endpoint:** `/api/v1/authentication/login/`
- **📡 HTTP Method:** `POST`
- **📝 Description:** Authenticate user and receive JWT tokens
- **🔐 Authentication:** Not Required

**📤 Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**✅ Success Response (Status: 200 OK):**
```json
{
  "success": true,
  "message": "Login successful. Welcome back!",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": "1",
      "email": "user@example.com",
      "user_type": "BUYER",
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "+1234567890",
      "is_email_verified": true,
      "is_new": false
    }
  },
  "status_code": 200
}
```

### 3.3. 🚪 User Logout

- **🔗 Endpoint:** `/api/v1/authentication/logout/`
- **📡 HTTP Method:** `POST`
- **📝 Description:** Logout user and blacklist access token
- **🔐 Authentication:** Required (Bearer Token)

**📤 Request Body:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**✅ Success Response (Status: 200 OK):**
```json
{
  "success": true,
  "message": "Logout successful.",
  "data": null,
  "status_code": 200
}
```

### 3.4. 📧 Request Email Verification

- **🔗 Endpoint:** `/api/v1/authentication/verify-email/request/`
- **📡 HTTP Method:** `POST`
- **📝 Description:** Request a new email verification link
- **🔐 Authentication:** Not Required

**📤 Request Body:**
```json
{
  "email": "user@example.com"
}
```

**✅ Success Response (Status: 200 OK):**
```json
{
  "success": true,
  "message": "A new verification link has been sent to your email.",
  "data": null,
  "status_code": 200
}
```

### 3.5. ✅ Verify Email

- **🔗 Endpoint:** `/api/v1/authentication/verify-email/{user_uuid}/{verification_token}/`
- **📡 HTTP Method:** `POST`
- **📝 Description:** Verify user email address
- **🔐 Authentication:** Not Required
- **🔗 URL Parameters:**
  - `user_uuid`: string (required) - User's UUID
  - `verification_token`: string (required) - Verification token from email

**📤 Request Body:** None

**✅ Success Response (Status: 200 OK):**
```json
{
  "success": true,
  "message": "Email verification successful. Welcome to Housing & Properties!",
  "data": {
    "user_type": "BUYER"
  },
  "status_code": 200
}
```

### 3.6. 🌐 Social Authentication (Google)

#### Start Social Authentication
- **🔗 Endpoint:** `/api/v1/authentication/social/begin/google-oauth2/`
- **📡 HTTP Method:** `GET`
- **📝 Description:** Initiate Google OAuth2 login
- **🔐 Authentication:** Not Required
- **🔗 Query Parameters:**
  - `user_type`: string (optional) - User type (BUYER, AGENT, VENDOR, SERVICE_PROVIDER)

#### Complete Social Authentication
- **🔗 Endpoint:** `/api/v1/authentication/social/complete/google-oauth2/`
- **📡 HTTP Method:** `GET`
- **📝 Description:** Complete Google OAuth2 login (callback)
- **🔐 Authentication:** Not Required

#### Get Social Auth Data
- **🔗 Endpoint:** `/api/v1/authentication/social/data/`
- **📡 HTTP Method:** `GET`
- **📝 Description:** Retrieve social authentication user data
- **🔐 Authentication:** Not Required

**✅ Success Response (Status: 200 OK):**
```json
{
  "success": true,
  "message": "Login successful. Welcome back!",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": "1",
      "email": "user@example.com",
      "user_type": "BUYER",
      "first_name": "John",
      "last_name": "Doe",
      "is_email_verified": true,
      "is_new": false
    }
  },
  "status_code": 200
}
```

---

## 👤 User Management API

### 4.1. 🔄 Update User Type

- **🔗 Endpoint:** `/api/v1/users/update-user-type/`
- **📡 HTTP Method:** `PUT`
- **📝 Description:** Update user type for authenticated user
- **🔐 Authentication:** Required (Bearer Token)

**📤 Request Body:**
```json
{
  "email": "user@example.com",
  "user_type": "LAND_AGENT"
}
```

**✅ Success Response (Status: 202 Accepted):**
```json
{
  "success": true,
  "message": "User Type update successful.",
  "data": null,
  "status_code": 202
}
```

---

## 🏢 Business Verification API

### 5.1. 🏗️ Create Business Profile

- **🔗 Endpoint:** `/api/v1/business-verification/create-profile/`
- **📡 HTTP Method:** `POST`
- **📝 Description:** Create a business profile (for HOUSE_AGENT, LAND_AGENT, VENDOR, SERVICE_PROVIDER only)
- **🔐 Authentication:** Required (Bearer Token)

**📤 Request Body:**
```json
{
  "business_name": "Acme Corporation",
  "registration_number": "RC12345678",
  "business_email": "contact@acme.com",
  "country_code": "NG",
  "address": "123 Business Street, Lagos",
  "phone_number": "+2341234567890",
  "website": "https://acme.com"
}
```

**✅ Success Response (Status: 201 Created):**
```json
{
  "success": true,
  "message": "Business profile created successfully",
  "data": {
    "id": 1,
    "user_id": 123,
    "business_name": "Acme Corporation",
    "registration_number": "RC12345678",
    "business_email": "contact@acme.com",
    "address": "123 Business Street, Lagos",
    "phone_number": "+2341234567890",
    "website": "https://acme.com",
    "verification_id": null,
    "is_business_email_verified": false,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  "status_code": 201
}
```

### 5.2. 🔍 Initiate Business Verification

- **🔗 Endpoint:** `/api/v1/business-verification/verify/`
- **📡 HTTP Method:** `POST`
- **📝 Description:** Start business verification process with external provider
- **🔐 Authentication:** Required (Bearer Token)

**📤 Request Body:**
```json
{
  "country_code": "NG"
}
```

**✅ Success Response (Status: 201 Created):**
```json
{
  "success": true,
  "message": "Business verification initiated successfully",
  "data": {
    "id": 1,
    "user_id": 123,
    "business_name": "Acme Corporation",
    "business_email": "contact@acme.com",
    "business_registration_number": "RC12345678",
    "country_code": "NG",
    "verification_provider_reference": null,
    "verification_status": "PENDING",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  "status_code": 201
}
```

### 5.3. 📊 Get Business Verification Status

- **🔗 Endpoint:** `/api/v1/business-verification/status/`
- **📡 HTTP Method:** `GET`
- **📝 Description:** Get current business verification status
- **🔐 Authentication:** Required (Bearer Token)

**📤 Request Body:** None

**✅ Success Response (Status: 200 OK):**
```json
{
  "success": true,
  "message": "Business verification status retrieved successfully",
  "data": {
    "id": 1,
    "user_id": 123,
    "business_name": "Acme Corporation",
    "business_email": "contact@acme.com",
    "business_registration_number": "RC12345678",
    "country_code": "NG",
    "verification_provider_reference": "YV_REF_123456",
    "verification_status": "SUCCESSFUL",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T11:00:00Z"
  },
  "status_code": 200
}
```

### 5.4. 📧 Request Business Email Verification

- **🔗 Endpoint:** `/api/v1/business-verification/verify-email/request/`
- **📡 HTTP Method:** `POST`
- **📝 Description:** Request business email verification
- **🔐 Authentication:** Required (Bearer Token)

**📤 Request Body:**
```json
{
  "business_email": "contact@acme.com"
}
```

**✅ Success Response (Status: 200 OK):**
```json
{
  "success": true,
  "message": "A new verification link has been sent to your business email.",
  "data": null,
  "status_code": 200
}
```

### 5.5. ✅ Verify Business Email

- **🔗 Endpoint:** `/api/v1/business-verification/verify-email/{verification_uuid}/{verification_token}/`
- **📡 HTTP Method:** `POST`
- **📝 Description:** Verify business email address
- **🔐 Authentication:** Not Required
- **🔗 URL Parameters:**
  - `verification_uuid`: string (required) - Business verification UUID
  - `verification_token`: string (required) - Verification token from email

**📤 Request Body:** None

**✅ Success Response (Status: 200 OK):**
```json
{
  "success": true,
  "message": "Business email verification successful. Welcome to Housing & Properties!",
  "data": null,
  "status_code": 200
}
```

---

## ⚙️ Configuration

### 🔐 Environment Variables

```env
# Django Core
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ENVIRONMENT=development
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Database
DJANGO_DATABASE_URL=postgresql://user:password@localhost:5432/housing_properties

# Authentication & Verification
DJANGO_VERIFICATION_TOKEN_EXPIRY=15
FROM_DOMAIN=http://127.0.0.1:8000
FRONTEND_URL=http://localhost:3000
FRONTEND_VERIFICATION_URL=http://localhost:3000/verify_email

# Email Configuration
DEFAULT_FROM_EMAIL=noreply@housingandproperties.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Social Authentication
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_client_secret

# Business Verification
BUSINESS_VERIFICATION_PROVIDER=youverify
YOUVERIFY_API_TOKEN=your_youverify_api_token
YOUVERIFY_BASE_URL=https://api.sandbox.youverify.co

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security & CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 🔧 User Types

```python
BUYER = "BUYER"                        # Regular users browsing properties
HOUSE_AGENT = "HOUSE_AGENT"            # Real estate agents (housing)
LAND_AGENT = "LAND_AGENT"              # Real estate agents (land)
VENDOR = "VENDOR"                      # Service providers and contractors
SERVICE_PROVIDER = "SERVICE_PROVIDER"  # Additional service providers
ADMIN = "ADMIN"                        # System administrators
```

### 📋 Business Verification Statuses

```python
PENDING = "PENDING"           # Initial state
IN_PROGRESS = "IN_PROGRESS"   # Being processed
FAILED = "FAILED"             # Verification failed
SUCCESSFUL = "SUCCESSFUL"     # Verification completed
```
---

## 🚀 Deployment

### 🐳 Production Docker

```bash
# Set environment
echo "DJANGO_ENVIRONMENT=production" >> .env

# Deploy
docker-compose up -d

# Collect static files
docker-compose exec web uv run manage.py collectstatic --noinput

# Apply migrations
docker-compose exec web uv run manage.py migrate
```

### 🔒 Production Security Checklist

- [ ] HTTPS enabled (`SECURE_SSL_REDIRECT = True`)
- [ ] Strong secret key configured
- [ ] Debug disabled (`DJANGO_DEBUG = False`)
- [ ] Database credentials secured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Email backend configured
- [ ] OAuth2 credentials secured
- [ ] Monitoring and logging set up

### 📈 Performance Optimization

- **Database**: Connection pooling, strategic indexing
- **Caching**: Redis for sessions and tokens
- **Async Processing**: Celery for background tasks
- **Static Files**: WhiteNoise for production

---

## 🔧 Development Workflow

### 📝 Available Commands

```bash
make install     # Install dependencies
make migrations  # Create new migrations
make migrate     # Apply database migrations
make superuser   # Create superuser
make test        # Run tests
make run         # Run development server
make clean       # Clean cache and temporary files
```

### 🎨 Code Quality

```bash
# Format code
make format

# Run pre-commit hooks
pre-commit run --all-files
```
---

## 🚨 Error Handling

### 📋 Standard Error Response Format

```json
{
  "success": false,
  "message": "Error occurred",
  "error": {
    "detail": "Specific error details"
  },
  "status_code": 400
}
```

### 🔍 Common Error Codes

- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **409 Conflict** - Resource conflict (duplicate email, etc.)
- **422 Unprocessable Entity** - Validation errors
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error
---
