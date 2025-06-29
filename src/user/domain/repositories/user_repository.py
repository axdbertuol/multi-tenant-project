from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.user import User
from ..value_objects.email import Email


class UserRepository(ABC):
    """User repository interface for the User bounded context."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Save or update a user."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool:
        """Check if user exists by email."""
        pass

    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """Delete user by ID."""
        pass

    @abstractmethod
    def list_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List active users with pagination."""
        pass

    @abstractmethod
    def count_active_users(self) -> int:
        """Count total active users."""
        pass
