import pytest
from user.domain.value_objects.email import Email


class TestEmail:
    def test_valid_email_creation(self):
        """Test creating a valid email."""
        email_str = "test@example.com"
        email = Email(value=email_str)
        
        assert email.value == email_str
        assert str(email) == email_str

    def test_email_normalization(self):
        """Test email normalization (lowercase, strip whitespace)."""
        email = Email(value="  TEST@EXAMPLE.COM  ")
        
        assert email.value == "test@example.com"

    def test_invalid_email_formats(self):
        """Test that invalid email formats raise ValueError."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "test@",
            "test.example.com",
            "test@.com",
            "test@com",
            "",
            "test@@example.com",
            "test@example.",
            "test @example.com",
            "test@exa mple.com"
        ]
        
        for invalid_email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email format"):
                Email(value=invalid_email)

    def test_valid_email_formats(self):
        """Test various valid email formats."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@example123.com",
            "test@sub.example.com",
            "a@b.co",
            "user@example-domain.com"
        ]
        
        for valid_email in valid_emails:
            email = Email(value=valid_email)
            assert email.value == valid_email.lower()

    def test_domain_extraction(self):
        """Test extracting domain from email."""
        email = Email(value="test@example.com")
        
        assert email.domain() == "example.com"

    def test_local_part_extraction(self):
        """Test extracting local part from email."""
        email = Email(value="test.user@example.com")
        
        assert email.local_part() == "test.user"

    def test_email_equality(self):
        """Test email equality comparison."""
        email1 = Email(value="test@example.com")
        email2 = Email(value="test@example.com")
        email3 = Email(value="other@example.com")
        
        assert email1 == email2
        assert email1 != email3
        assert email1 != "test@example.com"  # Different type
        assert email1 != None

    def test_email_hashing(self):
        """Test email hashing for use in sets and dicts."""
        email1 = Email(value="test@example.com")
        email2 = Email(value="test@example.com")
        email3 = Email(value="other@example.com")
        
        # Same emails should have same hash
        assert hash(email1) == hash(email2)
        
        # Different emails should have different hash (usually)
        assert hash(email1) != hash(email3)
        
        # Test in set
        email_set = {email1, email2, email3}
        assert len(email_set) == 2  # email1 and email2 are considered same

    def test_email_immutability(self):
        """Test that email objects are immutable."""
        email = Email(value="test@example.com")
        
        # Should not be able to modify value
        with pytest.raises(AttributeError):
            email.value = "other@example.com"

    def test_email_complex_domains(self):
        """Test emails with complex domain structures."""
        complex_emails = [
            "user@mail.example.com",
            "test@sub.domain.example.co.uk",
            "admin@localhost.localdomain",
            "user@example-with-dash.com"
        ]
        
        for email_str in complex_emails:
            email = Email(value=email_str)
            assert email.value == email_str.lower()
            assert email.domain() == email_str.split("@")[1].lower()

    def test_email_string_representation(self):
        """Test string representation of email."""
        email_str = "test@example.com"
        email = Email(value=email_str)
        
        assert str(email) == email_str
        assert repr(email) == f"Email(value='{email_str}')"

    def test_email_case_insensitive_comparison(self):
        """Test that email comparison is case insensitive."""
        email1 = Email(value="TEST@EXAMPLE.COM")
        email2 = Email(value="test@example.com")
        
        assert email1 == email2
        assert email1.value == "test@example.com"  # Normalized to lowercase

    def test_email_with_plus_addressing(self):
        """Test email with plus addressing (Gmail style)."""
        email = Email(value="user+tag@example.com")
        
        assert email.value == "user+tag@example.com"
        assert email.local_part() == "user+tag"
        assert email.domain() == "example.com"

    def test_email_with_dots_in_local_part(self):
        """Test email with dots in local part."""
        email = Email(value="first.last@example.com")
        
        assert email.value == "first.last@example.com"
        assert email.local_part() == "first.last"
        assert email.domain() == "example.com"