from typing import List, Optional
from uuid import UUID

from iam.domain.repositories.role_repository import RoleRepository
from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.repositories.user_repository import UserRepository
from ...domain.repositories.user_session_repository import UserSessionRepository

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
from ...domain.services.jwt_service import JWTService
from ...domain.services.rbac_service import RBACService


class AuthenticationUseCase:
    """Casos de uso para autenticação e autorização."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._session_repository: UserSessionRepository = uow.get_repository(
            "user_session"
        )
        self._auth_service = AuthenticationService(uow)
        self._jwt_service = JWTService()

        # Initialize RBAC service with required repositories
        role_repository = uow.get_repository("role")
        permission_repository = uow.get_repository("permission")
        role_permission_repository = uow.get_repository("role_permission")
        self._rbac_service = RBACService(
            role_repository=role_repository,
            permission_repository=permission_repository,
            role_permission_repository=role_permission_repository,
        )
        self._uow = uow

    def login(self, dto: LoginDTO) -> AuthResponseDTO:
        """Autentica um usuário e cria uma sessão."""
        with self._uow:
            # Authenticate user
            user = self._auth_service.authenticate(dto.email, dto.password)

            if not user:
                raise ValueError("Invalid email or password")

            # Determine session duration
            duration_hours = 720 if dto.remember_me else 24  # 30 days vs 1 day

            # Get user's organization context
            organization_id = self._get_user_primary_organization(user.id)

            # Get user permissions and roles for JWT token
            permissions = self._get_user_permissions(user.id, organization_id)
            roles = self._get_user_roles(user.id, organization_id)

            # Generate JWT access token with organization context and permissions
            access_token = self._jwt_service.create_access_token(
                user_id=str(user.id),
                organization_id=str(organization_id) if organization_id else None,
                email=user.email.value,
                permissions=permissions,
                roles=roles,
                user_agent=dto.user_agent,
                ip_address=dto.ip_address,
            )

            # Create session (keep for backward compatibility and session management)
            session = self._auth_service.create_session(
                user=user,
                token=access_token,  # Store JWT in session for revocation tracking
                duration_hours=duration_hours,
                user_agent=dto.user_agent,
                ip_address=dto.ip_address,
            )

        # Create response DTOs
        user_dto = UserResponseDTO.model_validate(
            {
                **user.model_dump(exclude="email"),
                "email": user.email.value,
            }
        )
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
            access_token=access_token,
            expires_in=int(duration_hours * 3600),  # Convert to seconds
        )

    def logout(self, token: str, dto: LogoutDTO) -> bool:
        """Realiza o logout do usuário, revogando a(s) sessão(ões)."""
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
        """Valida o token (JWT ou session) e retorna o usuário."""

        # First try to validate as JWT token
        jwt_payload = self._jwt_service.decode_token(token)
        if jwt_payload:
            # Valid JWT token - get user from database
            try:
                user_id = UUID(jwt_payload.user_id)
                user = self._user_repository.get_by_id(user_id)

                if not user or not user.is_active:
                    return None

                return UserResponseDTO.model_validate(
                    {
                        **user.model_dump(exclude="email"),
                        "email": user.email.value,
                    }
                )
            except (ValueError, TypeError):
                # Invalid user_id format or user not found
                pass

        # Fallback to session-based validation for backward compatibility
        user = self._auth_service.validate_session(token)

        if not user:
            return None

        return UserResponseDTO.model_validate(
            {
                **user.model_dump(exclude="email"),
                "email": user.email.value,
            }
        )

    def refresh_session(self, token: str) -> Optional[AuthResponseDTO]:
        """Atualiza o token JWT se for válido."""
        # First try to refresh as JWT token
        jwt_payload = self._jwt_service.decode_token(token)
        if jwt_payload:
            try:
                # Valid JWT token - get user and create new token
                user_id = UUID(jwt_payload.user_id)
                user = self._user_repository.get_by_id(user_id)

                if not user or not user.is_active:
                    return None

                # Get user's organization context (same as login)
                organization_id = self._get_user_primary_organization(user.id)

                # Get fresh permissions and roles for the new token
                permissions = self._get_user_permissions(user.id, organization_id)
                roles = self._get_user_roles(user.id, organization_id)

                # Create new JWT token
                new_access_token = self._jwt_service.create_access_token(
                    user_id=str(user.id),
                    organization_id=str(organization_id) if organization_id else None,
                    email=user.email.value,
                    permissions=permissions,
                    roles=roles,
                )

                # Update session in database if it exists
                with self._uow:
                    session = self._session_repository.get_by_token(token)
                    if session and session.is_valid():
                        # Create new session with new JWT token
                        original_duration = int(
                            (session.expires_at - session.created_at).total_seconds()
                            / 3600
                        )

                        new_session = self._auth_service.create_session(
                            user=user,
                            token=new_access_token,
                            duration_hours=original_duration,
                            user_agent=session.user_agent,
                            ip_address=session.ip_address,
                        )

                        # Revoke old session
                        self._auth_service.revoke_session(token)
                    else:
                        # Create new session with default duration
                        new_session = self._auth_service.create_session(
                            user=user,
                            token=new_access_token,
                            duration_hours=24,  # Default duration
                        )

                # Create response DTOs
                user_dto = UserResponseDTO.model_validate(
                    {
                        **user.model_dump(exclude="email"),
                        "email": user.email.value,
                    }
                )

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
                    access_token=new_access_token,
                    expires_in=int(24 * 3600),  # 24 hours in seconds
                )

            except (ValueError, TypeError):
                # Invalid user_id format or user not found
                pass

        # Fallback to legacy session-based refresh
        with self._uow:
            # Validate current session
            user = self._auth_service.validate_session(token)

            if not user:
                return None

            # Get current session
            session = self._session_repository.get_by_token(token)

            if not session or not session.is_valid():
                return None

            # Generate new JWT token instead of session token
            organization_id = self._get_user_primary_organization(user.id)
            permissions = self._get_user_permissions(user.id, organization_id)
            roles = self._get_user_roles(user.id, organization_id)

            new_token = self._jwt_service.create_access_token(
                user_id=str(user.id),
                organization_id=str(organization_id) if organization_id else None,
                email=user.email.value,
                permissions=permissions,
                roles=roles,
            )

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
        user_dto = UserResponseDTO.model_validate(
            {
                **user.model_dump(exclude="email"),
                "email": user.email.value,
            }
        )

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
        """Solicita a redefinição de senha para o usuário."""
        from ...domain.value_objects.email import Email

        # Check if user exists
        email_vo = Email(value=dto.email)
        user = self._user_repository.get_by_email(email_vo)

        if not user or not user.is_active:
            # Don't reveal if email exists or not
            return True

        # Generate reset token (in real implementation, this would be sent via email)
        # reset_token = self._generate_reset_token()

        # Store reset token (this would typically be in a separate table/cache)
        # For now, just return success

        return True

    def confirm_password_reset(self, dto: PasswordResetConfirmDTO) -> bool:
        """Confirma a redefinição de senha com o token."""

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
        """Altera a senha com a verificação da senha atual."""
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
        """Gera um token de sessão seguro."""
        import secrets

        return secrets.token_urlsafe(32)

    def _generate_reset_token(self) -> str:
        """Gera um token de redefinição de senha seguro."""
        import secrets

        return secrets.token_urlsafe(32)

    def _get_user_primary_organization(self, user_id: UUID) -> Optional[UUID]:
        """
        Get the user's primary organization ID.

        This method attempts to determine the user's primary organization context
        for JWT token generation. Currently returns None as a placeholder.

        TODO: This requires access to the organization context which is in a different
        bounded context. The implementation options are:
        1. Add organization context to IAM through dependency injection
        2. Use an application service that coordinates between contexts
        3. Emit domain events and handle organization context separately
        4. Create a shared service for user-organization lookup

        For now, JWT tokens will be generated without organization context.
        """
        # Placeholder implementation - returns None for organization_id
        # This means JWT tokens will not contain organization context initially
        return None

    def _get_user_permissions(
        self, user_id: UUID, organization_id: Optional[UUID]
    ) -> List[str]:
        """
        Get user permissions for JWT token.

        Args:
            user_id: User identifier
            organization_id: Organization context (optional)

        Returns:
            List of permission strings (e.g., ["user:read", "organization:write"])
        """
        try:
            return self._rbac_service.get_user_permissions(
                user_id=user_id, organization_id=organization_id
            )
        except Exception as e:
            # Log error and return empty permissions for security
            print(f"Error getting user permissions: {e}")
            return []

    def _get_user_roles(
        self, user_id: UUID, organization_id: Optional[UUID]
    ) -> List[str]:
        """
        Get user roles for JWT token.

        Args:
            user_id: User identifier
            organization_id: Organization context (optional)

        Returns:
            List of role names (e.g., ["admin", "user"])
        """
        try:
            # Get user roles through the role repository
            role_repo: RoleRepository = self._uow.get_repository("role")
            user_roles = role_repo.get_user_roles(user_id, organization_id)
            return [role.name for role in user_roles if role.is_active]
        except Exception as e:
            # Log error and return empty roles for security
            print(f"Error getting user roles: {e}")
            return []
