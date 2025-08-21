# Housing & Properties Backend API

A comprehensive marketplace platform backend built with Django 5 and Django REST Framework, implementing Clean Architecture principles.

## Features

- **Authentication System**: JWT-based with social auth, email verification, and token blacklisting
- **User Management**: Multi-type users (CLIENT, AGENT, VENDOR, SERVICE_PROVIDER, ADMIN)
- **Business Verification**: Automated business registration verification with YouVerify integration
- **RESTful API**: Consistent, scalable API endpoints with OpenAPI documentation
- **Security**: Rate limiting, password validation, CSRF protection
- **Email System**: Template-based email verification and notifications
- **Event-Driven Architecture**: Async processing with Celery

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Django | >=5.2.3 |
| API | Django REST Framework | >=3.16.0 |
| Database | PostgreSQL/SQLite | Latest |
| Authentication | JWT (SimpleJWT) | >=5.5.0 |
| Documentation | drf-spectacular | >=0.28.0 |
| Logging | Loguru | >=0.7.3 |
| Testing | Pytest | >=8.4.0 |
| Package Manager | uv | Latest |
| Code Quality | Ruff + pre-commit | Latest |
| Social Auth | drf-social-oauth2 | >=3.1.0 |
| Task Queue | Celery | >=5.3.1 |
| Caching | Redis | >=6.2.0 |
| UUID Generation | uuid6 | >=2025.0.0 |

## Architecture

The project follows Clean Architecture with clear separation of concerns:

```
Domain Layer (Business Entities)
    ↑
Application Layer (Use Cases/Business Rules)
    ↑
Infrastructure Layer (Data Access, External Services)
    ↑
Presentation Layer (API Views, Serializers)
```

## Project Structure

```
housing_properties/
├── apps/                        # Domain applications
│   ├── authentication/          # Auth & authorization
│   ├── business_verification/   # Business verification
│   └── users/                   # User management
├── api/                         # API routing & versioning
├── config/                      # Django configuration
├── core/                        # Shared utilities
├── docs/                        # Documentation
└── logs/                        # Application logs
```

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ (recommended for production)
- Redis 6+ (for caching and Celery)
- uv (package manager)

### Installation

1. **Clone and setup**
```bash
git clone <repository-url>
cd housing_properties
uv venv --python 3.12
source .venv/bin/activate  # Linux/macOS
```

2. **Install dependencies**
```bash
make install
# or manually: uv sync
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
# Server available at: http://localhost:8000
```

### Development Commands

```bash
make install     # Install dependencies
make run         # Run development server
make migrate     # Run migrations
make migrations  # Create new migrations
make superuser   # Create superuser
make clean       # Clean cache and temporary files
pytest           # Run tests
pytest --cov     # Run tests with coverage
```

## Environment Variables

Critical environment variables for `.env`:

```env
# Django Core
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ENVIRONMENT=development
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Database
DJANGO_DATABASE_URL=postgresql://user:password@localhost:5432/housing_properties

# Redis/Cache
DJANGO_CACHE_TIMEOUT=600

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
FRONTEND_URL=http://localhost:3000

# Social Authentication
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_client_secret

# Business Verification
BUSINESS_VERIFICATION_PROVIDER=youverify
YOUVERIFY_API_TOKEN=your_youverify_api_token
YOUVERIFY_BASE_URL=https://api.sandbox.youverify.co

# Security & CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## API Endpoints

### Authentication
```
POST   /api/v1/authentication/register/
POST   /api/v1/authentication/login/
POST   /api/v1/authentication/logout/
PUT    /api/v1/authentication/update-user-type/
POST   /api/v1/authentication/verify-email/request/
POST   /api/v1/authentication/verify-email/{uuid}/{token}/
GET    /api/v1/authentication/social/begin/{backend}/
GET    /api/v1/authentication/social/complete/{backend}/
GET    /api/v1/authentication/social/data/
```

### Business Verification
```
POST   /api/v1/business-verification/create-profile/
POST   /api/v1/business-verification/verify/
GET    /api/v1/business-verification/status/
POST   /api/v1/business-verification/verify-email/{uuid}/{token}/
POST   /api/v1/business-verification/verify-email/request/
```

### Documentation
- **Swagger UI**: http://localhost:8000/api/docs/swagger/
- **ReDoc**: http://localhost:8000/api/docs/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## API Examples

### User Registration
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

### User Login
```bash
curl -X POST http://localhost:8000/api/v1/authentication/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### Business Profile Creation
```bash
curl -X POST http://localhost:8000/api/v1/business-verification/create-profile/ \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Acme Corp",
    "registration_number": "RC123456",
    "business_email": "business@acme.com",
    "country_code": "NG"
  }'
```

## Docker Deployment

### Development
```bash
docker-compose up --build
docker-compose exec web uv run manage.py createsuperuser
```

### Production
```bash
echo "DJANGO_ENVIRONMENT=production" >> .env
docker-compose up -d
docker-compose exec web uv run manage.py collectstatic --noinput
docker-compose exec web uv run manage.py migrate
```

## Security

### Production Security Checklist
- [ ] HTTPS enabled (`SECURE_SSL_REDIRECT = True`)
- [ ] Strong secret key
- [ ] Debug disabled (`DJANGO_DEBUG = False`)
- [ ] Secure database credentials
- [ ] CORS configured for allowed origins
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Secure email backend
- [ ] OAuth2 credentials secured
- [ ] Appropriate log levels

### Security Headers (Auto-applied in production)
```python
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific tests
pytest apps/authentication/tests/
pytest -v  # verbose output
```

## Performance & Monitoring

### Database Optimization
- Connection pooling with `DATABASE_CONN_MAX_AGE`
- Strategic indexing on frequently queried fields
- UUID7 usage for better performance

### Caching Strategy
- Redis caching for session data and tokens
- Template caching for static content
- Configurable timeout via `DJANGO_CACHE_TIMEOUT`

### Monitoring
- Structured logging with Loguru
- Log rotation (10MB files, 10-day retention)
- Performance metrics via Django admin
- Error tracking with detailed stack traces

## Development Workflow

### Code Quality
```bash
make clean           # Format code
make install         # Install pre-commit hooks
pre-commit run --all-files  # Run hooks manually
```

### Environment Management
- **Development**: SQLite, console email, LocMem cache
- **Production**: PostgreSQL, SMTP email, Redis cache
- **Testing**: In-memory database, test settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Submit a pull request

### Code Standards
- Follow PEP 8 (enforced by pre-commit)
- Write comprehensive tests
- Document new features
- Use conventional commit messages
- Maintain backward compatibility
- Follow Clean Architecture principles

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [DRF Documentation](https://www.django-rest-framework.org/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [YouVerify API](https://docs.youverify.co/)