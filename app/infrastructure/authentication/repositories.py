from app.application.authentication.ports import IBlackListedTokenRepository
from app.domain.authentication.entities import (
    BlackListedToken as DomainBlackListedToken,
)

from .models.tables import BlackListedToken


def to_domain_token(django_token: BlackListedToken) -> DomainBlackListedToken:
    return DomainBlackListedToken(
        id=django_token.id,
        access=django_token.access,
        user_id=django_token.user_id,
        expires_at=django_token.expires_at,
        created_at=django_token.created_at,
    )


class DjangoBlackListedTokenRepository(IBlackListedTokenRepository):
    def create(
        self, blacklisted_token: DomainBlackListedToken
    ) -> DomainBlackListedToken:
        django_token = BlackListedToken.objects.create(
            access=blacklisted_token.access,
            user_id=blacklisted_token.user_id,
            expires_at=blacklisted_token.expires_at,
        )
        return to_domain_token(django_token)

    def check_exists(self, jti: str) -> bool:
        return BlackListedToken.is_blacklisted(access_token=jti)
