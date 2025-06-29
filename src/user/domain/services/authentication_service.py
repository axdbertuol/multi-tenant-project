from typing import Optional

from shared.domain.repositories.unit_of_work import UnitOfWork
from user.domain.repositories.user_repository import UserRepository
from user.domain.repositories.user_session_repository import UserSessionRepository

from ..entities.user import User
from ..entities.user_session import UserSession
from ..value_objects.email import Email


class AuthenticationService:
    """Domain service for authentication logic."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._session_repository: UserSessionRepository = uow.get_repository(
            "user_session"
        )
        self._uow = uow

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        try:
            email_vo = Email(value=email)
            user = self._user_repository.get_by_email(email_vo)

            if not user:
                return None

            if not user.is_active:
                return None

            if not user.verify_password(password):
                return None

            return user

        except ValueError:
            # Invalid email format
            return None

    def create_session(
        self,
        user: User,
        token: str,
        duration_hours: int = 24,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> UserSession:
        """Create a new user session."""
        from datetime import datetime, timedelta
        
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        session = UserSession.create(
            user_id=user.id,
            session_token=token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return self._session_repository.save(session)

    def validate_session(self, token: str) -> Optional[User]:
        """Validate session token and return user if valid."""
        session = self._session_repository.get_by_token(token)

        if not session or not session.is_valid():
            return None

        user = self._user_repository.get_by_id(session.user_id)

        if not user or not user.is_active:
            return None

        return user

    def revoke_session(self, token: str) -> bool:
        """Revoke a specific session."""
        session = self._session_repository.get_by_token(token)

        if not session:
            return False

        revoked_session = session.revoke()
        self._session_repository.save(revoked_session)

        return True

    def revoke_all_user_sessions(self, user_id) -> int:
        """Revoke all sessions for a user."""
        return self._session_repository.revoke_all_user_sessions(user_id)
