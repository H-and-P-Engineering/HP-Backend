# Business Verification System Documentation

A comprehensive business verification system that validates business registration and enables business email verification through external providers.

## Table of Contents

1. [System Overview](#system-overview)
2. [Business Profile Management](#business-profile-management)
3. [Verification Process](#verification-process)
4. [YouVerify Integration](#youverify-integration)
5. [Email Verification](#email-verification)
6. [API Endpoints](#api-endpoints)
7. [Data Models](#data-models)
8. [Configuration](#configuration)
9. [Error Handling](#error-handling)

## System Overview

### Architecture

The business verification system follows Clean Architecture principles with these components:

- **Application Rules**: Business verification logic and orchestration
- **Domain Models**: Business profile and verification entities
- **Infrastructure**: External service integrations (YouVerify API)
- **Events**: Async processing for verification and notifications

### Key Features

- Business profile creation and management
- Automated business registration verification
- Business email verification
- Integration with external verification providers
- Event-driven async processing
- Comprehensive audit logging

### User Types

Only certain user types can create business profiles:
- **AGENT**: Real estate agents
- **VENDOR**: Service providers and contractors
- **SERVICE_PROVIDER**: Additional service providers

Note: CLIENT and ADMIN users cannot create business profiles.

## Business Profile Management

### Profile Creation

Business profiles are created via the `/api/v1/business-verification/create-profile/` endpoint.

#### Required Fields

```json
{
  "business_name": "string (max 255 chars)",
  "registration_number": "string (max 50 chars)",
  "business_email": "email (max 255 chars)",
  "country_code": "string (max 10 chars)"
}
```

#### Optional Fields

```json
{
  "address": "string (max 500 chars)",
  "phone_number": "string (max 20 chars)",
  "website": "URL (max 255 chars)"
}
```

#### Registration Number Validation

```python
# Valid prefixes for Nigerian businesses
valid_prefixes = ["RC", "BN", "IT", "LP", "LLP"]

# Examples:
# RC12345678 - Valid
# BN98765432 - Valid
# ABC1234567 - Invalid (wrong prefix)
```

#### Business Rules

1. **User Type Validation**: Only AGENT, VENDOR, SERVICE_PROVIDER can create profiles
2. **Unique Constraints**: Registration numbers and business emails must be unique
3. **One Profile Per User**: Each user can only have one business profile
4. **Data Normalization**: Registration numbers are automatically uppercased and trimmed

### Profile Features

- **UUID7 Identifiers**: For better database performance
- **Audit Timestamps**: Automatic created_at and updated_at tracking
- **Email Verification Status**: Tracks business email verification
- **Verification Linking**: Connects to verification records

## Verification Process

### Verification Statuses

```python
class VerificationStatus(StrEnum):
    PENDING = "PENDING"           # Initial state
    IN_PROGRESS = "IN_PROGRESS"   # Being processed
    FAILED = "FAILED"             # Verification failed
    SUCCESSFUL = "SUCCESSFUL"     # Verification completed
```

### Verification Flow

1. **Initiation**
   ```
   POST /api/v1/business-verification/verify/
   ```

2. **Async Processing**
   - Status updated to IN_PROGRESS
   - External API call to verification provider
   - Status updated based on result

3. **Status Tracking**
   ```
   GET /api/v1/business-verification/status/
   ```

4. **Email Verification** (if business verification successful)
   - Business email verification initiated
   - Email sent with verification link
   - Email verification required to complete process

### Process Rules

1. **Profile Required**: Business profile must exist before verification
2. **Single Active Verification**: Only one verification per user
3. **Retry Logic**: Failed verifications can be retried
4. **Success Prevention**: Already successful verifications cannot be repeated

## YouVerify Integration

### API Configuration

```env
BUSINESS_VERIFICATION_PROVIDER=youverify
YOUVERIFY_API_TOKEN=your_api_token
YOUVERIFY_BASE_URL=https://api.sandbox.youverify.co  # Sandbox
YOUVERIFY_BASE_URL=https://api.youverify.co        # Production
```

### Verification Request

```python
# YouVerify API call
{
  "registrationNumber": "RC12345678",
  "countryCode": "NG",
  "isConsent": True
}
```

### Response Processing

```python
# Successful verification response
{
  "success": True,
  "provider_reference": "YV_REF_123456",
  "business_data": {
    "company_name": "Acme Corporation",
    "status": "found",
    "registration_number": "RC12345678"
  }
}

# Failed verification response
{
  "success": False,
  "error_message": "Business not found or verification failed"
}
```

### Error Handling

- **Network Errors**: Handled with appropriate error messages
- **API Errors**: Status code and response logging
- **Timeout Handling**: 30-second request timeout
- **Retry Logic**: Failed verifications can be retried

## Email Verification

### Business Email Verification Flow

After successful business verification:

1. **Verification Email Sent**
   - Secure token generated (32-byte URL-safe)
   - Token cached with 15-minute expiration
   - Email sent with verification link

2. **Email Verification**
   ```
   POST /api/v1/business-verification/verify-email/{uuid}/{token}/
   ```

3. **Verification Completion**
   - Token validated against cache
   - Business profile updated
   - Verification status cached

### Email Templates

- **Success Template**: `business_verification_success.html`
- **Failure Template**: `business_verification_failure.html`
- **Email Verification**: `verify_email.html` (with business context)

### Security Features

- **Time-Limited Tokens**: 15-minute expiration
- **UUID Validation**: Prevents token misuse
- **Cache-Based Storage**: No database persistence of tokens
- **Replay Protection**: Tokens can only be used once

## API Endpoints

### Business Verification Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/business-verification/create-profile/` | Create business profile | Yes |
| POST | `/api/v1/business-verification/verify/` | Initiate verification | Yes |
| GET | `/api/v1/business-verification/status/` | Get verification status | Yes |
| POST | `/api/v1/business-verification/verify-email/{uuid}/{token}/` | Verify business email | No |
| POST | `/api/v1/business-verification/verify-email/request/` | Request email verification | Yes |

### Request Examples

#### Create Business Profile

```bash
curl -X POST /api/v1/business-verification/create-profile/ \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Acme Corporation",
    "registration_number": "RC12345678",
    "business_email": "contact@acme.com",
    "country_code": "NG",
    "address": "123 Business Street, Lagos",
    "phone_number": "+2341234567890",
    "website": "https://acme.com"
  }'
```

#### Initiate Verification

```bash
curl -X POST /api/v1/business-verification/verify/ \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "NG"
  }'
```

#### Check Status

```bash
curl -X GET /api/v1/business-verification/status/ \
  -H "Authorization: Bearer your_access_token"
```

### Response Examples

#### Successful Profile Creation

```json
{
  "success": true,
  "message": "Business profile created successfully",
  "data": {
    "id": 1,
    "business_name": "Acme Corporation",
    "registration_number": "RC12345678",
    "business_email": "contact@acme.com",
    "is_business_email_verified": false,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### Verification Status

```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": 123,
    "business_name": "Acme Corporation",
    "business_registration_number": "RC12345678",
    "verification_status": "SUCCESSFUL",
    "verification_provider_reference": "YV_REF_123456",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T11:00:00Z"
  }
}
```

## Data Models

### Business Profile

```python
@dataclass
class BusinessProfile:
    user_id: int
    business_name: str
    business_email: str
    registration_number: str
    address: str | None = None
    phone_number: str | None = None
    website: str | None = None
    verification_id: int | None = None
    is_business_email_verified: bool = False
    id: int | None = None
    uuid: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

### Business Verification

```python
@dataclass
class BusinessVerification:
    user_id: int
    business_name: str
    business_email: str
    business_registration_number: str
    country_code: str = "NG"
    verification_provider: str | None = None
    verification_provider_reference: str | None = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    id: int | None = None
    uuid: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

### Django Models

#### Business Profile Model

```python
class BusinessProfile(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    business_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, unique=True)
    business_email = models.EmailField(max_length=255, unique=True)
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    verification = models.OneToOneField("BusinessVerification", on_delete=models.SET_NULL, null=True)
    is_business_email_verified = models.BooleanField(default=False)
    uuid = models.UUIDField(unique=True, default=uuid6.uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_profiles"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["business_name"]),
            models.Index(fields=["business_email"]),
            models.Index(fields=["registration_number"]),
        ]
```

#### Business Verification Model

```python
class BusinessVerification(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    business_registration_number = models.CharField(max_length=100)
    business_name = models.CharField(max_length=255, null=True, blank=True)
    business_email = models.EmailField(null=True, blank=True)
    country_code = models.CharField(max_length=10, default="NG")
    verification_provider = models.CharField(max_length=100, null=True, blank=True)
    verification_provider_reference = models.CharField(max_length=100, null=True, blank=True)
    verification_status = models.CharField(
        max_length=12,
        choices=VerificationStatus.choices(),
        default=VerificationStatus.PENDING,
    )
    uuid = models.UUIDField(unique=True, default=uuid6.uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_verifications"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["business_registration_number"]),
            models.Index(fields=["verification_status"]),
        ]
```

## Configuration

### Environment Variables

```env
# Business Verification Provider
BUSINESS_VERIFICATION_PROVIDER=youverify

# YouVerify Configuration
YOUVERIFY_API_TOKEN=your_youverify_api_token
YOUVERIFY_BASE_URL=https://api.sandbox.youverify.co

# Verification Settings
BUSINESS_VERIFICATION_TIMEOUT=30
BUSINESS_EMAIL_VERIFICATION_EXPIRY=15

# Email Configuration (inherited from core)
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Cache Configuration (inherited from core)
DJANGO_CACHE_TIMEOUT=600
```

### Settings Configuration

```python
# Django settings.py
INSTALLED_APPS = [
    # ...
    'apps.business_verification',
    # ...
]

# Business verification specific settings
BUSINESS_VERIFICATION_PROVIDER = env.str("BUSINESS_VERIFICATION_PROVIDER", default="youverify")
YOUVERIFY_API_TOKEN = env.str("YOUVERIFY_API_TOKEN", default="")
YOUVERIFY_BASE_URL = env.str("YOUVERIFY_BASE_URL", default="https://api.sandbox.youverify.co")
```

## Error Handling

### Common Error Messages

```python
# User validation errors
"User not found"
"User does not need business profile"
"Business profile already exists for this user"

# Profile validation errors
"Business profile not found for user"
"Profile with provided registration number already exists"
"Profile with business email already exists"

# Verification errors
"Business verification already successful"
"Business verification not found for user"
"Business verification was not successful"

# Email verification errors
"Business email is already verified"
"Verification session is invalid or expired"
"Provided verification id or verification token is invalid"
```

### HTTP Error Responses

```json
{
  "success": false,
  "message": "Error occurred",
  "error": {
    "detail": "Specific error message"
  },
  "status_code": 400
}
```

### External API Errors

```python
# YouVerify API error handling
try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    if response.status_code != 200:
        return BusinessVerificationResult(
            success=False,
            error_message=f"API error: {response.status_code}"
        )
except requests.exceptions.RequestException as e:
    return BusinessVerificationResult(
        success=False,
        error_message="Network error during verification"
    )
```

## Event System

### Domain Events

```python
class BusinessVerificationRequestedEvent:
    """Triggered when verification is initiated"""
    verification_id: int

class BusinessVerificationSuccessfulEvent:
    """Triggered when external verification succeeds"""
    verification_id: int
    user_id: int
    business_name: str
    business_email: str

class BusinessVerificationFailedEvent:
    """Triggered when external verification fails"""
    verification_id: int
    user_id: int
    business_name: str
    business_email: str
    error_reason: str

class BusinessVerificationEmailEvent:
    """Triggered to send business email verification"""
    verification_id: int

class BusinessEmailVerificationSuccessfulEvent:
    """Triggered when business email is verified"""
    verification_id: int
```

### Event Handlers

```python
# Async verification processing
def process_business_verification_event(event, rule):
    rule.execute(event.verification_id)

# Success email notification
def send_verification_success_email(event, email_service, repository):
    verification = repository.get_by_id(event.verification_id)
    email_service.send_business_verification_success_email(
        recipient_email=verification.business_email,
        business_name=verification.business_name,
        registration_number=verification.business_registration_number,
        provider_reference=verification.verification_provider_reference
    )

# Failure email notification
def send_verification_failed_email(event, email_service, repository):
    verification = repository.get_by_id(event.verification_id)
    email_service.send_business_verification_failed_email(
        recipient_email=event.business_email,
        business_name=event.business_name,
        registration_number=verification.business_registration_number,
        error_reason=event.error_reason
    )
```

## Testing

### Test Structure

```
apps/business_verification/tests/
├── application/          # Business logic tests
├── domain/              # Domain model tests
└── infrastructure/      # Service integration tests
```

### Running Tests

```bash
# Run business verification tests
pytest apps/business_verification/tests/

# Run with coverage
pytest apps/business_verification/tests/ --cov=apps/business_verification

# Run specific test file
pytest apps/business_verification/tests/application/test_rules.py
```

## Usage Examples

### Complete Verification Flow

```bash
# 1. Create business profile
curl -X POST /api/v1/business-verification/create-profile/ \
  -H "Authorization: Bearer token" \
  -d '{"business_name": "Acme Corp", "registration_number": "RC12345678", ...}'

# 2. Initiate verification
curl -X POST /api/v1/business-verification/verify/ \
  -H "Authorization: Bearer token" \
  -d '{"country_code": "NG"}'

# 3. Check status
curl -X GET /api/v1/business-verification/status/ \
  -H "Authorization: Bearer token"

# 4. Request business email verification (after success)
curl -X POST /api/v1/business-verification/verify-email/request/ \
  -H "Authorization: Bearer token" \
  -d '{"business_email": "contact@acme.com"}'

# 5. Verify email (from email link)
curl -X POST /api/v1/business-verification/verify-email/{uuid}/{token}/
```

## Performance Considerations

### Database Optimization

- Strategic indexes on frequently queried fields
- UUID7 for better database performance
- Optimized queries in repositories
- Proper foreign key relationships

### Caching Strategy

- Verification result caching
- Email verification token storage
- Status check optimization
- Template caching for emails

### External API Optimization

- Request timeout configuration (30 seconds)
- Error handling and retry logic
- Async processing to prevent blocking
- Rate limiting to prevent abuse

## Deployment

### Production Checklist

- [ ] YouVerify API credentials configured
- [ ] Email backend configured for notifications
- [ ] Redis cache configured
- [ ] Celery worker running for async processing
- [ ] Database migrations applied
- [ ] Monitoring for external API calls
- [ ] Error alerting configured

### Monitoring

- External API response times
- Verification success/failure rates
- Email delivery status
- Cache hit rates
- Database query performance