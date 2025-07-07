# 🏠 Housing & Properties Authentication System Documentation

## 📋 Table of Contents

1. [🏗️ System Architecture Overview](#system-architecture-overview)
2. [📧 Email-Based Authentication Flow](#email-based-authentication-flow)
3. [🔗 Social Authentication Implementation](#social-authentication-implementation)
4. [🎫 Token Management System](#token-management-system)
5. [🗄️ Data Model Implementation](#data-model-implementation)
6. [⚙️ Service Layer Architecture](#service-layer-architecture)
7. [🌐 API Endpoint Specifications](#api-endpoint-specifications)
8. [🔒 Security Measures and Validation](#security-measures-and-validation)
9. [❌ Error Handling Framework](#error-handling-framework)
10. [⚙️ Configuration and Settings](#configuration-and-settings)

---

## 🏗️ System Architecture Overview

The **Housing & Properties** authentication system implements a sophisticated **multi-layered architecture** that separates concerns across distinct components, adhering to **Clean Architecture** principles. The system leverages `Django REST Framework` for API development, `djangorestframework-simplejwt` for JWT token management, and `drf-social-oauth2` for social authentication integration.

### 🎯 **Architectural Principles**

The architecture follows a clear separation pattern where:
- 📋 **Presentation Layer** (`apps/authentication/presentation/`):
  - **Views** handle HTTP concerns, request routing, and delegate to the Application Layer.
  - **Serializers** manage data validation and transformation for API input/output.
- 🌐 **Application Layer** (`apps/authentication/application/`):
  - **Rules** (Use Cases) encapsulate core business logic and orchestration, operating on Domain Models and interacting with the Infrastructure Layer via Ports.
  - **Ports** define interfaces for external concerns (e.g., `UserRepositoryInterface`, `EmailServiceAdapterInterface`).
- 🗄️ **Domain Layer** (`apps/authentication/domain/`):
  - **Models** are pure business entities (dataclasses).
- 🛠️ **Infrastructure Layer** (`apps/authentication/infrastructure/`):
  - **Adapters** (e.g., `DjangoPasswordServiceAdapter`, `DjangoEmailServiceAdapter`) provide concrete implementations for the Domain Layer's Ports.
  - **Repositories** (e.g., `DjangoUserRepository`, `DjangoBlackListedTokenRepository`) manage data persistence, mapping Domain Models to Django ORM models.
  - **Django ORM Models** define the database schema and are specific to the Django framework.

This layered design ensures **maintainability**, **testability** (especially for the core business logic), and **scalability** while adhering to **SOLID** principles.

---

## 📧 Email-Based Authentication Flow

### 📝 Registration Process

The email-based registration flow begins when a client sends a `POST` request to `/api/v1/authentication/register/`. The `register_user` view (in `apps/authentication/presentation/views.py`) processes this request through a **carefully orchestrated sequence** of operations, delegating to the Application Layer.

#### 🔍 **Request Validation**
Upon receiving the request, the view instantiates the `UserRegistrationSerializer` which validates the incoming data. This serializer enforces **strict validation rules** including:

- ✅ **Email format validation** - RFC-compliant email address structure
- 🔐 **Password minimum length** - 8 characters minimum requirement
- 👤 **User type selection** - from predefined choices (**CLIENT, AGENT, VENDOR, ADMIN**)
- 📝 **Mandatory name fields** - both **first** and **last name** required

#### 🛡️ **Advanced Password Validation**
Once validation passes, the view delegates to the `RegisterUserRule` (in `apps/authentication/application/rules.py`). This rule utilizes `DjangoPasswordServiceAdapter` (in `apps/authentication/infrastructure/services.py`) to perform **advanced password validation** which implements comprehensive security checks:

**Password Requirements:**
- 🚫 **No spaces allowed** - prevents copy-paste errors
- 🔤 **One uppercase letter** - enhances complexity
- 🔡 **One lowercase letter** - ensures mixed case
- 🔢 **One digit** - numerical requirement
- 🔣 **One special character** - symbol inclusion

*These validations use **regular expressions** to ensure password complexity resistant to dictionary attacks.*

#### 👤 **User Creation & Profile Setup**
After password validation succeeds, the `RegisterUserRule` calls the `DjangoUserRepository`'s `create` method (in `apps/authentication/infrastructure/repositories.py`). The repository:

1. **🔄 Normalizes** the email address for case-insensitive uniqueness.
2. **👤 Creates** the user instance in the database using Django's ORM.

*Note: User profiles (AgentProfile, VendorProfile, ClientProfile) are conceptually described in the documentation but are not currently implemented as separate Django models or domain models in the provided codebase. This is a future enhancement.* 

#### 🎫 **JWT Token Generation**
The registration process continues with JWT token generation. The `RegisterUserRule` obtains tokens via the `DjangoJWTTokenAdapter` (in `apps/authentication/infrastructure/services.py`). This adapter creates both `access` and `refresh` tokens using the `djangorestframework-simplejwt` library. These tokens include **custom claims** for:
- 🏷️ `user_type` - for role-based access control
- 📧 `email` - for quick user identification

*This enables frontend applications to make authorization decisions without additional API calls.*

#### 📬 **Email Verification Setup**
Finally, the `RegisterUserRule` orchestrates sending a verification email by utilizing the `RequestEmailVerificationRule`. This rule leverages:

1. **🔐 `DjangoVerificationServiceAdapter`**: Generates a cryptographically secure token using Python's `secrets` module and creates the verification link.
2. **💾 `DjangoCacheServiceAdapter`**: Stores the token in Django's cache with user's `UUID` as part of the key.
3. **📧 `DjangoEmailServiceAdapter`**: Triggers sending the verification email using a Django template.
4. **⏰ Expiration**: The cache entry automatically expires after a configurable period (default 15 minutes), set by `settings.DJANGO_VERIFICATION_TOKEN_EXPIRY`.

---

### 🔐 Login Process

The login flow handles authentication for existing users through the `/api/v1/authentication/login/` endpoint. The `login_user` view (in `apps/authentication/presentation/views.py`) receives credentials and validates them through the `UserLoginSerializer`, then delegates to the Application Layer.

#### 🎯 **Authentication Flow**
The `LoginUserRule` (in `apps/authentication/application/rules.py`) performs authentication using the `DjangoUserRepository` and `DjangoPasswordServiceAdapter`:

**Sequential Security Checks:**
1. **🔍 Credential Authentication** - validates email/password combination.
2. **✅ Account Status Check** - ensures account is active and accessible.
3. **📧 Email Verification Check** - enforces email verification requirement.
4. **📊 Audit Logging** - updates `last_login` timestamp for security monitoring.
5. **🎫 Token Generation** - creates fresh JWT tokens via `DjangoJWTTokenAdapter` for session management.

**Security Features:**
- 🚫 **Generic error messages** prevent username enumeration attacks.
- 🔒 **Deactivated account protection** - blocks access with `BadRequestError`.
- ✉️ **Email verification enforcement** - unverified accounts cannot login.

---

### ✉️ Email Verification Mechanism

The email verification system implements a **secure token-based approach** balancing security with user convenience. The `verify_email` view (in `apps/authentication/presentation/views.py`) delegates to the `VerifyEmailRule` for processing.

#### 🔐 **Token Generation & Storage**
When a user registers, the `RequestEmailVerificationRule`:
- **🎲 Generates** a verification token using `secrets.token_urlsafe(32)` via `DjangoVerificationServiceAdapter`.
- **💾 Stores** the token in Django's cache framework (not database) via `DjangoCacheServiceAdapter`.
- **🏷️ Uses** cache key pattern: `email_verify_{user_uuid}`.

**Cache-Based Advantages:**
- ⏰ **Automatic expiration** without cleanup jobs.
- 📈 **Reduced database load** for temporary data.
- 🔄 **Backend flexibility** (Redis, Memcached, etc.).

#### ✅ **Verification Process**
When users click verification links, the `VerifyEmailRule`:
1. **🌐 Accesses** endpoint: `/api/v1/authentication/verify-email/{user_uuid}/{verification_token}`.
2. **🔍 Validates** cached token against provided parameters via `DjangoCacheServiceAdapter`.
3. **🔐 Verifies** user UUID matches to prevent cross-account attacks.
4. **✅ Activates** account by setting `is_email_verified = True` via `DjangoUserRepository`.
5. **🧹 Cleans up** cache entry to prevent token reuse via `DjangoCacheServiceAdapter`.

---

## 🚪 Logout Implementation

### 🎯 **Overview**

The logout flow handles **invalidation of JWT access tokens** for authenticated users through the `/api/v1/authentication/logout/` endpoint. Due to the **stateless nature of JWT tokens**, access tokens cannot easily be deleted or revoked server-side, hence the need for a **token blacklisting mechanism** to prevent their further use. The `logout_user` view (in `apps/authentication/presentation/views.py`) delegates to the Application Layer.

### 🔄 **Logout Process Flow**

#### 1. 📨 **Request Processing**
The `logout_user` view receives a request's `AUTHORIZATION` header and validates it through the `UserLogoutSerializer`, which ensures proper authorization header structure for `JWTAuthentication`.

#### 2. ✅ **Token Validation & Blacklisting**
The `LogoutUserRule` (in `apps/authentication/application/rules.py`) performs validation checks on the extracted `access_token` and handles its **blacklisting** by utilizing `DjangoBlackListedTokenRepository` and `DjangoJWTTokenAdapter`:

- 🔍 **Token Validation**: The `DjangoJWTTokenAdapter` checks the token's expiry.
- ❌ **Error Handling**: If any check fails, a `ValidationError` is raised.

#### 3. 🚫 **Token Blacklisting**
Upon successful validation, the `LogoutUserRule` delegates to the `DjangoBlackListedTokenRepository` to:
- 📝 **Register** the token in the database as "blacklisted" (via `BlackListedToken` model).
- 🔒 **Prevent** future use of the token even if it hasn't expired.
- 👤 **Associate** the blacklisted token with the user account for audit purposes.

#### 4. ✨ **Cleanup & Response**
- ✅ **Success Response**: Returns confirmation of successful logout.

### 🗄️ **BlacklistedToken Model**

```python
from core.models import BaseModel
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class BlacklistedToken(BaseModel):
    """
    🚫 Model to store blacklisted JWT access tokens.

    Used in logout functionality to invalidate access tokens before expiry.
    """

    access = models.TextField(unique=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="blacklisted_tokens",
        help_text="👤 User associated with the blacklisted token"
    )
    expires_at = models.DateTimeField()

    class Meta:
        """⚙️ Metadata options for the BlacklistedToken model."""

        db_table = "auth_blacklisted_tokens"
        indexes = [
            models.Index(fields=["access", "user"]),
            models.Index(fields=["expires_at"])
        ]

    def __str__(self) -> str:
        """📝 Returns a string representation of the blacklisted token."""
        return f"🚫 Token {self.access[:20]}... for {str(self.user)} (blacklisted at {self.created_at})"

    @classmethod
    def is_blacklisted(cls, access_token: str) -> bool:
        """🔍 Check if an access token is blacklisted."""
        return cls.objects.filter(access=access_token).exists()

    @classmethod
    def cleanup_expired(cls) -> None:
        """🧹 Delete expired blacklisted tokens to keep database clean."""
        return cls.objects.filter(expires_at__lt=timezone.now()).delete()
```

### 🛡️ **TokenBlacklistMiddleware**

```python
from django.utils.deprecation import MiddlewareMixin
from apps.authentication.models import BlacklistedToken
from core.logging import logger
from rest_framework.request import Request

class TokenBlacklistMiddleware(MiddlewareMixin):
    """
    🛡️ Middleware to check if JWT tokens are blacklisted.

    This runs before the authentication backend to prevent
    blacklisted tokens from being authenticated.
    """

    def process_request(self, request: Request) -> None:
        """
        🔍 Check if the token in the request is blacklisted.

        If the token is blacklisted, clears the authorization header
        to prevent authentication and logs the attempt.
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if auth_header.startswith("Bearer "):
            # 🔧 Extract token from Bearer header
            token = auth_header.split(" ")[1]

            # 🚫 Check if token is blacklisted
            if BlacklistedToken.is_blacklisted(token):
                # 🚨 Clear authorization header to prevent authentication
                request.META["HTTP_AUTHORIZATION"] = ""

                # 📝 Log security event
                logger.warning(
                    f"🚨 Blacklisted token attempted to access: {request.path}"
                )

        return None
```

---

## 🔗 Social Authentication Implementation

The social authentication system allows users to register and log in using third-party providers like Google. This is handled by `drf-social-oauth2` and integrated into the existing authentication flow.

### 🚀 Social Authentication Flow

The social authentication process involves two main steps:

1.  **Initiating Social Login (`/api/v1/authentication/social/begin/<backend>/`):**
    *   A client initiates the social login by making a `GET` request to this endpoint, specifying the social `backend` (e.g., `google-oauth2`).
    *   An optional `user_type` query parameter can be provided (e.g., `?user_type=AGENT`) to pre-select the user's role during registration.
    *   The `begin_social_authentication` view (in `apps/authentication/presentation/views.py`) redirects the user to the social provider's authentication page.
    *   The `user_type` is stored in the session to be used during the completion phase.

2.  **Completing Social Login (`/api/v1/authentication/social/complete/<backend>/`):**
    *   After successful authentication with the social provider, the user is redirected back to this endpoint.
    *   The `complete_social_authentication` view handles the callback from the social provider.
    *   It uses the `SocialAuthenticationRule` to either retrieve an existing user or create a new user account based on the social provider's information and the `user_type` from the session.
    *   Upon successful completion, JWT tokens are generated for the user, and they are logged in.

---

## 🎫 Token Management System

### 🎯 **Overview**

This system uses `djangorestframework-simplejwt` for managing **JSON Web Tokens (JWT)**. It provides a robust, stateless authentication mechanism for the API.

### 🔄 **Token Types**
- **Access Token**: Short-lived, used for authenticating API requests.
- **Refresh Tokens**: Long-lived, used to obtain new access tokens when the current one expires.

### 🔑 **Token Creation**
Tokens are created upon successful registration or login via `DjangoJWTTokenAdapter.create_tokens`. Custom claims are included in the token payload (e.g., `user_type`, `email`).

### 🚫 **Token Blacklisting**
Upon logout, access tokens are blacklisted using the `BlacklistedToken` model and `TokenBlacklistMiddleware` to prevent their reuse before natural expiry. This is crucial for maintaining security in a stateless JWT system.

### ⏰ **Token Expiration**
Token lifetimes are configured in `settings.py` via `SIMPLE_JWT` settings, allowing for fine-grained control over session duration and security.

---

## 🗄️ Data Model Implementation

This section details the Django ORM models and their relationship to the Domain Layer's dataclasses.

### 👤 **User Model (`apps/authentication/infrastructure/models.py`)**

Extends Django's `AbstractUser` to provide a custom user model with:
- `uuid`: A `UUIDField` (using `uuid6.uuid7`) for public, unique user identification.
- `email`: `EmailField` set as `unique=True` and `USERNAME_FIELD`.
- `user_type`: `CharField` with choices from `UserType` enum (CLIENT, AGENT, VENDOR, ADMIN).
- `is_email_verified`: `BooleanField` to track email verification status.
- `created_at`, `updated_at`: `DateTimeField` for auditing.

Uses a custom `UserManager` (`apps/authentication/infrastructure/managers.py`) for user creation and management.

### 🚫 **BlacklistedToken Model (`apps/authentication/infrastructure/models.py`)**

Stores JWT access tokens that have been explicitly invalidated (e.g., during logout) to prevent their reuse.
- `access`: `TextField` storing the blacklisted JWT, `unique=True`.
- `user`: `ForeignKey` to the `User` model.
- `expires_at`: `DateTimeField` indicating when the blacklisted token would have naturally expired.

Includes a class method `is_blacklisted` for efficient lookup.

### 🎯 **Domain Models (`apps/authentication/domain/models.py`)**

These are framework-agnostic Python dataclasses representing the core business entities, used by the Application Layer:
- `User`: Corresponds to the Django `User` model, holding user attributes.
- `BlackListedToken`: Corresponds to the Django `BlacklistedToken` model.

---

## ⚙️ Service Layer Architecture

The Infrastructure Layer contains adapters that implement the interfaces (ports) defined in the Domain Layer. These services interact with external frameworks and systems (Django ORM, cache, email, JWT).

### 🔑 `DjangoPasswordServiceAdapter` (`apps/authentication/infrastructure/services.py`)
Implements `PasswordServiceAdapterInterface`.
- Provides methods for hashing, checking, and validating password complexity (e.g., minimum length, character requirements).

### ✅ `DjangoVerificationServiceAdapter` (`apps/authentication/infrastructure/services.py`)
Implements `VerificationServiceAdapterInterface`.
- Handles generation of secure verification tokens.
- Constructs full email verification links using the application's `FROM_DOMAIN`.

### 💾 `DjangoCacheServiceAdapter` (`apps/authentication/infrastructure/services.py`)
Implements `CacheServiceAdapterInterface`.
- Provides a thin wrapper around Django's cache framework (e.g., Redis).
- Used for storing temporary data like email verification tokens with configurable timeouts.

### 📧 `DjangoEmailServiceAdapter` (`apps/authentication/infrastructure/services.py`)
Implements `EmailServiceAdapterInterface`.
- Responsible for sending templated emails (e.g., email verification, password reset).
- Utilizes Django's email backend and template rendering.

### 🎫 `DjangoJWTTokenAdapter` (`apps/authentication/infrastructure/services.py`)
Implements `JWTTokenAdapterInterface`.
- Handles the creation of `access` and `refresh` JWT tokens.
- Provides functionality to check access token expiry and extract token claims.

### 🔗 `SocialAuthenticationAdapter` (`apps/authentication/infrastructure/services.py`)
Implements `SocialAuthenticationAdapterInterface`.
- Integrates with `python-social-auth`'s `do_auth` function to initiate social authentication flows.
- Passes user type information to the social authentication pipeline.

### 🗄️ **Repository Layer Architecture**

Repositories are part of the Infrastructure Layer and implement the repository interfaces (ports) defined in the Domain Layer. They abstract data persistence details.

### 👥 `DjangoUserRepository` (`apps/authentication/infrastructure/repositories.py`)
Implements `UserRepositoryInterface`.
- Provides methods for creating, updating, and retrieving `User` domain models, mapping them to Django ORM `User` instances.
- Contains the `get_or_create_social` method which integrates with the `python-social-auth` pipeline for social user management.

### 🚫 `DjangoBlackListedTokenRepository` (`apps/authentication/infrastructure/repositories.py`)
Implements `BlackListedTokenRepositoryInterface`.
- Handles adding and retrieving `BlackListedToken` domain models, mapping them to Django ORM `BlackListedToken` instances.

---

## 🌐 API Endpoint Specifications

This section details the primary API endpoints for authentication, including HTTP methods, URLs, and a brief description of their functionality. For full request/response schemas, refer to the auto-generated OpenAPI documentation available via `drf-spectacular` (typically at `/api/schema/` or `/api/docs/swagger/`).

### User Management Endpoints

*   **`POST /api/v1/authentication/register/`**
    *   **Description:** Registers a new user with the system. Requires email, password, user type, first name, and last name. Triggers an email verification flow.
    *   **Authentication:** None (AllowAny)
    *   **Throttling:** Anonymous rate throttle applies.

*   **`POST /api/v1/authentication/login/`**
    *   **Description:** Authenticates an existing user with their email and password. Returns JWT access and refresh tokens upon successful login.
    *   **Authentication:** None (AllowAny)
    *   **Throttling:** Anonymous rate throttle applies.

*   **`POST /api/v1/authentication/logout/`**
    *   **Description:** Invalidates the provided JWT access token by blacklisting it, effectively logging out the user.
    *   **Authentication:** JWT (IsAuthenticated)
    *   **Throttling:** User rate throttle applies.

### Email Verification Endpoints

*   **`POST /api/v1/authentication/verify-email/request/`**
    *   **Description:** Requests a new email verification link to be sent to the provided email address.
    *   **Authentication:** None (AllowAny)
    *   **Throttling:** Anonymous rate throttle applies.

*   **`POST /api/v1/authentication/verify-email/<str:user_uuid>/<str:verification_token>/`**
    *   **Description:** Verifies a user's email address using the UUID and verification token received via email.
    *   **Authentication:** None (AllowAny)
    *   **Throttling:** Anonymous rate throttle applies.

### Social Authentication Endpoints

*   **`GET /api/v1/authentication/social/begin/<backend>/`**
    *   **Description:** Initiates the social authentication process for a specified backend (e.g., `google-oauth2`). Redirects the user to the social provider's authentication page.
    *   **Query Parameters:**
        *   `user_type` (optional): Specifies the desired user type (e.g., `AGENT`, `CLIENT`) for new registrations via social login.
    *   **Authentication:** None (AllowAny)
    *   **Throttling:** Anonymous rate throttle applies.

*   **`GET /api/v1/authentication/social/complete/<backend>/`**
    *   **Description:** Handles the callback from the social authentication provider. Completes the social login/registration and issues JWT tokens.
    *   **Authentication:** None (AllowAny)
    *   **Throttling:** Anonymous rate throttle applies.

---

## 🔒 Security Measures and Validation

### 🎯 **Password Validation**
- Enforced through `DjangoPasswordServiceAdapter`, including checks for length, uppercase, lowercase, digits, and special characters.

### 🛡️ **JWT Security**
- **Stateless Tokens**: Reduces server load and simplifies scaling.
- **Token Blacklisting**: Prevents reuse of invalidated access tokens.
- **Configurable Lifetimes**: Access and refresh token validity periods are configurable (`settings.SIMPLE_JWT`).

### 📧 **Email Verification**
- **Token-based verification** with cache-based, time-limited tokens to prevent brute-force attacks and ensure email ownership.
- **Unique links** per user for verification.

### ⚙️ **Rate Limiting**
- Implemented using DRF's `AnonRateThrottle` and `UserRateThrottle` to prevent abuse of API endpoints (e.g., registration, login).

### ❌ **Error Handling Security**
- **Generic error messages** for internal server errors (`HTTP 500`) to avoid leaking sensitive system information.
- Specific, actionable error messages for `4xx` client errors.

---

## ❌ Error Handling Framework

The project implements a centralized and robust exception handling mechanism via the `hp_exception_handler` function (configured as `REST_FRAMEWORK`'s `EXCEPTION_HANDLER` in `settings.py`). This handler ensures consistent API error responses and appropriate logging.

### 🎯 **Key Principles**
- **Standardized Response Format**: All error responses adhere to a consistent JSON structure (e.g., `{"success": False, "message": "...", "error": {"detail": "..."}, "status_code": ...}`).
- **Specific Client Errors (4xx)**: Anticipated errors (e.g., validation failures, business rule violations, conflicts) are mapped to appropriate `4xx` HTTP status codes with informative messages for the user.
  - `ValidationError` (DRF): Handled for serializer validation issues.
  - `IntegrityError` (Django ORM): Converted to `ConflictError` (`HTTP 409`) for database constraint violations.
  - `ParseError` (DRF): Converted to `UnprocessableEntityError` (`HTTP 422`) for malformed request bodies.
  - `BusinessRuleException` (Custom): Converted to `BadRequestError` (`HTTP 400`) for application-level business logic failures.
- **Generic Server Errors (5xx)**: Unexpected Python or Django exceptions are caught and transformed into a generic `HTTP 500 Internal Server Error` response for the user, preventing sensitive internal details from being exposed.
  - Explicitly handles `TypeError`, `AttributeError`, `KeyError`, and `IndexError`.
  - Catches any other unexpected `Exception` that isn't a known `APIException`.
- **Detailed Logging**: All unexpected server-side errors are logged with full tracebacks at an `ERROR` level, providing comprehensive details for developers to debug and resolve issues.
- **Security-Aware Messages**: Sensitive internal information is suppressed from user-facing error messages.

## ⚙️ Configuration and Settings

### 🎯 **Overview**
The project uses `django-environ` for managing environment variables and provides modular settings files for different deployment environments. Authentication-specific configurations are primarily managed in `config/settings/base.py`, with environment-specific overrides in `development.py` and `production.py`.

### 📋 **Key Settings and Environment Variables**

The following settings and environment variables are crucial for the authentication module's operation:

*   **Django Core Settings:**
    *   `SECRET_KEY`: A highly sensitive, randomly generated key. **Essential for security.**
    *   `DEBUG`: Controls debugging mode. Should be `False` in production.
    *   `ALLOWED_HOSTS`: List of host/domain names that this Django site can serve.
    *   `INSTALLED_APPS`: Includes `oauth2_provider`, `social_django`, `drf_social_oauth2`, `apps.authentication`, and `apps.users` for their respective functionalities.
    *   `MIDDLEWARE`: `apps.authentication.infrastructure.middleware.TokenBlackListMiddleware` is registered to enforce JWT token blacklisting.
    *   `AUTH_USER_MODEL`: Set to `users.User`, indicating the custom user model.
    *   `AUTHENTICATION_BACKENDS`: Configured to include `django.contrib.auth.backends.ModelBackend` for email/password authentication and `social_core.backends.google.GoogleOAuth2` for Google social login.

*   **Email Configuration:**
    *   `DEFAULT_FROM_EMAIL`: The default sender email address for outgoing emails (e.g., verification emails).
    *   `EMAIL_BACKEND`: Specifies the email backend to use (e.g., console for development, SMTP for production).
    *   `FROM_DOMAIN`: The base URL of your API, used to construct absolute verification links in emails.
    *   `DJANGO_VERIFICATION_TOKEN_EXPIRY`: An integer representing the expiry time in minutes for email verification tokens.

*   **Caching Configuration:**
    *   `DJANGO_CACHE_TIMEOUT`: The default timeout in seconds for cache entries (used for email verification tokens).
    *   `CACHES`: Defines the cache backends. Default uses `LocMemCache` for development, but can be configured for Redis (`django-redis`) in production.

*   **Django REST Framework (DRF) Settings:**
    *   `DEFAULT_AUTHENTICATION_CLASSES`: Set to `rest_framework_simplejwt.authentication.JWTAuthentication` for token-based authentication.
    *   `DEFAULT_THROTTLE_CLASSES` & `DEFAULT_THROTTLE_RATES`: Configures rate limiting for anonymous and authenticated users to prevent abuse.
    *   `EXCEPTION_HANDLER`: Points to `core.infrastructure.exceptions.hp_exception_handler` for standardized error responses.

*   **DRF Spectacular (OpenAPI) Settings:**
    *   `SPECTACULAR_SETTINGS`: Configures the API documentation generation, including title, description, version, and UI settings.

*   **Simple JWT Settings (`SIMPLE_JWT`):**
    *   `ACCESS_TOKEN_LIFETIME`: Defines the validity period for access tokens (e.g., `timedelta(minutes=30)`).
    *   `REFRESH_TOKEN_LIFETIME`: Defines the validity period for refresh tokens (e.g., `timedelta(hours=24)`).
    *   `ROTATE_REFRESH_TOKENS`: `True` enables rotation of refresh tokens upon renewal.
    *   `BLACKLIST_AFTER_ROTATION`: `True` ensures old refresh tokens are blacklisted after new ones are issued.
    *   `ALGORITHM`, `SIGNING_KEY`, `AUTH_HEADER_TYPES`, `USER_ID_FIELD`, `USER_ID_CLAIM`, `AUTH_TOKEN_CLASSES`: Standard JWT configurations.

*   **Social Authentication Settings (Python Social Auth):**
    *   `SOCIAL_AUTH_USER_MODEL`: Specifies the Django user model to be used with social authentication (`users.User`).
    *   `SOCIAL_AUTH_JSONFIELD_ENABLED`: Enables JSONField for storing extra data from social providers.
    *   `SOCIAL_AUTH_REDIRECT_IS_HTTPS`: Ensures redirects for social authentication are over HTTPS.
    *   `SOCIAL_AUTH_PIPELINE`: Defines the sequence of steps for processing social authentication, including custom steps like `apps.authentication.infrastructure.pipelines.create_user` for user creation/linking.
    *   `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY`, `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET`: Your Google OAuth2 client ID and secret. **These must be set as environment variables in production.**

---