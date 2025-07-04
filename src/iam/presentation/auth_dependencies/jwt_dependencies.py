"""JWT authentication dependencies for FastAPI."""

from typing import List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from shared.infrastructure.database.connection import get_db
from ...application.use_cases.authentication_use_cases import AuthenticationUseCase
from ...domain.services.jwt_service import JWTService, JWTTokenPayload
from ...infrastructure.iam_unit_of_work import IAMUnitOfWork


def get_iam_uow(db: Session = Depends(get_db)) -> IAMUnitOfWork:
    """Get IAMUnitOfWork instance for JWT dependencies."""
    return IAMUnitOfWork(
        db, ["user", "user_session", "role", "permission", "policy", "resource"]
    )


def get_auth_use_case(
    uow: IAMUnitOfWork = Depends(get_iam_uow),
) -> AuthenticationUseCase:
    """Get AuthenticationUseCase for JWT validation."""
    return AuthenticationUseCase(uow)


class JWTAuthenticationContext:
    """Context object containing JWT authentication information."""
    
    def __init__(
        self,
        user_id: UUID,
        organization_id: Optional[UUID],
        email: str,
        permissions: List[str],
        roles: List[str],
        user_agent: Optional[str],
        ip_address: Optional[str],
        token_payload: JWTTokenPayload,
    ):
        self.user_id = user_id
        self.organization_id = organization_id
        self.email = email
        self.permissions = permissions
        self.roles = roles
        self.user_agent = user_agent
        self.ip_address = ip_address
        self.token_payload = token_payload
    
    def has_permission(self, required_permission: str) -> bool:
        """
        Check if the user has a specific permission.
        
        Args:
            required_permission: Permission to check (e.g., "user:read")
        
        Returns:
            True if user has permission, False otherwise
        """
        # Check for exact permission match
        if required_permission in self.permissions:
            return True
        
        # Check for wildcard permissions
        resource, action = required_permission.split(":", 1) if ":" in required_permission else (required_permission, "")
        
        # Check for resource wildcard (e.g., "user:*")
        if f"{resource}:*" in self.permissions:
            return True
        
        # Check for global wildcard (e.g., "*:*")
        if "*:*" in self.permissions:
            return True
        
        # Check for action wildcard (e.g., "*:read")
        if f"*:{action}" in self.permissions:
            return True
        
        return False
    
    def has_role(self, required_role: str) -> bool:
        """
        Check if the user has a specific role.
        
        Args:
            required_role: Role to check (e.g., "admin")
        
        Returns:
            True if user has role, False otherwise
        """
        return required_role in self.roles


def extract_bearer_token(request: Request) -> str:
    """
    Extract Bearer token from Authorization header.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Token string without 'Bearer ' prefix
    
    Raises:
        HTTPException: If Authorization header is missing or invalid
    """
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return auth_header.split(" ", 1)[1]


def get_jwt_service() -> JWTService:
    """Get JWT service instance."""
    return JWTService()


