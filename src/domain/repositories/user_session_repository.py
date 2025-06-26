from abc import ABC
from typing import List, Optional
from uuid import UUID
from domain.entities.user_session import UserSession
from domain.repositories.base_repository import Repository


class UserSessionRepository(Repository[UserSession], ABC):
    """Repository interface for UserSession aggregate."""
    
    async def get_by_session_token(self, session_token: str) -> Optional[UserSession]:
        """Get session by session token."""
        pass
    
    async def get_active_sessions_by_user_id(self, user_id: UUID) -> List[UserSession]:
        """Get all active sessions for a user."""
        pass
    
    async def get_all_sessions_by_user_id(self, user_id: UUID) -> List[UserSession]:
        """Get all sessions (active and inactive) for a user."""
        pass
    
    async def expire_sessions_by_user_id(self, user_id: UUID) -> int:
        """Expire all active sessions for a user. Returns count of expired sessions."""
        pass
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from storage. Returns count of cleaned sessions."""
        pass