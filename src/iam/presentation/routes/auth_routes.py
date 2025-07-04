"""Unified authentication endpoints with resource-based application support."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional

from ...presentation.dependencies import get_auth_use_case
from ...application.dtos.auth_dto import (
    LoginDTO,
    AuthResponseDTO,
    LogoutDTO,
    PasswordResetRequestDTO,
    PasswordResetConfirmDTO,
)
from ...application.use_cases.authentication_use_cases import AuthenticationUseCase

router = APIRouter(tags=["Authentication"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client information from request for security logging."""
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return user_agent, ip_address


@router.post("/login", response_model=AuthResponseDTO)
def login(
    dto: LoginDTO,
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """
    Authenticate user and create JWT session.
    
    This unified endpoint supports authentication for all resource types including:
    - Web chat resources
    - Management dashboard resources  
    - API access resources
    - Any custom application resources
    
    The JWT token will contain organization context and resource permissions
    based on the user's roles and the resources they have access to.
    """
    try:
        # Extract client information for security tracking
        user_agent, ip_address = get_client_info(request)
        dto.user_agent = user_agent
        dto.ip_address = ip_address
        
        # Authenticate user and generate JWT with resource permissions
        result = use_case.login(dto)
        
        return result
        
    except ValueError as e:
        # Handle authentication errors securely
        error_msg = str(e)
        
        # Don't expose internal details for security
        if "password" in error_msg.lower():
            error_msg = "Invalid email or password"
        elif "user" in error_msg.lower() and "active" in error_msg.lower():
            error_msg = "Account is not active"
        elif "email" in error_msg.lower():
            error_msg = "Invalid email or password"
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except Exception as e:
        # Handle unexpected errors without exposing internals
        print(f"Authentication error: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable",
        )


@router.post("/logout")
def logout(
    dto: LogoutDTO,
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Log out user and revoke JWT session."""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
            )

        token = auth_header.split(" ")[1]
        success = use_case.logout(token, dto)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session",
            )

        return {"message": "Logged out successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refresh", response_model=AuthResponseDTO)
def refresh_session(
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Refresh JWT token with updated permissions."""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
            )

        token = auth_header.split(" ")[1]
        result = use_case.refresh_session(token)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
            )

        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/validate")
def validate_session(
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Validate JWT token and return user information with resource permissions."""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
            )

        token = auth_header.split(" ")[1]
        user = use_case.validate_session(token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
            )

        # Extract additional context from JWT token
        from ...domain.services.jwt_service import JWTService
        jwt_service = JWTService()
        organization_id = jwt_service.get_token_organization_id(token)
        permissions = jwt_service.get_token_permissions(token)
        roles = jwt_service.get_token_roles(token)

        return {
            "user": user,
            "organization_id": organization_id,
            "permissions": permissions,
            "roles": roles,
            "token_valid": True,
            "message": "Token is valid"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        print(f"Token validation error: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/password-reset/request")
def request_password_reset(
    dto: PasswordResetRequestDTO,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Request password reset for user."""
    try:
        use_case.request_password_reset(dto)
        return {"message": "Password reset email sent if account exists"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/password-reset/confirm")
def confirm_password_reset(
    dto: PasswordResetConfirmDTO,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Confirm password reset with token."""
    try:
        success = use_case.confirm_password_reset(dto)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        return {"message": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))