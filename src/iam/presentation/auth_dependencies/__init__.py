"""JWT and authentication dependencies."""

from .jwt_dependencies import (
    JWTAuthenticationContext,
    extract_bearer_token,
    get_jwt_service,
    get_jwt_payload,
    get_jwt_auth_context,
    get_current_user_from_jwt,
    require_organization_context,
    require_permission,
    require_role,
    require_any_permission,
    require_all_permissions,
    CurrentUser,
    JWTAuth,
    JWTAuthWithOrg,
)

__all__ = [
    "JWTAuthenticationContext",
    "extract_bearer_token",
    "get_jwt_service",
    "get_jwt_payload",
    "get_jwt_auth_context",
    "get_current_user_from_jwt",
    "require_organization_context",
    "require_permission",
    "require_role",
    "require_any_permission",
    "require_all_permissions",
    "CurrentUser",
    "JWTAuth",
    "JWTAuthWithOrg",
]