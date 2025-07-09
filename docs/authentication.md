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

The **Housing & Properties** authentication system implements a sophisticated **multi-layered architecture** that separates concerns across distinct components, adhering to **Clean Architecture** principles. The system leverages `Django REST Framework` for API development, `djangorestframework-simplejwt` for JWT token management, and `python-social-auth` with `drf-social-oauth2` for social authentication integration.

### 🎯 **Architectural Principles**

The architecture follows a clear separation pattern where:

- 📋 **Presentation Layer** (`apps/authentication/presentation/`):
  - **Views** handle HTTP concerns using function-based views with `@api_view` decorators
  - **Serializers** manage data validation and transformation for API input/output
  - **URL routing** organized in `api/v1/authentication.py` for versioned endpoints

- 🌐 **Application Layer** (`apps/authentication/application/`):
  - **Rules** (Use Cases) encapsulate core business logic and orchestration:
    - `RegisterUserRule` - handles user registration with email verification
    - `LoginUserRule` - manages user authentication and token generation
    - `LogoutUserRule` - handles token blacklisting for secure logout
    - `VerifyEmailRule` - processes email verification flow
    - `UpdateUserTypeRule` - manages user type updates
    - `SocialAuthenticationRule` - handles social login flows
  - **Ports** define interfaces for external concerns (e.g., `UserRepositoryInterface`, `EmailServiceAdapterInterface`)

- 🗄️ **Domain Layer**:
  - **User Domain** (`apps/users/domain/`):
    - `User` dataclass with business attributes (email, password_hash, user_type, etc.)
    - `UserType` enum with values: CLIENT, AGENT, VENDOR, SERVICE_PROVIDER, ADMIN
    - `UserEvent` base class for domain events
  - **Authentication Domain** (`apps/authentication/domain/`):
    - `BlackListedToken` dataclass for JWT token blacklisting
    - Domain events: `UserVerificationEmailEvent`, `UserEmailVerifiedEvent`, `UserUpdateEvent`, `UserLogoutEvent`

- 🛠️ **Infrastructure Layer** (`apps/authentication/infrastructure/`):
  - **Adapters** provide concrete implementations:
    - `DjangoPasswordServiceAdapter` - password hashing and validation
    - `DjangoEmailServiceAdapter` - templated email sending
    - `DjangoCacheServiceAdapter` - Redis/cache operations
    - `DjangoJWTTokenAdapter` - JWT token creation and validation
    - `SocialAuthenticationAdapter` - social auth integration
    - `DjangoEventPublisherAdapter` - async event publishing with Celery
  - **Repositories** handle data persistence:
    - `DjangoUserRepository` - user CRUD operations with domain model mapping
    - `DjangoBlackListedTokenRepository` - token blacklist management
  - **Django Models**:
    - Custom `User` model extending `AbstractUser` with UUID7, email authentication
    - `BlackListedToken` model for JWT invalidation
  - **Factory** (`factory.py`) - dependency injection setup and event handler registration

### 🎭 **Event-Driven Architecture**

The system implements an event-driven pattern using:

- **Domain Events**: Pure domain objects representing business events
- **Event Bus**: Central event dispatching mechanism (`core/application/event_bus.py`)
- **Event Handlers**: Async handlers for side effects (email sending, cache updates)
- **Event Publisher**: Celery-based async event processing

This layered design ensures **maintainability**, **testability**, and **scalability** while adhering to **SOLID** principles.

---

## 📧 Email-Based Authentication Flow

### 📝 Registration Process

The email-based registration flow begins when a client sends a `POST` request to `/api/v1/authentication/register/`. The `register_user` view processes this request through a **carefully orchestrated sequence** of operations.

#### 🔍 **Request Validation**
The `UserRegistrationSerializer` validates incoming data with **strict validation rules**:

```python
class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
```

#### 🛡️ **Advanced Password Validation**
The serializer implements comprehensive password security checks:

