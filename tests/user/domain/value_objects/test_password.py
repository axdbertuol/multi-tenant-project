import pytest
from user.domain.value_objects.password import Password


class TestPassword:
    def test_create_valid_password(self):
        """Test creating a password with valid strength."""
        plain_password = "SecurePass123"
        password = Password.create(plain_password)
        
        assert isinstance(password, Password)
        assert password.hashed_value != plain_password
        assert password.verify(plain_password) is True

    def test_password_strength_validation_minimum_length(self):
        """Test password minimum length validation."""
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            Password.create("Short1")

    def test_password_strength_validation_maximum_length(self):
        """Test password maximum length validation."""
        long_password = "A" * 129 + "a1"  # 131 characters
        with pytest.raises(ValueError, match="Password cannot exceed 128 characters"):
            Password.create(long_password)

    def test_password_strength_validation_empty(self):
        """Test empty password validation."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            Password.create("")
        
        with pytest.raises(ValueError, match="Password cannot be empty"):
            Password.create("   ")  # Only whitespace

    def test_password_strength_validation_uppercase(self):
        """Test password must contain uppercase letter."""
        with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
            Password.create("lowercase123")

    def test_password_strength_validation_lowercase(self):
        """Test password must contain lowercase letter."""
        with pytest.raises(ValueError, match="Password must contain at least one lowercase letter"):
            Password.create("UPPERCASE123")

    def test_password_strength_validation_digit(self):
        """Test password must contain digit."""
        with pytest.raises(ValueError, match="Password must contain at least one digit"):
            Password.create("NoDigitsHere")

    def test_valid_password_examples(self):
        """Test various valid password examples."""
        valid_passwords = [
            "SecurePass123",
            "MyPassword1",
            "StrongPwd2023",
            "ComplexPassword1",
            "Aa1bcdefgh",  # Minimum valid
            "A" * 126 + "a1"  # Maximum valid (128 chars)
        ]
        
        for pwd in valid_passwords:
            password = Password.create(pwd)
            assert password.verify(pwd) is True

    def test_password_verification(self):
        """Test password verification with correct and incorrect passwords."""
        plain_password = "SecurePass123"
        password = Password.create(plain_password)
        
        # Correct password
        assert password.verify(plain_password) is True
        
        # Incorrect passwords
        assert password.verify("WrongPassword123") is False
        assert password.verify("securepass123") is False  # Case sensitive
        assert password.verify("SecurePass124") is False  # Different digit
        assert password.verify("") is False

    def test_password_from_hash(self):
        """Test creating password from existing hash."""
        plain_password = "SecurePass123"
        original_password = Password.create(plain_password)
        
        # Create new password object from hash
        password_from_hash = Password.from_hash(original_password.hashed_value)
        
        assert password_from_hash.hashed_value == original_password.hashed_value
        assert password_from_hash.verify(plain_password) is True
        assert password_from_hash == original_password

    def test_password_hashing_uniqueness(self):
        """Test that same password creates different hashes (due to salt)."""
        plain_password = "SecurePass123"
        password1 = Password.create(plain_password)
        password2 = Password.create(plain_password)
        
        # Hashes should be different due to random salt
        assert password1.hashed_value != password2.hashed_value
        
        # But both should verify the same plain password
        assert password1.verify(plain_password) is True
        assert password2.verify(plain_password) is True

    def test_password_equality(self):
        """Test password equality comparison."""
        plain_password = "SecurePass123"
        password1 = Password.create(plain_password)
        password2 = Password.from_hash(password1.hashed_value)
        password3 = Password.create("DifferentPass123")
        
        # Same hash should be equal
        assert password1 == password2
        
        # Different passwords should not be equal
        assert password1 != password3
        
        # Different types should not be equal
        assert password1 != "SecurePass123"
        assert password1 != None

    def test_password_hashing_for_collections(self):
        """Test password hashing for use in sets and dictionaries."""
        plain_password = "SecurePass123"
        password1 = Password.create(plain_password)
        password2 = Password.from_hash(password1.hashed_value)
        
        # Same passwords should have same hash
        assert hash(password1) == hash(password2)
        
        # Test in set
        password_set = {password1, password2}
        assert len(password_set) == 1  # Should be considered same

    def test_password_string_representation(self):
        """Test password string representation for security."""
        password = Password.create("SecurePass123")
        
        # Should not reveal actual password
        assert str(password) == "[PROTECTED]"
        assert repr(password) == "Password([PROTECTED])"
        
        # Should not contain actual password or hash in string representation
        assert "SecurePass123" not in str(password)
        assert "SecurePass123" not in repr(password)
        assert password.hashed_value not in str(password)

    def test_password_immutability(self):
        """Test that password objects are immutable."""
        password = Password.create("SecurePass123")
        
        # Should not be able to modify hashed_value
        with pytest.raises(AttributeError):
            password.hashed_value = "modified_hash"

    def test_password_edge_cases(self):
        """Test password edge cases."""
        # Exactly 8 characters (minimum)
        min_password = "MinPass1"
        password_min = Password.create(min_password)
        assert password_min.verify(min_password) is True
        
        # Exactly 128 characters (maximum)
        max_password = "A" * 125 + "a12"  # 128 characters total
        password_max = Password.create(max_password)
        assert password_max.verify(max_password) is True

    def test_password_special_characters(self):
        """Test passwords with special characters."""
        special_passwords = [
            "SecurePass123!",
            "MyP@ssw0rd",
            "Strong#Pass1",
            "Secure$123Password"
        ]
        
        for pwd in special_passwords:
            password = Password.create(pwd)
            assert password.verify(pwd) is True

    def test_password_unicode_characters(self):
        """Test passwords with unicode characters."""
        unicode_passwords = [
            "Sécüre123",  # Accented characters
            "Пароль123",  # Cyrillic
            "パスワード123A"  # Japanese + Latin
        ]
        
        for pwd in unicode_passwords:
            password = Password.create(pwd)
            assert password.verify(pwd) is True

    def test_bcrypt_compatibility(self):
        """Test that created passwords are compatible with bcrypt."""
        import bcrypt
        
        plain_password = "SecurePass123"
        password = Password.create(plain_password)
        
        # Should be able to verify using bcrypt directly
        assert bcrypt.checkpw(
            plain_password.encode('utf-8'),
            password.hashed_value.encode('utf-8')
        ) is True