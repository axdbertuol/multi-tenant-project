import time
from typing import List
from uuid import UUID

from ..entities.authorization_context import AuthorizationContext
from ..value_objects.authorization_decision import (
    AuthorizationDecision,
    DecisionReason,
)
from .rbac_service import RBACService
from .abac_service import ABACService


class AuthorizationService:
    """Main authorization service that combines RBAC and ABAC."""

    def __init__(self, rbac_service: RBACService, abac_service: ABACService):
        self._rbac_service = rbac_service
        self._abac_service = abac_service

    def authorize(self, context: AuthorizationContext) -> AuthorizationDecision:
        """Main authorization method combining RBAC and ABAC."""
        start_time = time.time()
        reasons: List[DecisionReason] = []

        try:
            # First try RBAC (faster)
            rbac_decision = self._rbac_service.authorize(context)
            reasons.extend(rbac_decision.reasons)

            if rbac_decision.is_allowed():
                # RBAC allows, check if there are any ABAC policies that deny
                abac_decision = self._abac_service.evaluate_policies(context)
                reasons.extend(abac_decision.reasons)

                if abac_decision.is_denied():
                    # ABAC explicitly denies
                    evaluation_time = (time.time() - start_time) * 1000
                    return AuthorizationDecision.deny(reasons, evaluation_time)

                # RBAC allows and ABAC doesn't deny
                evaluation_time = (time.time() - start_time) * 1000
                return AuthorizationDecision.allow(reasons, evaluation_time)

            # RBAC denies, check ABAC for potential allow
            abac_decision = self._abac_service.evaluate_policies(context)
            reasons.extend(abac_decision.reasons)

            if abac_decision.is_allowed():
                # ABAC explicitly allows despite RBAC denial
                evaluation_time = (time.time() - start_time) * 1000
                return AuthorizationDecision.allow(reasons, evaluation_time)

            # Both deny or are not applicable
            evaluation_time = (time.time() - start_time) * 1000

            # If we have explicit deny reasons, deny. Otherwise, default deny
            has_explicit_deny = any(
                reason.type in ["rbac_deny", "policy_deny"] for reason in reasons
            )

            if has_explicit_deny or reasons:
                return AuthorizationDecision.deny(reasons, evaluation_time)
            else:
                # No applicable rules found, default deny
                default_reason = DecisionReason(
                    type="default_deny",
                    message="No applicable authorization rules found",
                    details={
                        "resource_type": context.resource_type,
                        "action": context.action,
                        "user_id": str(context.user_id),
                    },
                )
                return AuthorizationDecision.deny([default_reason], evaluation_time)

        except Exception as e:
            # Authorization failure should default to deny
            evaluation_time = (time.time() - start_time) * 1000
            error_reason = DecisionReason(
                type="authorization_error",
                message=f"Authorization evaluation failed: {str(e)}",
                details={"error": str(e)},
            )
            return AuthorizationDecision.deny([error_reason], evaluation_time)

    def can_user_access_resource(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action: str,
        organization_id: UUID = None,
    ) -> bool:
        """Simplified method to check if user can access a resource."""
        context = AuthorizationContext.create(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            organization_id=organization_id,
        )

        decision = self.authorize(context)
        return decision.is_allowed()

    def get_user_permissions(
        self, user_id: UUID, organization_id: UUID = None
    ) -> List[str]:
        """Get all permissions for a user."""
        return self._rbac_service.get_user_permissions(user_id, organization_id)

    def check_multiple_permissions(
        self,
        user_id: UUID,
        resource_type: str,
        actions: List[str],
        organization_id: UUID = None,
        resource_id: UUID = None,
    ) -> dict[str, bool]:
        """Check multiple permissions at once for efficiency."""
        results = {}

        for action in actions:
            context = AuthorizationContext.create(
                user_id=user_id,
                resource_type=resource_type,
                action=action,
                organization_id=organization_id,
                resource_id=resource_id,
            )

            decision = self.authorize(context)
            results[action] = decision.is_allowed()

        return results