**Password Requirements (enforced via regex):**
- 🚫 **No spaces allowed** - prevents copy-paste errors
- 🔤 **One uppercase letter** - enhances complexity
- 🔡 **One lowercase letter** - ensures mixed case
- 🔢 **One digit** - numerical requirement
- 🔣 **One special character** - symbol inclusion (`!@#$%^&*(),.?"'{}|<>`)

#### 👤 **User Creation Flow**
The `RegisterUserRule` orchestrates the registration process:

1. **Password Hashing**: Uses `DjangoPasswordServiceAdapter.hash()` with Django's secure password hashing
2. **Domain User Creation**: Creates a `User` domain model with validated data
3. **Repository Persistence**: `DjangoUserRepository.create()` saves to database
4. **Event Publishing**: Triggers `UserVerificationEmailEvent` for async email sending

```python
def execute(self, email: str, password: str, first_name: str, last_name: str) -> DomainUser:
    password_hash = self._password_service.hash(password)
    
    user = DomainUser(
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
    )
    
    created_user = self._user_repository.create(user)
    self._event_publisher.publish(UserVerificationEmailEvent(created_user.id))
    
    return created_user
```

#### 🎫 **JWT Token Generation**
After successful user creation, the system generates JWT tokens via `DjangoJWTTokenAdapter`:
- **Access Token**: 30-minute lifetime for API requests
- **Refresh Token**: 24-hour lifetime for token renewal
- **Token Rotation**: Enabled for enhanced security

#### 📬 **Email Verification Setup**
The email verification process is handled asynchronously:

1. **Event Handler**: `send_verification_email_event` processes the `UserVerificationEmailEvent`
2. **Token Generation**: `DjangoVerificationServiceAdapter.generate_token()` creates secure 32-byte token
3. **Cache Storage**: Token stored in Redis with key pattern `email_verify_{user_uuid}`
4. **Link Generation**: Full verification URL constructed with `FROM_DOMAIN` setting
5. **Email Dispatch**: HTML template email sent via `DjangoEmailServiceAdapter`

**Cache Configuration:**
- **Expiration**: 15 minutes (configurable via `DJANGO_VERIFICATION_TOKEN_EXPIRY`)
- **Backend**: Redis for production, local memory for development
- **Auto-cleanup**: Expired tokens automatically removed

---

### 🔐 Login Process

The login flow authenticates existing users through `/api/v1/authentication/login/` endpoint.

#### 🎯 **Authentication Flow**
The `LoginUserRule` performs sequential security checks:

```python
def execute(self, email: str, password: str) -> DomainUser:
    user = self._user_repository.get_by_email(email)
    
    if not user or not self._password_service.check(password, user.password_hash):
        raise BusinessRuleException("Login failed. Provided email or password is invalid.")
    
    if not user.is_active:
        raise BusinessRuleException("Login failed. Requested user account is deactivated.")
    
    if not user.is_email_verified:
        raise BusinessRuleException("Login failed. Requested user email is not verified.")
    
    # Update last login timestamp
    self._event_publisher.publish(
        UserUpdateEvent(update_fields={"last_login": datetime.now(tz=UTC)}, user_id=user.id)
    )
    
    return user
```

**Security Features:**
- 🚫 **Generic error messages** prevent username enumeration attacks
- 🔒 **Account status validation** ensures only active users can login
- ✉️ **Email verification enforcement** blocks unverified accounts
- 📊 **Audit logging** tracks login attempts and timestamps

---

### ✉️ Email Verification Mechanism

The email verification system implements a **secure token-based approach** with cache storage.

#### 🔐 **Token Generation & Storage**
When verification is requested, the `RequestEmailVerificationRule`:

1. **Validates User**: Ensures user exists and isn't already verified
2. **Cache Check**: Prevents spam by checking for existing verified status
3. **Token Generation**: Creates cryptographically secure token using `secrets.token_urlsafe(32)`
4. **Cache Storage**: Stores `(user_id, token)` tuple with user UUID as key
5. **Event Publishing**: Triggers async email sending

