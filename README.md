# HP-Backend

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-6.0-green.svg)](https://djangoproject.com)

Real estate marketplace backend with JWT auth, business verification, and location intelligence.

---

## What It Does

HP-Backend is a Django REST API for property marketplaces. It handles:

1. **Authentication** - JWT tokens, social login (Google), email verification
2. **Business Verification** - CAC verification via YouVerify API
3. **Location Intelligence** - Nearby services, geocoding via Mapradar

---

## Installation

<details open>
<summary><strong>Quick Start</strong></summary>

```bash
git clone <repository-url>
cd HP-Backend
uv sync
cp .env.example .env  # Configure your environment
uv run manage.py migrate
uv run manage.py runserver
```

</details>

<details>
<summary><strong>With Celery</strong></summary>

```bash
# Terminal 1: Django server
uv run manage.py runserver

# Terminal 2: Celery worker
uv run celery -A core worker -l info -Q default,emails,caching,monitoring,users

# Terminal 3: Redis (if not running)
redis-server
```

</details>

---

## Features

| Feature                   | Description                             |
| ------------------------- | --------------------------------------- |
| **JWT Auth**              | Access/refresh tokens with blacklisting |
| **Social Login**          | Google OAuth2 integration               |
| **Email Verification**    | Token-based email confirmation          |
| **Business Verification** | CAC lookup via YouVerify                |
| **Location Services**     | Geocoding, nearby places via Mapradar   |
| **Background Tasks**      | Celery for async operations             |
| **Single Session**        | New login invalidates previous tokens   |

---

## API Endpoints

| Endpoint                                              | Method | Description            |
| ----------------------------------------------------- | ------ | ---------------------- |
| `/api/v1/authentication/register/`                    | POST   | Create account         |
| `/api/v1/authentication/login/`                       | POST   | Get JWT tokens         |
| `/api/v1/authentication/logout/`                      | POST   | Blacklist token        |
| `/api/v1/authentication/verify-email/{uuid}/{token}/` | POST   | Verify email           |
| `/api/v1/users/update-user-type/`                     | PUT    | Change user type       |
| `/api/v1/business-verification/create-profile/`       | POST   | Create business        |
| `/api/v1/business-verification/verify/`               | POST   | Start CAC verification |
| `/api/v1/location/nearby-services/`                   | POST   | Find nearby amenities  |

<details>
<summary><strong>API Documentation</strong></summary>

- **Swagger UI**: http://localhost:8000/api/docs/swagger/
- **ReDoc**: http://localhost:8000/api/docs/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

</details>

---

## API Reference

All responses follow this format:

```json
{
  "success": true,
  "message": "Description of result",
  "data": { ... },
  "status_code": 200
}
```

### Authentication

<details open>
<summary><strong>Register</strong></summary>

**POST** `/api/v1/authentication/register/`

```json
// Request
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+2341234567890",
  "user_type": "BUYER"
}

// Response (201)
{
  "success": true,
  "message": "Registration successful. Check your email for a verification link.",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "user_type": "BUYER",
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "+2341234567890",
      "is_email_verified": false,
      "is_new": true
    }
  }
}
```

</details>

<details>
<summary><strong>Request Email Verification</strong></summary>

**POST** `/api/v1/authentication/verify-email/request/`

```json
// Request
{
  "email": "user@example.com"
}

// Response (200)
{
  "success": true,
  "message": "A new verification link has been sent to your email.",
  "data": null
}
```

</details>

<details>
<summary><strong>Verify Email</strong></summary>

**POST** `/api/v1/authentication/verify-email/{uuid}/{token}/`

```json
// Request
{
  "uuid": "019c5344-212e-7a8e-98b6-dbf565f42732",
  "token": "jEOsnW7sh439DzgS9wxjR6aQ3PpjzmWVR8gnqhctCjE"
}

// Response (200)
{
  "success": true,
  "message": "Email verification successful. You can now login.",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "user_type": "BUYER",
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "+2341234567890",
      "is_email_verified": true,
      "is_new": true
    }
  }
}
```

</details>

<details>
<summary><strong>Login</strong></summary>

**POST** `/api/v1/authentication/login/`

```json
// Request
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

// Response (200)
{
  "success": true,
  "message": "Login successful. Welcome back!",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "user_type": "BUYER",
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "+2341234567890",
      "is_email_verified": true,
      "is_new": true
    }
  }
}
```

</details>

<details>
<summary><strong>Logout</strong></summary>

**POST** `/api/v1/authentication/logout/` (Requires Bearer token)

```json
// Request
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

// Response (200)
{
  "success": true,
  "message": "Logout successful.",
  "data": null
}
```

</details>

<details>
<summary><strong>Social Auth (Google)</strong></summary>

**Flow:**

1. Redirect to `GET /api/v1/authentication/social/begin/google-oauth2/?user_type=BUYER`
2. User authenticates with Google
3. Callback redirects, then fetch tokens from `GET /api/v1/authentication/social/data/`

```json
// Response from /social/data/ (200)
{
  "success": true,
  "message": "Login successful. Welcome back!",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": { ... }
  }
}
```

</details>

### Business Verification

<details>
<summary><strong>Create Business Profile</strong></summary>

**POST** `/api/v1/business-verification/create-profile/` (Requires Bearer token)

```json
// Request
{
  "business_name": "Acme Realty",
  "registration_number": "RC12345678",
  "business_email": "contact@acme.com",
  "country_code": "NG",
  "address": "123 Business Street, Lagos"
}

// Response (201)
{
  "success": true,
  "message": "Business profile created successfully",
  "data": {
    "id": 1,
    "business_name": "Acme Realty",
    "registration_number": "RC12345678",
    "is_business_email_verified": false
  }
}
```

</details>

<details>
<summary><strong>Initiate Verification</strong></summary>

**POST** `/api/v1/business-verification/verify/` (Requires Bearer token)

```json
// Request
{
  "country_code": "NG"
}

// Response (201)
{
  "success": true,
  "message": "Business verification initiated successfully",
  "data": {
    "verification_status": "PENDING"
  }
}
```

**Statuses:** `PENDING` → `IN_PROGRESS` → `SUCCESSFUL` | `FAILED`

</details>

### Location Intelligence

<details>
<summary><strong>Find Nearby Services</strong></summary>

**POST** `/api/v1/location/nearby-services/` (Requires Bearer token)

```json
// Request (by address)
{
  "address": "Victoria Island, Lagos",
  "service_types": ["HOSPITAL", "SCHOOL", "BANK"],
  "radius_km": 5.0
}

// Request (by coordinates)
{
  "latitude": 6.4281,
  "longitude": 3.4219,
  "service_types": ["HOSPITAL"],
  "radius_km": 3.0
}

// Response (200)
{
  "success": true,
  "data": {
    "location": {
      "address": "Victoria Island, Lagos",
      "latitude": 6.4281,
      "longitude": 3.4219,
      "country": "NG"
    },
    "nearby_services": [
      {
        "name": "Lagos University Teaching Hospital",
        "service_type": "HOSPITAL",
        "distance_km": 2.1,
        "rating": 4.2
      }
    ],
    "total_services_found": 12
  }
}
```

**Service Types:** `HOSPITAL`, `SCHOOL`, `BANK`, `MARKET`, `MALL`, `RESTAURANT`, `FUEL_STATION`, `BUS_STOP`, `TRAIN_STATION`

</details>

### Error Responses

```json
// 400 Bad Request
{
  "success": false,
  "message": "Validation failed",
  "error": { "email": ["This field is required."] }
}

// 401 Unauthorized
{
  "success": false,
  "message": "Authentication credentials were not provided."
}

// 404 Not Found
{
  "success": false,
  "message": "User not found."
}
```

---

## Project Structure

```
HP-Backend/
├── api/v1/              # URL routing
├── users/               # Auth, user management
├── business/            # Business profiles, verification
├── location/            # Geocoding, nearby services
├── core/                # Shared utils, Celery tasks
├── monitoring/          # Health checks, DLQ
└── config/              # Django settings
```

---

## Configuration

| Variable              | Description                 |
| --------------------- | --------------------------- |
| `DJANGO_SECRET_KEY`   | Django secret key           |
| `DJANGO_DEBUG`        | Debug mode (`True`/`False`) |
| `CELERY_BROKER_URL`   | Redis URL for Celery        |
| `YOUVERIFY_API_TOKEN` | YouVerify API key           |
| `MAPRADAR_API_KEY`    | Mapradar/Google Maps key    |

<details>
<summary><strong>All Environment Variables</strong></summary>

```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Database
DJANGO_DATABASE_URL=sqlite:///db.sqlite3

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-app-password

# Social Auth
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your-client-id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your-client-secret

# External APIs
YOUVERIFY_API_TOKEN=your-token
MAPRADAR_API_KEY=your-api-key

# JWT
ACCESS_TOKEN_LIFETIME=30  # minutes
REFRESH_TOKEN_LIFETIME=24  # hours
```

</details>

---

## User Types

| Type               | Description                  |
| ------------------ | ---------------------------- |
| `BUYER`            | Property seekers             |
| `HOUSE_AGENT`      | Real estate agents (housing) |
| `LAND_AGENT`       | Real estate agents (land)    |
| `VENDOR`           | Service providers            |
| `SERVICE_PROVIDER` | Contractors                  |
| `ADMIN`            | System administrators        |

---

## Development

| Command                      | Purpose              |
| ---------------------------- | -------------------- |
| `uv sync`                    | Install dependencies |
| `uv run manage.py migrate`   | Apply migrations     |
| `uv run manage.py runserver` | Start dev server     |
| `uv run ruff check --fix .`  | Lint and fix         |
| `uv run ruff format .`       | Format code          |

---

## FAQ

<details>
<summary>How does single-session work?</summary>

When a user logs in, their previous access token is automatically blacklisted via a background task. Only one active session per user.

</details>

<details>
<summary>What happens to expired tokens on login?</summary>

The middleware clears the Authorization header for auth endpoints, so expired tokens don't block login attempts.

</details>

<details>
<summary>How is location data fetched?</summary>

Uses the `mapradar` library which wraps Google Maps APIs (Geocoding, Places).

</details>
