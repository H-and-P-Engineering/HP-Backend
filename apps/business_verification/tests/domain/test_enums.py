from apps.business_verification.domain.enums import VerificationStatus


class TestVerificationStatus:
    def test_verification_status_values(self):
        assert VerificationStatus.PENDING == "PENDING"
        assert VerificationStatus.IN_PROGRESS == "IN_PROGRESS"
        assert VerificationStatus.FAILED == "FAILED"
        assert VerificationStatus.SUCCESSFUL == "SUCCESSFUL"

    def test_verification_status_choices(self):
        choices = VerificationStatus.choices()
        expected_choices = [
            ("PENDING", "PENDING"),
            ("IN_PROGRESS", "IN_PROGRESS"),
            ("FAILED", "FAILED"),
            ("SUCCESSFUL", "SUCCESSFUL"),
        ]
        assert choices == expected_choices

    def test_verification_status_values_list(self):
        values = VerificationStatus.values()
        expected_values = ["PENDING", "IN_PROGRESS", "FAILED", "SUCCESSFUL"]
        assert values == expected_values