#### ✅ **Verification Process**
The `VerifyEmailRule` handles verification via `/api/v1/authentication/verify-email/{user_uuid}/{verification_token}/`:

1. **Cache Retrieval**: Fetches stored token data using user UUID
2. **Token Validation**: Compares provided token with cached value
3. **User Verification**: Cross-validates user ID and UUID
4. **Account Activation**: Publishes `UserEmailVerifiedEvent` for processing
5. **Cache Cleanup**: Removes verification token to prevent reuse

**Event-Driven Side Effects:**
- `cache_email_verification_status`: Caches verified status
- `update_user_verification_status`: Updates database `is_email_verified` flag

---

## 🚪 Logout Implementation

### 🎯 **JWT Token Blacklisting**

Due to JWT's stateless nature, the system implements token blacklisting for secure logout via `/api/v1/authentication/logout/`.

#### 🔄 **Logout Process Flow**

1. **Request Validation**: `UserLogoutSerializer` extracts and validates access token
2. **Token Processing**: `LogoutUserRule` validates token expiry and creates blacklist entry
3. **Database Storage**: `DjangoBlackListedTokenRepository` persists blacklisted token
4. **Event Publishing**: `UserLogoutEvent` triggers async blacklisting

```python
def execute(self, user_id: int, access_token: str) -> None:
    token_expiry = self._jwt_token_service.check_access_token_expiry(access_token)
    
    token = BlackListedToken(
        access=access_token,
        user_id=user_id,
        expires_at=token_expiry
    )
    
    self._event_publisher.publish(UserLogoutEvent(token=token, user_id=user_id))
```

#### 🛡️ **TokenBlackListMiddleware**

Middleware intercepts requests to check token blacklist status:

```python
def process_request(self, request: Request) -> None:
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ")[1]
        
        if self.blacklisted_token_repository.exists(access_token):
            request.META["HTTP_AUTHORIZATION"] = ""
            logger.warning(f"Blacklisted token attempted to access {request.path}")
```

#### 🗄️ **BlackListedToken Model**

```python
class BlackListedToken(models.Model):
    access = models.TextField(unique=True)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def is_blacklisted(cls, access_token: str) -> bool:
        return cls.objects.filter(access=access_token).exists()
```

---

## 🔗 Social Authentication Implementation

The social authentication system integrates with `python-social-auth` for third-party provider support, enabling users to register and login using OAuth providers like Google.

### 🚀 **Social Authentication Flow**

The social authentication process involves two main steps with comprehensive user type handling:

#### 1. **Initiating Social Login** (`/api/v1/authentication/social/begin/<backend>/`)

```python
@csrf.csrf_exempt
@cache.never_cache
@psa("authentication:social-complete")
@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def begin_social_authentication(request: Request, backend_name: str) -> Any:
    user_type = request.query_params.get("user_type", "CLIENT")
    
    social_authentication_rule = get_social_authentication_rule()
    return social_authentication_rule.begin_authentication(request=request)
```

**Flow Details:**
- 🌐 **Client Request**: A client initiates social login by making a `GET` request to this endpoint, specifying the social `backend` (e.g., `google-oauth2`)
- 👤 **User Type Selection**: An optional `user_type` query parameter can be provided (e.g., `?user_type=AGENT`) to pre-select the user's role during registration
- 🔄 **Provider Redirect**: The `begin_social_authentication` view redirects the user to the social provider's authentication page
- 💾 **Session Storage**: The `user_type` is stored in the session to be used during the completion phase
- 🔒 **Security**: CSRF exempt and cache-disabled for OAuth flow compatibility

#### 2. **Completing Social Login** (`/api/v1/authentication/social/complete/<backend>/`)

