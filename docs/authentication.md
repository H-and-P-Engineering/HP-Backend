# Authentication System Documentation

A comprehensive authentication system implementing JWT tokens, email verification, social authentication, and secure user management.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Authentication Flow](#authentication-flow)
3. [Social Authentication](#social-authentication)
4. [Token Management](#token-management)
5. [Email Verification](#email-verification)
6. [API Endpoints](#api-endpoints)
7. [Security Features](#security-features)
8. [Configuration](#configuration)
9. [Error Handling](#error-handling)

## System Architecture

### Clean Architecture Implementation

The authentication system follows Clean Architecture principles with these layers:

- **Presentation Layer**: API views and serializers (`apps/authentication/presentation/`)
- **Application Layer**: Business rules and use cases (`apps/authentication/application/`)
- **Domain Layer**: Core business entities and events (`apps/authentication/domain/`)
- **Infrastructure Layer**: External service adapters (`apps/authentication/infrastructure/`)

### Key Components

**Application Rules (Use Cases):**
- `RegisterUserRule` - User registration with email verification
- `LoginUserRule` - User authentication and token generation
- `LogoutUserRule` - Token blacklisting for secure logout
- `VerifyEmailRule` - Email verification processing
- `UpdateUserTypeRule` - User type management
- `SocialAuthenticationRule` - Social login flows

**Infrastructure Adapters:**
- `DjangoPasswordServiceAdapter` - Password hashing and validation
- `DjangoEmailServiceAdapter` - Email sending
- `DjangoCacheServiceAdapter` - Redis/cache operations
- `DjangoJWTTokenAdapter` - JWT token management
- `SocialAuthenticationAdapter` - Social auth integration

## Authentication Flow

### User Registration

1. **Request Validation**
   - Email format validation
   - Password complexity requirements
   - User type validation
   - Required field validation

2. **Password Requirements**
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one digit
   - At least one special character
   - No spaces allowed

3. **Registration Process**
   ```python
   # Example registration request
   {
     "email": "user@example.com",
     "password": "SecurePass123!",
     "first_name": "John",
     "last_name": "Doe",
     "phone_number": "+1234567890",
     "user_type": "CLIENT"
   }
   ```

4. **Email Verification**
   - Secure token generation (32-byte URL-safe)
   - 15-minute expiration
   - Cache-based storage
   - Template-based emails

### User Login

1. **Validation Steps**
   - Email and password verification
   - Account status check (active)
   - Email verification status check

2. **JWT Token Generation**
   - Access token: 30-minute lifetime
   - Refresh token: 24-hour lifetime
   - Token rotation enabled
   - Custom claims included

3. **Login Response**
   ```json
   {
     "success": true,
     "data": {
       "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
       "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
       "user": {
         "id": "uuid-here",
         "email": "user@example.com",
         "user_type": "CLIENT",
         "is_email_verified": true
       }
     }
   }
   ```

### User Logout

1. **Token Blacklisting**
   - Access token added to blacklist
   - Token expiry validation
   - Database persistence
   - Middleware enforcement

2. **Logout Process**
   ```python
   # Logout request
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
   }
   ```

## Social Authentication

### Supported Providers

- Google OAuth2 (extensible for other providers)

### Authentication Flow

1. **Initiate Social Login**
   ```
   GET /api/v1/authentication/social/begin/google-oauth2/?user_type=CLIENT
   ```

2. **Provider Callback**
   - Automatic user creation or linking
   - Email verification bypass for social users
   - JWT token generation
   - Secure session management

3. **Complete Authentication**
   ```
   GET /api/v1/authentication/social/complete/google-oauth2/
   ```

4. **Retrieve User Data**
   ```
   GET /api/v1/authentication/social/data/
   ```

### Social Auth Pipeline

Custom pipeline handles:
- User creation with proper user type
- Email verification status
- Last login updates
- Error handling and validation

## Token Management

### JWT Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=24),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}
```

### Token Blacklisting

1. **Middleware Integration**
   ```python
   class TokenBlackListMiddleware(MiddlewareMixin):
       def process_request(self, request):
           # Check blacklisted tokens
           # Remove invalid authorization headers
   ```

2. **Database Model**
   ```python
   class BlackListedToken(models.Model):
       access = models.TextField(unique=True)
       user = models.ForeignKey("users.User", on_delete=models.CASCADE)
       expires_at = models.DateTimeField()
       created_at = models.DateTimeField(auto_now_add=True)
   ```

3. **Automatic Cleanup**
   - Expired tokens can be cleaned via management command
   - Optimized queries with proper indexing

## Email Verification

### Verification Process

1. **Token Generation**
   ```python
   token = secrets.token_urlsafe(32)  # Cryptographically secure
   ```

2. **Cache Storage**
   ```python
   cache_key = f"email_verify_{user_uuid}"
   cache_value = (user_id, token)
   timeout = 15 * 60  # 15 minutes
   ```

3. **Email Template**
   - HTML template with verification link
   - User-friendly design
   - Security warnings included

4. **Verification Link**
   ```
   POST /api/v1/authentication/verify-email/{user_uuid}/{verification_token}/
   ```

### Email Verification Security

- Time-limited tokens (15 minutes)
- UUID validation prevents token misuse
- Cache-based storage (no database persistence)
- Protection against brute-force attacks

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/authentication/register/` | User registration | No |
| POST | `/api/v1/authentication/login/` | User login | No |
| POST | `/api/v1/authentication/logout/` | User logout | Yes |
| PUT | `/api/v1/authentication/update-user-type/` | Update user type | Yes |
| POST | `/api/v1/authentication/verify-email/request/` | Request email verification | No |
| POST | `/api/v1/authentication/verify-email/{uuid}/{token}/` | Verify email | No |
| GET | `/api/v1/authentication/social/begin/{backend}/` | Start social auth | No |
| GET | `/api/v1/authentication/social/complete/{backend}/` | Complete social auth | No |
| GET | `/api/v1/authentication/social/data/` | Get social auth data | No |

### Request/Response Examples

**User Registration:**
```bash
curl -X POST /api/v1/authentication/register/ \
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

**User Login:**
```bash
curl -X POST /api/v1/authentication/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**User Type Update (Authenticated Request):**
```bash
curl -X PUT /api/v1/authentication/update-user-type/ \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "user_type": "AGENT"
  }'
```

## Security Features

### Password Security

1. **Complex Validation**
   - Multiple character type requirements
   - Minimum length enforcement
   - Common pattern detection
   - Space prohibition

2. **Secure Hashing**
   - Django's Argon2 password hasher
   - Salt-based hashing
   - Configurable iterations

### Rate Limiting

- **Anonymous users**: 5 requests/minute
- **Authenticated users**: 10 requests/minute
- **Per-endpoint control**: Configurable throttling
- **IP-based protection**: Additional security layer

### Security Headers

Production settings automatically apply:
```python
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
```

### CSRF Protection

- Built-in Django CSRF middleware
- CSRF exempt for social auth endpoints
- Secure cookie configuration

## Configuration

### Environment Variables

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key

# Email Configuration
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Email Verification
DJANGO_VERIFICATION_TOKEN_EXPIRY=15  # minutes
FROM_DOMAIN=https://yourdomain.com

# Social Authentication
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_client_secret

# Frontend URL for redirects
FRONTEND_URL=https://yourfrontend.com

# Cache Configuration
DJANGO_CACHE_TIMEOUT=600  # 10 minutes
```

### Social Auth Settings

```python
# Google OAuth2 Configuration
SOCIAL_AUTH_GOOGLE_OAUTH2_USER_FIELDS = ["email", "first_name", "last_name"]
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ["email", "profile"]

# Pipeline Configuration
SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'apps.authentication.infrastructure.pipelines.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.user.user_details',
]
```

## Error Handling

### Business Rule Exceptions

Custom exceptions for domain-specific errors:
```python
class BusinessRuleException(Exception):
    pass

# Usage examples
"Login failed. Provided email or password is invalid."
"Login failed. Requested user account is deactivated."
"Login failed. Requested user email is not verified."
"Email verification failed. Verification session is invalid or expired."
```

### HTTP Error Responses

Standardized error response format:
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

### Common Error Scenarios

1. **Registration Errors**
   - Email already exists
   - Invalid password format
   - Invalid user type

2. **Login Errors**
   - Invalid credentials
   - Account deactivated
   - Email not verified

3. **Email Verification Errors**
   - Expired token
   - Invalid token
   - Already verified

4. **Token Errors**
   - Expired access token
   - Blacklisted token
   - Invalid token format

## Data Models

### User Model

```python
class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid6.uuid7)
    username = None  # Email-based authentication
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    user_type = models.CharField(max_length=16, choices=UserType.choices)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
```

### User Types

```python
class UserType(StrEnum):
    CLIENT = "CLIENT"
    AGENT = "AGENT"
    VENDOR = "VENDOR"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    ADMIN = "ADMIN"
```

### Blacklisted Token Model

```python
class BlackListedToken(models.Model):
    access = models.TextField(unique=True)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
```

## Event System

### Domain Events

- `UserVerificationEmailEvent` - Triggers email verification
- `UserEmailVerifiedEvent` - Handles email verification completion
- `UserUpdateEvent` - Manages user data updates
- `UserLogoutEvent` - Processes user logout

### Event Handlers

Events are processed asynchronously using Celery:
```python
@shared_task
def send_verification_email(user_id, verification_link):
    # Send email asynchronously
    pass
```

## Testing

### Test Structure

```
apps/authentication/tests/
├── application/          # Business logic tests
├── domain/              # Domain model tests
├── infrastructure/      # Infrastructure tests
└── presentation/        # API endpoint tests
```

### Running Tests

```bash
# Run authentication tests
pytest apps/authentication/tests/

# Run with coverage
pytest apps/authentication/tests/ --cov=apps/authentication

# Run specific test file
pytest apps/authentication/tests/application/test_rules.py
```

## Performance Considerations

### Database Optimization

- Strategic indexes on frequently queried fields
- UUID7 for better database performance
- Connection pooling configuration
- Query optimization in repositories

### Caching Strategy

- Redis for token blacklist checks
- Email verification token storage
- Session data caching
- Template caching for emails

### Monitoring

- Structured logging with Loguru
- Request/response logging
- Error tracking and alerting
- Performance metrics collection

## Deployment

### Production Checklist

- [ ] HTTPS enabled
- [ ] Strong secret keys
- [ ] Debug mode disabled
- [ ] Secure database credentials
- [ ] Email backend configured
- [ ] Redis cache configured
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Social auth credentials secured
- [ ] Logging levels appropriate

### Docker Configuration

The authentication system works with the provided Docker setup:
```bash
docker-compose up --build
docker-compose exec web uv run manage.py migrate
docker-compose exec web uv run manage.py createsuperuser
```