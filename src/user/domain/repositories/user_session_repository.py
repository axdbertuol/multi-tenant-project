from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.user_session import UserSession


class UserSessionRepository(ABC):
    """User session repository interface for the User bounded context."""

    @abstractmethod
    def save(self, session: UserSession) -> UserSession:
        """Save or update a user session."""
        pass

    @abstractmethod
    def get_by_id(self, session_id: UUID) -> Optional[UserSession]:
        """Get session by ID."""
        pass

    @abstractmethod
    def get_by_token(self, token: str) -> Optional[UserSession]:
        """Get session by token."""
        pass

    @abstractmethod
    def get_active_by_user_id(self, user_id: UUID) -> List[UserSession]:
        """Get all active sessions for a user."""
        pass

    @abstractmethod
    def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """Revoke all sessions for a user. Returns count of revoked sessions."""
        pass

    @abstractmethod
    def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions. Returns count of cleaned sessions."""
        pass

    @abstractmethod
    def delete(self, session_id: UUID) -> bool:
        """Delete session by ID."""
        pass