```python
@csrf.csrf_exempt
@cache.never_cache
@psa("authentication:social-complete")
@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def complete_social_authentication(request: Request, backend_name: str) -> Response:
    social_authentication_rule = get_social_authentication_rule()
    user_dict = social_authentication_rule.complete_authentication(request)
    
    user = user_dict["user"]
    jwt_token_service = get_jwt_token_service()
    tokens = jwt_token_service.create_tokens(user)
    response_serializer = JWTTokenSerializer(dict(user=user, **tokens))
    
    is_new_user = user_dict["is_new_user"]
    
    if is_new_user:
        return StandardResponse.created(
            data=response_serializer.data,
            message="Registration successful. Welcome to Housing & Properties!",
        )
    else:
        return StandardResponse.success(
            data=response_serializer.data,
            message="Login successful. Welcome back!",
        )
```

**Completion Flow:**
- 🔄 **Provider Callback**: After successful authentication with the social provider, the user is redirected back to this endpoint
- 🎭 **User Resolution**: The `complete_social_authentication` view handles the callback from the social provider
- 🏗️ **User Creation/Retrieval**: Uses the `SocialAuthenticationRule` to either retrieve an existing user or create a new user account based on the social provider's information and the `user_type` from the session
- 🎫 **Token Generation**: Upon successful completion, JWT tokens are generated for the user
- ✅ **Response Differentiation**: Returns different success messages based on whether the user is new (registration) or existing (login)

#### 📋 **Social Authentication Pipeline**

Custom pipeline in `apps/authentication/infrastructure/pipelines.py`:

```python
def create_user(backend, details: Dict[str, Any], user: Any = None, *args, **kwargs) -> Dict[str, Any]:
    if user:
        # Existing user - update last login
        event_publisher.publish(UserUpdateEvent(
            update_fields={"last_login": datetime.now(tz=UTC)},
            user_id=user.id,
        ))
        return {"user": user, "is_new": False}
    
    # New user creation
    domain_user = DomainUser(
        email=fields["email"],
        first_name=fields.get("first_name", ""),
        last_name=fields.get("last_name", ""),
        is_email_verified=True,  # Social users are pre-verified
    )
    
    created_user = user_repository.create_social(domain_user)
    return {"user": created_user, "is_new": True}
```

**Pipeline Configuration:**
```python
SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'apps.authentication.infrastructure.pipelines.create_user',  # Custom step
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.user.user_details',
]
```

---

## 🎫 Token Management System

### 🎯 **JWT Configuration**

The system uses `djangorestframework-simplejwt` with the following configuration:

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

### 🔑 **Token Creation Process**

The `DjangoJWTTokenAdapter` handles token generation:

```python
def create_tokens(self, user) -> dict:
    refresh = RefreshToken.for_user(user)
    tokens = {
        "refresh": str(refresh),
        "access": str(refresh.access_token)
    }
    return tokens
```

### 🚫 **Token Blacklisting Architecture**

- **Middleware Integration**: `TokenBlackListMiddleware` checks every request
- **Database Storage**: Blacklisted tokens stored with expiry information
- **Event-Driven**: Async blacklisting via `UserLogoutEvent`
- **Automatic Cleanup**: Expired blacklisted tokens can be cleaned up periodically

---

## 🗄️ Data Model Implementation

### 👤 **User Domain Model**

```python
@dataclass(frozen=True)
class User:
    email: str
    password_hash: str | None = field(default=None, repr=False)
    first_name: str = ""
    last_name: str = ""
    user_type: UserType = UserType.CLIENT
    is_email_verified: bool = False
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    is_new: bool = False
    id: int | None = None
    uuid: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login: datetime | None = None
```

### 🏷️ **UserType Enum**

```python
class UserType(Enum):
    CLIENT = "CLIENT"
    AGENT = "AGENT"
    VENDOR = "VENDOR"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    ADMIN = "ADMIN"
    
    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(member.value, member.name) for member in cls]
```

### 🗄️ **Django User Model**

