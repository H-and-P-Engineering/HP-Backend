from unittest.mock import Mock, patch

import pytest
from django.test import TestCase
from rest_framework_simplejwt.exceptions import InvalidToken

from apps.authentication.infrastructure.services import (
    DjangoJWTTokenAdapter,
    DjangoPasswordServiceAdapter,
)


class TestAuthenticationSecurity(TestCase):
    def setUp(self):
        self.password_service = DjangoPasswordServiceAdapter()
        self.jwt_service = DjangoJWTTokenAdapter()

    def test_password_hashing_security(self):
        """Test that passwords are properly hashed"""
        passwords = [
            "simple_password",
            "Complex!Password123",
            "超複雜密碼",  # Unicode password
            "pass" * 50,  # Long password
        ]

        for password in passwords:
            hashed = self.password_service.hash(password)

            # Hash should be different from original
            assert hashed != password

            # Hash should be non-empty
            assert len(hashed) > 0

            # Should be able to verify
            assert self.password_service.check(password, hashed) is True

            # Wrong password should fail
            assert self.password_service.check(password + "wrong", hashed) is False

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes (salt)"""
        password = "TestPassword123!"

        hash1 = self.password_service.hash(password)
        hash2 = self.password_service.hash(password)

        # Same password should produce different hashes due to salt
        assert hash1 != hash2

        # Both should verify correctly
        assert self.password_service.check(password, hash1) is True
        assert self.password_service.check(password, hash2) is True

    def test_jwt_token_security(self):
        """Test JWT token security"""
        from apps.users.infrastructure.models import User

        user = User.objects.create_user(email="test@example.com", password="testpass")

        tokens = self.jwt_service.create_tokens(user)

        # Should have both access and refresh tokens
        assert "access" in tokens
        assert "refresh" in tokens

        # Tokens should be non-empty strings
        assert isinstance(tokens["access"], str)
        assert isinstance(tokens["refresh"], str)
        assert len(tokens["access"]) > 0
        assert len(tokens["refresh"]) > 0

        # Tokens should be different
        assert tokens["access"] != tokens["refresh"]

    def test_jwt_token_expiry_validation(self):
        """Test JWT token expiry validation"""
        from rest_framework.exceptions import ValidationError

        from apps.users.infrastructure.models import User

        user = User.objects.create_user(email="test@example.com", password="testpass")

        tokens = self.jwt_service.create_tokens(user)
        access_token = tokens["access"]

        # Valid token should return future expiry time
        expiry = self.jwt_service.check_access_token_expiry(access_token)

        from datetime import UTC, datetime

        now = datetime.now(tz=UTC)
        assert expiry > now

    def test_invalid_jwt_token_handling(self):
        """Test handling of invalid JWT tokens"""
        from rest_framework.exceptions import ValidationError

        invalid_tokens = [
            "invalid.token.here",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
            "",
            "not.a.jwt",
            "too.many.parts.in.token.here",
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises(ValidationError, match="Access token is invalid"):
                self.jwt_service.check_access_token_expiry(invalid_token)

    def test_timing_attack_resistance(self):
        """Test that password checking has consistent timing"""
        import time

        # Create a known hash
        known_password = "CorrectPassword123!"
        known_hash = self.password_service.hash(known_password)

        # Time correct password check
        start = time.time()
        result1 = self.password_service.check(known_password, known_hash)
        time1 = time.time() - start

        # Time incorrect password check
        start = time.time()
        result2 = self.password_service.check("WrongPassword123!", known_hash)
        time2 = time.time() - start

        assert result1 is True
        assert result2 is False

        # Time difference should be minimal (< 10ms difference)
        # This is a basic check; real timing attack resistance requires more sophisticated testing
        time_diff = abs(time1 - time2)
        assert time_diff < 0.01, f"Timing difference too large: {time_diff:.4f}s"
