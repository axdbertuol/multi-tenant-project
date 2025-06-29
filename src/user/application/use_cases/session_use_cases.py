from typing import Optional
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork

from ..dtos.session_dto import (
    SessionCreateDTO,
    SessionResponseDTO,
    SessionListResponseDTO,
)
from ...domain.entities.user_session import UserSession
from ...domain.repositories.user_repository import UserRepository
from ...domain.repositories.user_session_repository import UserSessionRepository
from ...domain.services.authentication_service import AuthenticationService


class SessionUseCase:
    """Use cases for session management."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._session_repository: UserSessionRepository = uow.get_repository(
            "user_session"
        )
        self._auth_service = AuthenticationService(uow)
        self._uow = uow

    def create_session(self, dto: SessionCreateDTO) -> SessionResponseDTO:
        """Create a new user session."""
        with self._uow:
            # Verify user exists and is active
            user = self._user_repository.get_by_id(dto.user_id)

            if not user:
                raise ValueError("User not found")

            if not user.is_active:
                raise ValueError("User account is not active")

            # Generate session token
            session_token = self._generate_session_token()

            # Create session
            session = self._auth_service.create_session(
                user=user,
                token=session_token,
                duration_hours=dto.duration_hours,
                user_agent=dto.user_agent,
                ip_address=dto.ip_address,
            )

        return SessionResponseDTO.model_validate(
            {
                **session.model_dump(),
                "is_expired": session.is_expired(),
                "is_valid": session.is_valid(),
            }
        )

    def get_session_by_id(self, session_id: UUID) -> Optional[SessionResponseDTO]:
        """Get session by ID."""
        session = self._session_repository.get_by_id(session_id)

        if not session:
            return None

        return SessionResponseDTO.model_validate(
            {
                **session.model_dump(),
                "is_expired": session.is_expired(),
                "is_valid": session.is_valid(),
            }
        )

    def get_session_by_token(self, token: str) -> Optional[SessionResponseDTO]:
        """Get session by token."""
        session = self._session_repository.get_by_token(token)

        if not session:
            return None

        return SessionResponseDTO.model_validate(
            {
                **session.model_dump(),
                "is_expired": session.is_expired(),
                "is_valid": session.is_valid(),
            }
        )

    def get_user_sessions(self, user_id: UUID) -> SessionListResponseDTO:
        """Get all sessions for a user."""

        # Get active sessions
        sessions = self._session_repository.get_active_by_user_id(user_id)

        # Convert to DTOs
        session_dtos = []
        active_count = 0

        for session in sessions:
            session_dto = SessionResponseDTO.model_validate(
                {
                    **session.model_dump(),
                    "is_expired": session.is_expired(),
                    "is_valid": session.is_valid(),
                }
            )
            session_dtos.append(session_dto)

            if session_dto.is_valid:
                active_count += 1

        return SessionListResponseDTO(
            sessions=session_dtos, total=len(session_dtos), active_count=active_count
        )

    def revoke_session(self, session_id: UUID) -> bool:
        """Revoke a specific session."""
        with self._uow:
            session = self._session_repository.get_by_id(session_id)

            if not session:
                return False

            result = self._auth_service.revoke_session(session.session_token)

        return result

    def revoke_session_by_token(self, token: str) -> bool:
        """Revoke session by token."""
        with self._uow:
            result = self._auth_service.revoke_session(token)
        return result

    def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """Revoke all sessions for a user."""
        with self._uow:
            result = self._auth_service.revoke_all_user_sessions(user_id)
        return result

    def extend_session(
        self, session_id: UUID, hours: int = 24
    ) -> Optional[SessionResponseDTO]:
        """Extend session duration."""
        with self._uow:
            session = self._session_repository.get_by_id(session_id)

            if not session or not session.is_valid():
                return None

            # Extend session
            extended_session = session.extend(hours)
            saved_session = self._session_repository.save(extended_session)

        return SessionResponseDTO.model_validate(
            {
                **saved_session.model_dump(),
                "is_expired": saved_session.is_expired(),
                "is_valid": saved_session.is_valid(),
            }
        )

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        with self._uow:
            result = self._session_repository.cleanup_expired_sessions()
        return result

    def validate_session_access(
        self, token: str, required_permissions: list[str] = None
    ) -> bool:
        """Validate session and optional permissions."""

        # Validate session
        user = self._auth_service.validate_session(token)

        if not user:
            return False

        # If no specific permissions required, just return session validity
        if not required_permissions:
            return True

        # Here you would integrate with authorization service to check permissions
        # For now, assume all authenticated users have basic permissions

        return True

    def _generate_session_token(self) -> str:
        """Generate secure session token."""
        import secrets

        return secrets.token_urlsafe(32)