```python
class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid6.uuid7, editable=False)
    username = None  # Removed username field
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=16, choices=DomainUserType.choices, default=DomainUserType.CLIENT)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    objects = UserManager()
```

**Key Features:**
- **UUID7**: Time-ordered UUIDs for better database performance
- **Email Authentication**: No username required, email is the primary identifier
- **User Types**: Support for different platform roles
- **Audit Fields**: Automatic timestamp tracking

### 🚫 **BlackListedToken Models**

**Domain Model:**
```python
@dataclass(frozen=True)
class BlackListedToken:
    access: str
    user_id: int
    expires_at: datetime
    id: int | None = None
    created_at: datetime | None = None
```

**Django Model:**
```python
class BlackListedToken(models.Model):
    access = models.TextField(unique=True)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="blacklisted_tokens")
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "auth_blacklisted_tokens"
        indexes = [
            models.Index(fields=["access"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["user", "expires_at"]),
        ]
```

---

## ⚙️ Service Layer Architecture

### 🔧 **Infrastructure Adapters**

#### **Password Service**
```python
class DjangoPasswordServiceAdapter(PasswordServiceAdapterInterface):
    def hash(self, password: str) -> str:
        return make_password(password)
    
    def check(self, raw_password: str, hashed_password: str) -> bool:
        return check_password(raw_password, hashed_password)
```

#### **Cache Service**
```python
class DjangoCacheServiceAdapter(CacheServiceAdapterInterface):
    def get(self, key: str) -> Any:
        return cache.get(key, None)
    
    def set(self, key: str, value: Any, timeout: int | None = None) -> None:
        timeout = timeout or settings.DJANGO_CACHE_TIMEOUT
        cache.set(key, value, timeout)
```

#### **Email Service**
```python
class DjangoEmailServiceAdapter(EmailServiceAdapterInterface):
    def send_verification_email(self, recipient_email: str, verification_link: str) -> None:
        context = {
            "email": recipient_email,
            "verification_link": verification_link,
            "expiry_minutes": settings.DJANGO_VERIFICATION_TOKEN_EXPIRY,
        }
        self._send_template_email(
            subject="Verify your email address",
            template_name="verify_email",
            context=context,
            recipient_list=[recipient_email],
        )
```

### 🏭 **Factory Pattern for Dependency Injection**

The system uses a factory pattern for dependency management:

```python
# apps/authentication/infrastructure/factory.py
def get_register_user_rule():
    return RegisterUserRule(
        user_repository=get_user_repository(),
        password_service=get_password_service(),
        event_publisher=get_event_publisher(),
    )

def register_authentication_event_handlers():
    user_repository = get_user_repository()
    # ... other dependencies
    
    EventBus.subscribe(
        UserVerificationEmailEvent,
        lambda event: send_verification_email_event(event, user_repository, ...)
    )
```

### 🔄 **Event-Driven Architecture**

#### **Event Bus**
```python
class EventBus:
    _handlers: Dict[Type[DomainEvent], List[Callable[[DomainEvent], None]]] = {}
    
    @classmethod
    def subscribe(cls, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
    
    @classmethod
    def publish(cls, event: DomainEvent) -> None:
        for handler in cls._handlers.get(type(event), []):
            handler(event)
```

#### **Async Event Publisher**
```python
class DjangoEventPublisherAdapter(EventPublisherInterface):
    def publish(self, event: DomainEvent) -> None:
        event_data = pickle.dumps(event)
        _publish_event_to_bus.delay(event_data)  # Celery task

@shared_task
def _publish_event_to_bus(event_data: bytes) -> None:
    event = pickle.loads(event_data)
    EventBus.publish(event)
```

---

## 🌐 API Endpoint Specifications

### 📋 **URL Configuration**

