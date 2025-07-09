from apps.authentication.application.ports import BlackListedTokenRepositoryInterface
from apps.authentication.domain.models import BlackListedToken as DomainBlackListedToken
from apps.authentication.infrastructure.models import BlackListedToken


class DjangoBlackListedTokenRepository(BlackListedTokenRepositoryInterface):
    def add(self, blacklisted_token: DomainBlackListedToken) -> DomainBlackListedToken:
        django_token = BlackListedToken.objects.create(
            access=blacklisted_token.access,
            user_id=blacklisted_token.user_id,
            expires_at=blacklisted_token.expires_at,
        )
        return self._to_domain_token(django_token)

    def exists(self, jti: str) -> bool:
        return BlackListedToken.is_blacklisted(access_token=jti)

    def _to_domain_token(
        self, django_token: BlackListedToken
    ) -> DomainBlackListedToken:
        return DomainBlackListedToken(
            id=django_token.id,
            access=django_token.access,
            user_id=django_token.user_id,
            expires_at=django_token.expires_at,
            created_at=django_token.created_at,
        )
