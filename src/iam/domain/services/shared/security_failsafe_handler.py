"""Security failsafe handler for IAM services."""

import logging
from typing import Optional, Any, Callable, TypeVar
from functools import wraps

from ...value_objects.authorization_decision import AuthorizationDecision, DecisionReason

T = TypeVar('T')
logger = logging.getLogger(__name__)


class SecurityFailsafeHandler:
    """Handler for security-related error patterns with fail-safe defaults."""

    @staticmethod
    def with_security_failsafe(
        operation: Callable[[], T],
        default_value: T,
        operation_name: str,
        log_errors: bool = True
    ) -> T:
        """
        Execute operation with security failsafe - returns secure default on error.
        
        Used in: AuthenticationService, AuthorizationService, RBACService
        """
        try:
            return operation()
        except Exception as e:
            if log_errors:
                logger.error(
                    f"Security operation '{operation_name}' failed: {str(e)}",
                    exc_info=True
                )
            return default_value

    @staticmethod
    def with_authorization_failsafe(
        operation: Callable[[], AuthorizationDecision],
        operation_name: str,
        context_details: Optional[dict] = None
    ) -> AuthorizationDecision:
        """
        Execute authorization operation with failsafe - returns DENY on error.
        
        Used in: AuthorizationService, ABACService, RBACService
        """
        try:
            return operation()
        except Exception as e:
            logger.error(
                f"Authorization operation '{operation_name}' failed: {str(e)}",
                exc_info=True,
                extra={"context": context_details}
            )
            
            error_reason = DecisionReason(
                type="authorization_error",
                message=f"Authorization failed: {operation_name}",
                details={
                    "error": str(e),
                    "operation": operation_name,
                    **(context_details or {})
                }
            )
            return AuthorizationDecision.deny([error_reason])

    @staticmethod
    def with_authentication_failsafe(
        operation: Callable[[], Optional[Any]],
        operation_name: str,
        user_identifier: Optional[str] = None
    ) -> Optional[Any]:
        """
        Execute authentication operation with failsafe - returns None on error.
        
        Used in: AuthenticationService, JWTService
        """
        try:
            return operation()
        except Exception as e:
            logger.warning(
                f"Authentication operation '{operation_name}' failed: {str(e)}",
                extra={
                    "user_identifier": user_identifier,
                    "operation": operation_name
                }
            )
            return None

    @staticmethod
    def with_bool_failsafe(
        operation: Callable[[], bool],
        operation_name: str,
        default_value: bool = False,
        log_level: str = "warning"
    ) -> bool:
        """
        Execute boolean operation with failsafe - returns secure default on error.
        
        Used in: MembershipService, DocumentAuthorizationService
        """
        try:
            return operation()
        except Exception as e:
            log_func = getattr(logger, log_level, logger.warning)
            log_func(
                f"Boolean operation '{operation_name}' failed: {str(e)}",
                extra={"operation": operation_name}
            )
            return default_value

    @staticmethod
    def with_list_failsafe(
        operation: Callable[[], list],
        operation_name: str,
        default_value: Optional[list] = None
    ) -> list:
        """
        Execute list operation with failsafe - returns empty list on error.
        
        Used in: RBACService, RoleInheritanceService
        """
        try:
            return operation()
        except Exception as e:
            logger.warning(
                f"List operation '{operation_name}' failed: {str(e)}",
                extra={"operation": operation_name}
            )
            return default_value or []

    @staticmethod
    def audit_security_event(
        event_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        details: Optional[dict] = None,
        success: bool = True
    ) -> None:
        """
        Audit security events with standardized logging.
        
        Used in: AuthenticationService, AuthorizationService, ABACService
        """
        audit_data = {
            "event_type": event_type,
            "user_id": user_id,
            "resource_id": resource_id,
            "organization_id": organization_id,
            "success": success,
            "details": details or {}
        }
        
        log_level = "info" if success else "warning"
        log_func = getattr(logger, log_level)
        
        log_func(
            f"Security audit: {event_type}",
            extra={"audit": audit_data}
        )


def security_failsafe(
    default_value: Any = None,
    operation_name: Optional[str] = None,
    log_errors: bool = True
):
    """
    Decorator for security failsafe operations.
    
    Usage:
        @security_failsafe(default_value=False, operation_name="check_permission")
        def risky_permission_check(self) -> bool:
            # operation that might fail
            return some_operation()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__name__}"
            return SecurityFailsafeHandler.with_security_failsafe(
                lambda: func(*args, **kwargs),
                default_value,
                op_name,
                log_errors
            )
        return wrapper
    return decorator


def authorization_failsafe(operation_name: Optional[str] = None):
    """
    Decorator for authorization operations that should fail safely to DENY.
    
    Usage:
        @authorization_failsafe(operation_name="rbac_check")
        def authorize_request(self, context) -> AuthorizationDecision:
            # operation that might fail
            return some_authorization_check()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__name__}"
            return SecurityFailsafeHandler.with_authorization_failsafe(
                lambda: func(*args, **kwargs),
                op_name
            )
        return wrapper
    return decorator