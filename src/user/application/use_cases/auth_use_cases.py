from typing import Optional
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from user.domain.repositories.user_repository import UserRepository
from user.domain.repositories.user_session_repository import UserSessionRepository

from ..dtos.auth_dto import (
    LoginDTO,
    AuthResponseDTO,
    LogoutDTO,
    PasswordResetRequestDTO,
    PasswordResetConfirmDTO,
)
from ..dtos.user_dto import UserResponseDTO
from ..dtos.session_dto import SessionResponseDTO
from ...domain.services.authentication_service import AuthenticationService


class AuthUseCase:
    """Use cases for authentication and authorization."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._session_repository: UserSessionRepository = uow.get_repository(
            "user_session"
        )
        self._auth_service = AuthenticationService(uow)
        self._uow = uow

    def login(self, dto: LoginDTO) -> AuthResponseDTO:
        """Authenticate user and create session."""
        with self._uow:
            # Authenticate user
            user = self._auth_service.authenticate(dto.email, dto.password)

            if not user:
                raise ValueError("Invalid email or password")

            # Determine session duration
            duration_hours = 720 if dto.remember_me else 24  # 30 days vs 1 day

            # Generate session token
            session_token = self._generate_session_token()

            # Create session
            session = self._auth_service.create_session(
                user=user,
                token=session_token,
                duration_hours=duration_hours,
                user_agent=dto.user_agent,
                ip_address=dto.ip_address,
            )

        # Create response DTOs
        user_dto = UserResponseDTO.model_validate(user)
        session_dto = SessionResponseDTO.model_validate(
            {
                **session.model_dump(),
                "is_expired": session.is_expired(),
                "is_valid": session.is_valid(),
            }
        )

        return AuthResponseDTO(
            user=user_dto,
            session=session_dto,
            access_token=session_token,
            expires_in=int(duration_hours * 3600),  # Convert to seconds
        )

    def logout(self, token: str, dto: LogoutDTO) -> bool:
        """Logout user by revoking session(s)."""
        with self._uow:
            # Get session to find user
            session = self._session_repository.get_by_token(token)

            if not session:
                return False

            if dto.revoke_all_sessions:
                # Revoke all user sessions
                self._auth_service.revoke_all_user_sessions(session.user_id)
            else:
                # Revoke only current session
                self._auth_service.revoke_session(token)

        return True

    def validate_session(self, token: str) -> Optional[UserResponseDTO]:
        """Validate session token and return user."""

        user = self._auth_service.validate_session(token)

        if not user:
            return None

        return UserResponseDTO.model_validate(user)

    def refresh_session(self, token: str) -> Optional[AuthResponseDTO]:
        """Refresh session if valid."""
        with self._uow:
            # Validate current session
            user = self._auth_service.validate_session(token)

            if not user:
                return None

            # Get current session
            session = self._session_repository.get_by_token(token)

            if not session or not session.is_valid():
                return None

            # Generate new token
            new_token = self._generate_session_token()

            # Create new session with same duration
            original_duration = int(
                (session.expires_at - session.created_at).total_seconds() / 3600
            )

            new_session = self._auth_service.create_session(
                user=user,
                token=new_token,
                duration_hours=original_duration,
                user_agent=session.user_agent,
                ip_address=session.ip_address,
            )

            # Revoke old session
            self._auth_service.revoke_session(token)

        # Create response DTOs
        user_dto = UserResponseDTO.model_validate(user)
        session_dto = SessionResponseDTO.model_validate(
            {
                **new_session.model_dump(),
                "is_expired": new_session.is_expired(),
                "is_valid": new_session.is_valid(),
            }
        )

        return AuthResponseDTO(
            user=user_dto,
            session=session_dto,
            access_token=new_token,
            expires_in=int(original_duration * 3600),
        )

    def request_password_reset(self, dto: PasswordResetRequestDTO) -> bool:
        """Request password reset for user."""
        from ...domain.value_objects.email import Email

        # Check if user exists
        email_vo = Email(value=dto.email)
        user = self._user_repository.get_by_email(email_vo)

        if not user or not user.is_active:
            # Don't reveal if email exists or not
            return True

        # Generate reset token (in real implementation, this would be sent via email)
        reset_token = self._generate_reset_token()

        # Store reset token (this would typically be in a separate table/cache)
        # For now, just return success

        return True

    def confirm_password_reset(self, dto: PasswordResetConfirmDTO) -> bool:
        """Confirm password reset with token."""

        # In real implementation, validate reset token and get associated user
        # For now, this is a placeholder implementation

        # Validate token format
        if len(dto.token) < 32:
            raise ValueError("Invalid reset token")

        # Here you would:
        # 1. Validate token exists and is not expired
        # 2. Get associated user
        # 3. Update user password
        # 4. Revoke all user sessions
        # 5. Delete/mark token as used

        return True

    def change_password_with_current(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """Change password with current password verification."""
        with self._uow:
            user = self._user_repository.get_by_id(user_id)

            if not user:
                raise ValueError("User not found")

            # Verify current password
            if not user.verify_password(current_password):
                raise ValueError("Current password is incorrect")

            # Update password
            updated_user = user.change_password(new_password)
            self._user_repository.save(updated_user)

            # Revoke all sessions to force re-login
            self._auth_service.revoke_all_user_sessions(user_id)

        return True

    def _generate_session_token(self) -> str:
        """Generate secure session token."""
        import secrets

        return secrets.token_urlsafe(32)

    def _generate_reset_token(self) -> str:
        """Generate secure password reset token."""
        import secrets

        return secrets.token_urlsafe(32)