**API Structure:**
```python
# api/v1/__init__.py
urlpatterns = [
    path("authentication/", include("api.v1.authentication")),
]

# api/v1/authentication.py
urlpatterns = [
    path("register/", register_user, name="register"),
    path("update-user-type/", update_user_type, name="update-user-type"),
    path("verify-email/request/", verify_email_request, name="verify-email-request"),
    path("verify-email/<str:user_uuid>/<str:verification_token>/", verify_email, name="verify-email"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path(f"social/begin/<str:backend>{extra}", begin_social_authentication, name="social-begin"),
    path("social/complete/<str:backend>/", complete_social_authentication, name="social-complete"),
]
```

### 🎯 **Endpoint Details**

#### **User Registration**
- **URL**: `POST /api/v1/authentication/register/`
- **Authentication**: None (AllowAny)
- **Throttling**: AnonRateThrottle (5/min)
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
- **Response**: JWT tokens + user info + verification message

#### **User Login**
- **URL**: `POST /api/v1/authentication/login/`
- **Authentication**: None (AllowAny)
- **Throttling**: AnonRateThrottle (5/min)
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123!"
  }
  ```

#### **User Logout**
- **URL**: `POST /api/v1/authentication/logout/`
- **Authentication**: JWT Required (IsAuthenticated)
- **Throttling**: UserRateThrottle (10/min)
- **Request Body**:
  ```json
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

#### **Email Verification Request**
- **URL**: `POST /api/v1/authentication/verify-email/request/`
- **Authentication**: None (AllowAny)
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```

#### **Email Verification**
- **URL**: `POST /api/v1/authentication/verify-email/{user_uuid}/{verification_token}/`
- **Authentication**: None (AllowAny)
- **URL Parameters**: User UUID and verification token from email

#### **User Type Update**
- **URL**: `PUT /api/v1/authentication/update-user-type/`
- **Authentication**: JWT Required
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "user_type": "AGENT"
  }
  ```

### 📊 **Standard Response Format**

All endpoints use the `StandardResponse` pattern:

```python
# Success Response
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "status_code": 200
}

# Error Response
{
  "success": false,
  "message": "Error occurred",
  "error": {
    "detail": "Specific error details"
  },
  "status_code": 400
}
```

---

## 🔒 Security Measures and Validation

### 🛡️ **Password Security**

The `UserRegistrationSerializer` implements comprehensive password validation:

```python
def validate_password(self, value: str) -> str:
    if " " in value:
        raise serializers.ValidationError("Password must not contain spaces.")
    
    if not re.search(r"[A-Z]", value):
        raise serializers.ValidationError("Password must contain at least one uppercase letter.")
    
    if not re.search(r"[a-z]", value):
        raise serializers.ValidationError("Password must contain at least one lowercase letter.")
    
    if not re.search(r"\d", value):
        raise serializers.ValidationError("Password must contain at least one digit.")
    
    if not re.search(r"[!@#$%^&*(),.?\"'{}|<>]", value):
        raise serializers.ValidationError("Password must contain at least one special character.")
    
    return value
```

### 🚫 **Rate Limiting**

Configured in `REST_FRAMEWORK` settings:
- **Anonymous**: 5 requests/minute
- **Authenticated**: 10 requests/minute
- Applied per view using `@throttle_classes` decorator

### 🔐 **JWT Security Features**

- **Token Rotation**: Refresh tokens are rotated on renewal
- **Blacklisting**: Immediate token invalidation on logout
- **Short Lifetimes**: 30-minute access tokens, 24-hour refresh tokens
- **Secure Signing**: HMAC-SHA256 with Django SECRET_KEY

### 📧 **Email Verification Security**

- **Cryptographic Tokens**: 32-byte URL-safe tokens using `secrets` module
- **Time-Limited**: 15-minute expiration with automatic cleanup
- **UUID Validation**: Cross-references user UUID to prevent token misuse
- **Cache-Based**: No database storage of temporary verification data

### 🛡️ **Middleware Protection**

```python
class TokenBlackListMiddleware(MiddlewareMixin):
    def process_request(self, request: Request) -> None:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]
            
            if self.blacklisted_token_repository.exists(access_token):
                request.META["HTTP_AUTHORIZATION"] = ""
                logger.warning(f"Blacklisted token attempted to access {request.path}")
```

