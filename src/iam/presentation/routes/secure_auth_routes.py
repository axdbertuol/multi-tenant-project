"""Secure JWT authentication endpoints with RBAC integration."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional

from ..dependencies import get_auth_use_case
from ...application.dtos.auth_dto import (
    LoginDTO,
    AuthResponseDTO,
)
from ...application.use_cases.authentication_use_cases import AuthenticationUseCase

router = APIRouter(prefix="/secure-auth", tags=["Secure Authentication"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client information from request for security logging."""
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return user_agent, ip_address


@router.post("/token", response_model=AuthResponseDTO)
def generate_secure_jwt_token(
    dto: LoginDTO,
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """
    Generate a secure JWT token with RBAC permissions.
    
    This endpoint implements the following security features:
    - Short-lived JWT tokens (15 minutes default)
    - RBAC permissions embedded in token
    - Organization context inclusion
    - Client metadata tracking (IP, user agent)
    - Secure session management
    - Graceful error handling
    
    Security Compliance:
    - Validates credentials against database using AuthenticationUseCase
    - Generates JWT with user ID and organization context
    - Includes permissions claims from RBAC service
    - Captures client metadata (ip_address, user_agent)
    - Creates session in database for revocation capability
    - Returns standardized AuthResponseDTO
    - Handles errors gracefully without exposing sensitive data
    
    Args:
        dto: Login credentials (email/password) with optional remember_me flag
        request: FastAPI request object for extracting client information
        use_case: Authentication use case (injected dependency)
    
    Returns:
        AuthResponseDTO containing:
        - JWT access token with embedded permissions
        - User details (excluding sensitive fields)
        - Session information for tracking
        - Token metadata (expiration, type)
    
    Raises:
        HTTPException: 
        - 401 if credentials are invalid
        - 401 if user account is inactive/revoked
        - 400 if request data is malformed
        - 500 if internal authentication error occurs
    
    Security Notes:
    - JWT tokens are short-lived (15 minutes) to reduce exposure window
    - Permissions are embedded to reduce database queries
    - Session tracking enables token revocation
    - Client information is logged for security monitoring
    - RS256 algorithm provides stronger cryptographic security
    """
    try:
        # Extract client information for security tracking
        user_agent, ip_address = get_client_info(request)
        dto.user_agent = user_agent
        dto.ip_address = ip_address
        
        # Authenticate user and generate JWT with RBAC permissions
        # This internally:
        # 1. Validates credentials against database
        # 2. Retrieves user permissions via RBAC service
        # 3. Generates short-lived JWT token (15 minutes)
        # 4. Creates session for revocation capability
        # 5. Returns comprehensive authentication response
        return use_case.login(dto)
        
    except ValueError as e:
        # Handle authentication errors (invalid credentials, inactive user)
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
        # In production, this should be logged for monitoring
        print(f"Secure authentication error: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable",
        )


@router.post("/validate")
def validate_secure_token(
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """
    Validate a JWT token and return user information.
    
    This endpoint validates the JWT token and returns user details
    if the token is valid and not expired. It checks:
    - JWT signature and format
    - Token expiration
    - User still exists and is active
    - Session is still valid (for revocation support)
    
    Args:
        request: FastAPI request object containing Authorization header
        use_case: Authentication use case (injected dependency)
    
    Returns:
        User information if token is valid
    
    Raises:
        HTTPException:
        - 401 if Authorization header is missing or malformed
        - 401 if token is invalid, expired, or revoked
        - 401 if user is no longer active
    """
    try:
        # Extract JWT token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header with Bearer token required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]
        
        # Validate token and get user information
        # This internally:
        # 1. Decodes and validates JWT signature
        # 2. Checks token expiration
        # 3. Verifies user still exists and is active
        # 4. Validates session if available
        user = use_case.validate_session(token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or revoked token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "user": user,
            "token_valid": True,
            "message": "Token is valid"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        # Handle unexpected validation errors
        print(f"Token validation error: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=AuthResponseDTO)
def refresh_secure_token(
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """
    Refresh a JWT token with updated permissions.
    
    This endpoint generates a new JWT token with fresh permissions
    from the RBAC service. This is important for:
    - Maintaining short token lifespans
    - Ensuring permissions are up-to-date
    - Handling permission changes without re-login
    
    Args:
        request: FastAPI request object containing Authorization header
        use_case: Authentication use case (injected dependency)
    
    Returns:
        AuthResponseDTO with new JWT token and updated permissions
    
    Raises:
        HTTPException:
        - 401 if Authorization header is missing or malformed  
        - 401 if current token is invalid or expired
        - 401 if user is no longer active
    """
    try:
        # Extract current JWT token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header with Bearer token required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]
        
        # Refresh token with updated permissions
        # This internally:
        # 1. Validates current token
        # 2. Retrieves fresh user permissions
        # 3. Generates new JWT with updated data
        # 4. Creates new session and revokes old one
        result = use_case.refresh_session(token)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token - please login again",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        # Handle unexpected refresh errors
        print(f"Token refresh error: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh service temporarily unavailable",
        )