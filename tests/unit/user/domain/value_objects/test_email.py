from pydantic import ValidationError
import pytest
from user.domain.value_objects.email import Email


class TestEmail:
    """Unit tests for Email value object."""

    def test_create_valid_email(self):
        """Test creating a valid email."""
        email = Email(value="test@example.com")
        assert email.value == "test@example.com"
        assert str(email) == "test@example.com"

    def test_email_validation_invalid_format(self):
        """Test email validation with invalid format."""
        with pytest.raises(
            ValidationError, match="value is not a valid email address:"
        ):
            Email(value="invalid-email")

    def test_email_validation_empty_string(self):
        """Test email validation with empty string."""
        with pytest.raises(
            ValidationError, match="value is not a valid email address:"
        ):
            Email(value="")

    def test_email_validation_none(self):
        """Test email validation with None."""
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            Email(value=None)

    def test_email_validation_whitespace_only(self):
        """Test email validation with whitespace only."""
        with pytest.raises(
            ValidationError, match="value is not a valid email address:"
        ):
            Email(value="   ")

    def test_email_equality(self):
        """Test email equality comparison."""
        email1 = Email(value="test@example.com")
        email2 = Email(value="test@example.com")
        email3 = Email(value="different@example.com")

        assert email1 == email2
        assert email1 != email3

    def test_email_hash(self):
        """Test email hashing for use in sets/dicts."""
        email1 = Email(value="test@example.com")
        email2 = Email(value="test@example.com")

        assert hash(email1) == hash(email2)

        # Test in set
        email_set = {email1, email2}
        assert len(email_set) == 1

    def test_email_immutability(self):
        """Test that email is immutable."""
        email = Email(value="test@example.com")

        # Should not be able to change the value
        with pytest.raises(ValidationError):
            email.value = "new@example.com"

    def test_email_case_sensitivity(self):
        """Test email case handling."""
        email1 = Email(value="Test@Example.Com")
        email2 = Email(value="test@example.com")

        # Should normalize to lowercase
        assert email1.value == "test@example.com"
        assert email1 == email2

    def test_email_with_special_characters(self):
        """Test email with valid special characters."""
        valid_emails = [
            "user.name@example.com",
            "user+tag@example.com",
            "user-name@example.com",
            "123@example.com",
            "test@sub.domain.com",
        ]

        for email_str in valid_emails:
            email = Email(value=email_str)
            assert email.value == email_str.lower()

    def test_email_invalid_formats(self):
        """Test various invalid email formats."""
        invalid_emails = [
            "plainaddress",
            "@missinglocal.com",
            "missing@.com",
            "missing@domain",
            "spaces @domain.com",
            "user @domain.com",
            "user@ domain.com",
            "user@domain .com",
        ]

        for invalid_email in invalid_emails:
            with pytest.raises(
                ValidationError, match="value is not a valid email address:"
            ):
                Email(value=invalid_email)
