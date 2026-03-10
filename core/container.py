from typing import Any, Dict, Type, TypeVar
from users.repositories import UserRepository, BlackListedTokenRepository
from business.repositories import BusinessProfileRepository, BusinessVerificationRepository
from core.services import EmailService, VerificationService

T = TypeVar("T")


class DependencyContainer:
    _instances: Dict[str, Any] = {}

    @classmethod
    def get(cls, key: str, factory: Type[T] = None, **kwargs) -> T:
        if key not in cls._instances:
            if factory is None:
                raise ValueError(f"No instance or factory provided for {key}")
            cls._instances[key] = factory(**kwargs)
        return cls._instances[key]

    # Repositories
    @classmethod
    def user_repository(cls):
        return cls.get("user_repository", UserRepository)

    @classmethod
    def blacklisted_token_repository(cls):
        return cls.get("blacklisted_token_repository", BlackListedTokenRepository)

    @classmethod
    def business_profile_repository(cls):
        return cls.get("business_profile_repository", BusinessProfileRepository)

    @classmethod
    def business_verification_repository(cls):
        return cls.get(
            "business_verification_repository", BusinessVerificationRepository
        )

    # Services
    @classmethod
    def email_service(cls):
        return cls.get("email_service", EmailService)

    @classmethod
    def verification_service(cls):
        return cls.get("verification_service", VerificationService)

    @classmethod
    def social_cache_service(cls):
        from users.services import SocialCacheService

        return cls.get("social_cache_service", SocialCacheService)

    @classmethod
    def active_token_cache_service(cls):
        from users.services import ActiveTokenCacheService

        return cls.get("active_token_cache_service", ActiveTokenCacheService)

    @classmethod
    def user_service(cls):
        from users.services import UserService

        return cls.get(
            "user_service",
            UserService,
            repository=cls.user_repository(),
            email_service=cls.email_service(),
        )

    @classmethod
    def social_auth_service(cls):
        from users.services import SocialAuthService

        return cls.get("social_auth_service", SocialAuthService)

    @classmethod
    def authentication_service(cls):
        from users.services import AuthenticationService

        return cls.get(
            "authentication_service",
            AuthenticationService,
            user_service=cls.user_service(),
            social_auth_service=cls.social_auth_service(),
            blacklisted_token_repo=cls.blacklisted_token_repository(),
            active_token_cache=cls.active_token_cache_service(),
        )

    @classmethod
    def geocoding_service(cls):
        from location.services import GeocodingService

        return cls.get("geocoding_service", GeocodingService)

    @classmethod
    def travel_service(cls):
        from location.services import TravelService

        return cls.get(
            "travel_service", TravelService, geocoding_service=cls.geocoding_service()
        )

    @classmethod
    def business_profile_service(cls):
        from business.services import BusinessProfileService

        return cls.get(
            "business_profile_service",
            BusinessProfileService,
            repository=cls.business_profile_repository(),
        )

    @classmethod
    def business_verification_service(cls):
        from business.services import BusinessVerificationService

        return cls.get(
            "business_verification_service",
            BusinessVerificationService,
            repository=cls.business_verification_repository(),
            profile_repo=cls.business_profile_repository(),
            user_repo=cls.user_repository(),
            email_service=cls.email_service(),
        )

    @classmethod
    def location_intelligence_service(cls):
        from location.services import LocationIntelligenceService

        return cls.get(
            "location_intelligence_service",
            LocationIntelligenceService,
            geocoding_service=cls.geocoding_service(),
        )


# Global access point
container = DependencyContainer()
