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
from ...domain.services.authorization_service import AuthorizationService
from ...domain.entities.authorization_context import AuthorizationContext


class SessionUseCase:
    """Casos de uso para gerenciamento de sessões."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._session_repository: UserSessionRepository = uow.get_repository(
            "user_session"
        )
        self._auth_service = AuthenticationService(uow)
        self._uow = uow
        
        # Initialize authorization service for permission checking
        from ...domain.services.rbac_service import RBACService
        from ...domain.services.abac_service import ABACService
        from ...domain.services.policy_evaluation_service import PolicyEvaluationService
        
        rbac_service = RBACService(
            role_repository=uow.get_repository("role"),
            permission_repository=uow.get_repository("permission"),
            role_permission_repository=uow.get_repository("role_permission"),
        )
        policy_evaluation_service = PolicyEvaluationService()
        abac_service = ABACService(
            policy_repository=uow.get_repository("policy"),
            resource_repository=uow.get_repository("resource"),
            policy_evaluation_service=policy_evaluation_service,
        )
        self._authorization_service = AuthorizationService(rbac_service, abac_service)

    def create_session(self, dto: SessionCreateDTO) -> SessionResponseDTO:
        """Cria uma nova sessão de usuário."""
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
        """Obtém uma sessão pelo ID."""
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
        """Obtém uma sessão pelo token."""
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
        """Obtém todas as sessões de um usuário."""

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
        """Revoga uma sessão específica."""
        with self._uow:
            session = self._session_repository.get_by_id(session_id)

            if not session:
                return False

            result = self._auth_service.revoke_session(session.session_token)

        return result

    def revoke_session_by_token(self, token: str) -> bool:
        """Revoga uma sessão pelo token."""
        with self._uow:
            result = self._auth_service.revoke_session(token)
        return result

    def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """Revoga todas as sessões de um usuário."""
        with self._uow:
            result = self._auth_service.revoke_all_user_sessions(user_id)
        return result

    def extend_session(
        self, session_id: UUID, hours: int = 24
    ) -> Optional[SessionResponseDTO]:
        """Estende a duração de uma sessão."""
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
        """Limpa sessões expiradas."""
        with self._uow:
            result = self._session_repository.cleanup_expired_sessions()
        return result

    def validate_session_access(
        self, 
        token: str, 
        required_permissions: list[str] = None,
        resource_type: str = None,
        resource_id: str = None,
        organization_id: str = None
    ) -> bool:
        """
        Valida a sessão e permissões opcionais.
        
        Args:
            token: Token da sessão
            required_permissions: Lista de permissões necessárias (ex: ["user:read", "organization:manage"])
            resource_type: Tipo do recurso para verificação de permissão (ex: "user", "organization")
            resource_id: ID específico do recurso
            organization_id: ID da organização para escopo de permissões
            
        Returns:
            bool: True se a sessão é válida e o usuário tem as permissões necessárias
        """
        # Validate session first
        user = self._auth_service.validate_session(token)
        if not user:
            return False

        # If no specific permissions required, just return session validity
        if not required_permissions:
            return True

        # Check each required permission using the authorization service
        for permission in required_permissions:
            # Create authorization context
            from uuid import UUID as UUIDType
            
            # Handle UUID conversion for organization_id and resource_id
            org_uuid = None
            if organization_id:
                org_uuid = UUIDType(organization_id) if isinstance(organization_id, str) else organization_id
                
            res_uuid = None
            if resource_id:
                res_uuid = UUIDType(resource_id) if isinstance(resource_id, str) else resource_id
            
            context = AuthorizationContext.create(
                user_id=user.id,
                resource_type=resource_type or permission.split(':')[0],  # Extract from permission if not provided
                action=permission.split(':')[1] if ':' in permission else permission,
                organization_id=org_uuid,
                resource_id=res_uuid,
                user_attributes={
                    "email": user.email.value,
                    "name": user.name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                }
            )
            
            # Check permission using authorization service
            decision = self._authorization_service.authorize(context)
            if not decision.is_allowed():
                return False
                
        return True

    def validate_session_access_simple(
        self, 
        token: str, 
        action: str, 
        resource_type: str = "system",
        organization_id: str = None
    ) -> bool:
        """
        Método simplificado para validação de sessão e permissão única.
        
        Args:
            token: Token da sessão
            action: Ação específica (ex: "read", "write", "delete")
            resource_type: Tipo do recurso (padrão: "system")
            organization_id: ID da organização para escopo
            
        Returns:
            bool: True se autorizado
        """
        permission = f"{resource_type}:{action}"
        return self.validate_session_access(
            token=token,
            required_permissions=[permission],
            resource_type=resource_type,
            organization_id=organization_id
        )

    def get_session_user_permissions(self, token: str, organization_id: str = None) -> list[str]:
        """
        Obtém todas as permissões do usuário da sessão.
        
        Args:
            token: Token da sessão
            organization_id: ID da organização para escopo
            
        Returns:
            list[str]: Lista de permissões do usuário
        """
        user = self._auth_service.validate_session(token)
        if not user:
            return []
            
        # Create a basic context to get user permissions
        from uuid import UUID as UUIDType
        
        org_uuid = None
        if organization_id:
            org_uuid = UUIDType(organization_id) if isinstance(organization_id, str) else organization_id
            
        context = AuthorizationContext.create(
            user_id=user.id,
            resource_type="system",
            action="list_permissions",
            organization_id=org_uuid,
            user_attributes={
                "email": user.email.value,
                "name": user.name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            }
        )
        
        # Get user permissions through RBAC service
        return self._authorization_service._rbac_service.get_user_permissions(
            user_id=user.id,
            organization_id=organization_id
        )

    def _generate_session_token(self) -> str:
        """Gera um token de sessão seguro."""
        import secrets

        return secrets.token_urlsafe(32)