---

## ❌ Error Handling Framework

### 🎯 **Centralized Exception Handling**

The `hp_exception_handler` in `core/infrastructure/exceptions/handler.py` provides consistent error responses:

```python
def hp_exception_handler(exc: Exception, context: Dict[str, Any]) -> Response | None:
    # Convert Django/DRF exceptions to standardized format
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
    elif isinstance(exc, IntegrityError):
        logger.exception(f"Unhandled database constraint error: {exc}")
        exc = ConflictError()
    elif isinstance(exc, BusinessRuleException):
        exc = BadRequestError(detail=str(exc))
    
    # Return standardized error response
    response_data = {
        "success": False,
        "message": "An error occurred.",
        "error": {},
        "status_code": None,
    }
    # ... handle specific exception types
```

### 📊 **Business Rule Exceptions**

```python
class BusinessRuleException(Exception):
    """Base exception for business rule violations"""
    pass

# Usage in application rules
if not user or not self._password_service.check(password, user.password_hash):
    raise BusinessRuleException("Login failed. Provided email or password is invalid.")
```

### 🔍 **Error Response Normalization**

The handler normalizes various error types into a consistent format:

```python
def normalize_error_detail(detail: Any) -> str | List[str] | Dict[str, Any]:
    if isinstance(detail, dict):
        normalized = {}
        for key, value in detail.items():
            if hasattr(value, "__iter__") and not isinstance(value, str):
                # Handle field validation errors
                normalized[key] = str(value[0]).replace("This field", key.title()) if len(value) == 1 else [str(v) for v in value]
            else:
                normalized[key] = str(value)
        return normalized
    # ... handle other types
```

---

## ⚙️ Configuration and Settings

### 🎛️ **Modular Settings Architecture**

The project uses environment-based settings:

```python
# config/settings/__init__.py
ENVIRONMENT = env.str("DJANGO_ENVIRONMENT", default="development")

if ENVIRONMENT == "production":
    from config.settings.production import *
elif ENVIRONMENT == "test":
    from config.settings.test import *
else:
    from config.settings.development import *
```

### 🔧 **Core Authentication Settings**

```python
# JWT Configuration
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

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.google.GoogleOAuth2',
]

# Custom User Model
AUTH_USER_MODEL = 'users.User'
```

### 📧 **Email Configuration**

```python
# Email Settings
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="noreply@housingandproperties.com")
EMAIL_BACKEND = env.str("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

# Production Email (when EMAIL_BACKEND is SMTP)
EMAIL_HOST = env.str("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
```

### 💾 **Cache Configuration**

```python
# Redis Cache for Production
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("REDIS_URL", default="redis://localhost:6379/0"),
    }
}

# Cache Timeouts
DJANGO_CACHE_TIMEOUT = env.int("DJANGO_CACHE_TIMEOUT", default=900)  # 15 minutes
DJANGO_VERIFICATION_TOKEN_EXPIRY = env.int("DJANGO_VERIFICATION_TOKEN_EXPIRY", default=15)  # minutes
```

### 🔗 **Social Authentication Setup**

```python
# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_USER_FIELDS = ["email", "first_name", "last_name"]
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ["email", "profile"]

# Social Auth Pipeline
SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'apps.authentication.infrastructure.pipelines.create_user',  # Custom pipeline step
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.user.user_details',
]
```

### ⚡ **Celery Configuration**

```python
# Celery for Async Tasks
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["application/json", "application/x-python-serialize"]
CELERY_TASK_SERIALIZER = "pickle"
CELERY_RESULT_SERIALIZER = "pickle"
```

### 🛡️ **Security Settings**

Production-specific security configurations:

```python
# Production Security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

This documentation reflects the actual implementation of the Housing & Properties authentication system, providing a comprehensive guide to its architecture, features, and configuration.