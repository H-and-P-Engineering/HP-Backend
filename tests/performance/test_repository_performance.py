import time

import pytest
from django.test import TestCase

from apps.users.infrastructure.models import User
from apps.users.infrastructure.repositories import DjangoUserRepository


@pytest.mark.django_db
class TestRepositoryPerformance(TestCase):
    def setUp(self):
        self.repository = DjangoUserRepository()

    def test_bulk_user_creation_performance(self):
        """Test performance of creating multiple users"""
        start_time = time.time()

        # Create 20000 users
        users = []
        for i in range(20000):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="testpass",
                first_name=f"User{i}",
                last_name="Test",
            )
            users.append(user)

        end_time = time.time()
        creation_time = end_time - start_time

        # Should create 20000 users in reasonable time (< 5 seconds)
        assert creation_time < 5.0, (
            f"Creating 10000 users took {creation_time:.2f} seconds"
        )
        assert len(users) == 20000

    def test_user_lookup_performance(self):
        """Test performance of user lookups"""
        # Create test users
        users = []
        for i in range(20000):
            user = User.objects.create_user(
                email=f"lookup{i}@example.com", password="testpass"
            )
            users.append(user)

        # Test email lookup performance
        start_time = time.time()

        for user in users:
            found_user = self.repository.get_by_email(user.email)
            assert found_user is not None
            assert found_user.id == user.id

        end_time = time.time()
        lookup_time = end_time - start_time

        # Should lookup 20000 users in reasonable time (< 2 seconds)
        assert lookup_time < 5.0, (
            f"Looking up 20000 users took {lookup_time:.2f} seconds"
        )

    def test_user_id_lookup_performance(self):
        """Test performance of user ID lookups"""
        # Create test users
        user_ids = []
        for i in range(5000):
            user = User.objects.create_user(
                email=f"idlookup{i}@example.com", password="testpass"
            )
            user_ids.append(user.id)

        # Test ID lookup performance
        start_time = time.time()

        for user_id in user_ids:
            found_user = self.repository.get_by_id(user_id)
            assert found_user is not None
            assert found_user.id == user_id

        end_time = time.time()
        lookup_time = end_time - start_time

        # Should lookup 5000 users by ID in reasonable time (< 1 second)
        assert lookup_time < 1.0, (
            f"Looking up 5000 users by ID took {lookup_time:.2f} seconds"
        )