def get_jwt_payload(
    request: Request,
    jwt_service: JWTService = Depends(get_jwt_service),
) -> JWTTokenPayload:
    """
    Extract and validate JWT token from request.
    
    Args:
        request: FastAPI request object
        jwt_service: JWT service dependency
    
    Returns:
        JWTTokenPayload if token is valid
    
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    token = extract_bearer_token(request)
    
    payload = jwt_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def get_jwt_auth_context(
    jwt_payload: JWTTokenPayload = Depends(get_jwt_payload),
) -> JWTAuthenticationContext:
    """
    Get JWT authentication context from token payload.
    
    Args:
        jwt_payload: JWT token payload
    
    Returns:
        JWTAuthenticationContext with user and organization information
    
    Raises:
        HTTPException: If payload contains invalid data
    """
    try:
        user_id = UUID(jwt_payload.user_id)
        organization_id = UUID(jwt_payload.organization_id) if jwt_payload.organization_id else None
        
        return JWTAuthenticationContext(
            user_id=user_id,
            organization_id=organization_id,
            email=jwt_payload.email or "",
            permissions=jwt_payload.permissions,
            roles=jwt_payload.roles,
            user_agent=jwt_payload.user_agent,
            ip_address=jwt_payload.ip_address,
            token_payload=jwt_payload,
        )
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token payload: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_from_jwt(
    auth_context: JWTAuthenticationContext = Depends(get_jwt_auth_context),
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """
    Get current user from JWT token with database validation.
    
    This dependency validates the JWT token and then verifies the user
    still exists and is active in the database.
    
    Args:
        auth_context: JWT authentication context
        auth_use_case: Authentication use case
    
    Returns:
        UserResponseDTO if user is valid and active
    
    Raises:
        HTTPException: If user is not found or inactive
    """
    # Validate user exists and is active in database
    user = auth_use_case._user_repository.get_by_id(auth_context.user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from ...application.dtos.user_dto import UserResponseDTO
    
    return UserResponseDTO.model_validate(
        {
            **user.model_dump(exclude="email"),
            "email": user.email.value,
        }
    )


def require_organization_context(
    auth_context: JWTAuthenticationContext = Depends(get_jwt_auth_context),
) -> JWTAuthenticationContext:
    """
    Require that the JWT token contains organization context.
    
    Args:
        auth_context: JWT authentication context
    
    Returns:
        JWTAuthenticationContext with guaranteed organization_id
    
    Raises:
        HTTPException: If organization context is missing
    """
    if not auth_context.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization context required for this operation",
        )
    
    return auth_context


def require_permission(required_permission: str):
    """
    Create a dependency that requires a specific permission.
    
    Args:
        required_permission: Permission required (e.g., "user:read")
    
    Returns:
        FastAPI dependency function
    """
    def permission_dependency(
        auth_context: JWTAuthenticationContext = Depends(get_jwt_auth_context),
    ) -> JWTAuthenticationContext:
        if not auth_context.has_permission(required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {required_permission}",
            )
        return auth_context
    
    return Depends(permission_dependency)


def require_role(required_role: str):
    """
    Create a dependency that requires a specific role.
    
    Args:
        required_role: Role required (e.g., "admin")
    
    Returns:
        FastAPI dependency function
    """
    def role_dependency(
        auth_context: JWTAuthenticationContext = Depends(get_jwt_auth_context),
    ) -> JWTAuthenticationContext:
        if not auth_context.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {required_role}",
            )
        return auth_context
    
    return Depends(role_dependency)


def require_any_permission(*required_permissions: str):
    """
    Create a dependency that requires any of the specified permissions.
    
    Args:
        required_permissions: Permissions (at least one required)
    
    Returns:
        FastAPI dependency function
    """
    def any_permission_dependency(
        auth_context: JWTAuthenticationContext = Depends(get_jwt_auth_context),
    ) -> JWTAuthenticationContext:
        if not any(auth_context.has_permission(perm) for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {', '.join(required_permissions)}",
            )
        return auth_context
    
    return Depends(any_permission_dependency)


def require_all_permissions(*required_permissions: str):
    """
    Create a dependency that requires all of the specified permissions.
    
    Args:
        required_permissions: Permissions (all required)
    
    Returns:
        FastAPI dependency function
    """
    def all_permissions_dependency(
        auth_context: JWTAuthenticationContext = Depends(get_jwt_auth_context),
    ) -> JWTAuthenticationContext:
        if not all(auth_context.has_permission(perm) for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All of these permissions required: {', '.join(required_permissions)}",
            )
        return auth_context
    
    return Depends(all_permissions_dependency)


# Convenience dependencies for different use cases
CurrentUser = Depends(get_current_user_from_jwt)
JWTAuth = Depends(get_jwt_auth_context)
JWTAuthWithOrg = Depends(require_organization_context)