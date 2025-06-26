import pytest
import bcrypt
from src.domain.value_objects.password import Password


class TestPassword:
    """Unit tests for Password value object."""
    
    def test_create_password_from_plain_text(self):
        """Test creating password from plain text."""
        password = Password.create("password123")
        
        assert password.hashed_value is not None
        assert len(password.hashed_value) > 0
        assert password.hashed_value != "password123"  # Should be hashed
    
    def test_create_password_from_hash(self):
        """Test creating password from existing hash."""
        original_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        password = Password.from_hash(original_hash)
        
        assert password.hashed_value == original_hash
    
    def test_password_verification_correct(self):
        """Test password verification with correct password."""
        password = Password.create("password123")
        
        assert password.verify("password123") is True
    
    def test_password_verification_incorrect(self):
        """Test password verification with incorrect password."""
        password = Password.create("password123")
        
        assert password.verify("wrongpassword") is False
    
    def test_password_minimum_length_validation(self):
        """Test password minimum length validation."""
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            Password.create("short")
    
    def test_password_empty_validation(self):
        """Test password empty validation."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            Password.create("")
    
    def test_password_whitespace_only_validation(self):
        """Test password whitespace only validation."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            Password.create("   ")
    
    def test_password_none_validation(self):
        """Test password None validation."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            Password.create(None)
    
    def test_password_string_representation(self):
        """Test password string representation is protected."""
        password = Password.create("password123")
        
        assert str(password) == "[PROTECTED]"
        assert repr(password) == "Password([PROTECTED])"
    
    def test_password_equality(self):
        """Test password equality comparison."""
        password1 = Password.create("password123")
        password2 = Password.from_hash(password1.hashed_value)
        password3 = Password.create("different123")
        
        assert password1 == password2
        assert password1 != password3
    
    def test_password_hash_consistency(self):
        """Test password hash consistency."""
        password1 = Password.create("password123")
        password2 = Password.from_hash(password1.hashed_value)
        
        assert hash(password1) == hash(password2)
    
    def test_password_immutability(self):
        """Test that password is immutable."""
        password = Password.create("password123")
        
        # Should not be able to change the hashed_value
        with pytest.raises(AttributeError):
            password.hashed_value = "new_hash"
    
    def test_password_with_special_characters(self):
        """Test password with special characters."""
        special_password = "P@ssw0rd!#$%"
        password = Password.create(special_password)
        
        assert password.verify(special_password) is True
        assert password.verify("password123") is False
    
    def test_password_case_sensitivity(self):
        """Test password case sensitivity."""
        password = Password.create("Password123")
        
        assert password.verify("Password123") is True
        assert password.verify("password123") is False
        assert password.verify("PASSWORD123") is False
    
    def test_password_unicode_characters(self):
        """Test password with unicode characters."""
        unicode_password = "pássword123"
        password = Password.create(unicode_password)
        
        assert password.verify(unicode_password) is True
        assert password.verify("password123") is False
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = Password.create("password123")
        password2 = Password.create("password456")
        
        assert password1.hashed_value != password2.hashed_value
        assert password1 != password2
    
    def test_same_password_different_hashes_due_to_salt(self):
        """Test that same password can produce different hashes due to salt."""
        password1 = Password.create("password123")
        password2 = Password.create("password123")
        
        # Different hashes due to different salts
        assert password1.hashed_value != password2.hashed_value
        # But both verify correctly
        assert password1.verify("password123") is True
        assert password2.verify("password123") is True
    
    def test_password_with_exact_minimum_length(self):
        """Test password with exactly minimum length (8 characters)."""
        password = Password.create("12345678")
        
        assert password.verify("12345678") is True
        assert len("12345678") == 8