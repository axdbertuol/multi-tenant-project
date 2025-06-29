from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from domain.entities.authorization_context import AuthorizationContext
from domain.entities.resource_permission import ResourcePermission, PermissionEffect, ContextCondition
from domain.entities.permission import Permission
from domain.entities.role import Role
from domain.repositories.unit_of_work import UnitOfWork
from domain.repositories.resource_permission_repository import ResourcePermissionRepository
from domain.repositories.resource_repository import ResourceRepository
from application.services.permission_service import PermissionService


class AuthorizationDecision:
    def __init__(self, allowed: bool, reason: str, applied_rules: List[str]):
        self.allowed = allowed
        self.reason = reason
        self.applied_rules = applied_rules


class ConditionEvaluator:
    """Evaluates ABAC conditions against authorization context"""
    
    @staticmethod
    def evaluate_condition(condition: ContextCondition, context: AuthorizationContext) -> bool:
        """Evaluate a single condition against the context"""
        actual_value = context.get_attribute(condition.attribute)
        expected_value = condition.value
        
        if actual_value is None:
            return False
            
        operator = condition.operator.lower()
        
        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "in":
            return actual_value in expected_value if isinstance(expected_value, (list, tuple, set)) else False
        elif operator == "not_in":
            return actual_value not in expected_value if isinstance(expected_value, (list, tuple, set)) else True
        elif operator == "contains":
            return expected_value in str(actual_value)
        elif operator == "not_contains":
            return expected_value not in str(actual_value)
        elif operator == "starts_with":
            return str(actual_value).startswith(str(expected_value))
        elif operator == "ends_with":
            return str(actual_value).endswith(str(expected_value))
        elif operator == "greater_than":
            try:
                return float(actual_value) > float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(actual_value) < float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "greater_equal":
            try:
                return float(actual_value) >= float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_equal":
            try:
                return float(actual_value) <= float(expected_value)
            except (ValueError, TypeError):
                return False
        else:
            return False
    
    @classmethod
    def evaluate_conditions(cls, conditions: List[ContextCondition], context: AuthorizationContext) -> bool:
        """Evaluate all conditions (AND logic)"""
        return all(cls.evaluate_condition(condition, context) for condition in conditions)


class HybridAuthorizationService:
    """
    Hybrid RBAC + ABAC authorization service
    
    Decision flow:
    1. Check role-based permissions (RBAC)
    2. Check resource-specific permissions (ABAC)
    3. Evaluate contextual conditions
    4. Apply priority and effect rules (ALLOW/DENY)
    """
    
    def __init__(self, uow: UnitOfWork, permission_service: PermissionService):
        self.uow = uow
        self.permission_service = permission_service
        self.condition_evaluator = ConditionEvaluator()

    async def is_authorized(
        self,
        context: AuthorizationContext,
        permission_name: str,
        resource_id: Optional[UUID] = None,
    ) -> AuthorizationDecision:
        """
        Main authorization method that combines RBAC and ABAC
        
        Args:
            context: Authorization context with user, resource, and environment info
            permission_name: Name of the permission to check (e.g., "read", "write", "delete")
            resource_id: Optional specific resource ID to check
            
        Returns:
            AuthorizationDecision with result and reasoning
        """
        async with self.uow:
            # Get the permission by name
            permission = await self.uow.permissions.find_by_name(permission_name)
            if not permission:
                return AuthorizationDecision(
                    allowed=False,
                    reason=f"Permission '{permission_name}' not found",
                    applied_rules=[]
                )

            # Step 1: Check basic RBAC permissions (role-based)
            rbac_decision = await self._check_rbac_permissions(context, permission)
            
            # Step 2: Check resource-specific permissions (ABAC)
            if resource_id:
                abac_decision = await self._check_abac_permissions(context, permission, resource_id)
                
                # Combine RBAC and ABAC decisions
                return self._combine_decisions(rbac_decision, abac_decision)
            else:
                # No specific resource, rely on RBAC only
                return rbac_decision

    async def _check_rbac_permissions(
        self,
        context: AuthorizationContext,
        permission: Permission,
    ) -> AuthorizationDecision:
        """Check traditional role-based permissions"""
        # Get all user permissions (from roles, groups, and direct assignments)
        user_permissions = await self.permission_service.get_all_user_permissions(context.user_id)
        
        # Check if user has the required permission
        has_permission = any(perm.name == permission.name for perm in user_permissions)
        
        if has_permission:
            return AuthorizationDecision(
                allowed=True,
                reason=f"User has role-based permission '{permission.name}'",
                applied_rules=["RBAC_ALLOW"]
            )
        else:
            return AuthorizationDecision(
                allowed=False,
                reason=f"User lacks role-based permission '{permission.name}'",
                applied_rules=["RBAC_DENY"]
            )

    async def _check_abac_permissions(
        self,
        context: AuthorizationContext,
        permission: Permission,
        resource_id: UUID,
    ) -> AuthorizationDecision:
        """Check attribute-based permissions for specific resources"""
        # Get user roles for role-based resource permissions
        user_roles = await self.permission_service.get_user_roles(context.user_id)
        user_role_ids = [role.id for role in await self._get_role_entities(user_roles)]
        
        # Get all applicable resource permissions
        resource_permissions = await self.uow.resource_permissions.find_effective_permissions(
            user_id=context.user_id,
            resource_id=resource_id,
            permission_id=permission.id,
            user_roles=user_role_ids,
        )
        
        if not resource_permissions:
            return AuthorizationDecision(
                allowed=False,
                reason=f"No resource-specific permissions found for resource {resource_id}",
                applied_rules=["ABAC_NO_RULES"]
            )
        
        # Evaluate each permission with its conditions
        applicable_permissions = []
        for res_perm in resource_permissions:
            if res_perm.conditions:
                # Evaluate ABAC conditions
                conditions_met = self.condition_evaluator.evaluate_conditions(res_perm.conditions, context)
                if conditions_met:
                    applicable_permissions.append(res_perm)
            else:
                # No conditions, permission applies
                applicable_permissions.append(res_perm)
        
        if not applicable_permissions:
            return AuthorizationDecision(
                allowed=False,
                reason="Resource permissions exist but conditions not met",
                applied_rules=["ABAC_CONDITIONS_NOT_MET"]
            )
        
        # Sort by priority (higher first) and apply effect logic
        applicable_permissions.sort(key=lambda p: p.priority, reverse=True)
        
        # Apply the highest priority rule
        highest_priority = applicable_permissions[0]
        
        if highest_priority.effect == PermissionEffect.ALLOW:
            return AuthorizationDecision(
                allowed=True,
                reason=f"Resource permission allows access (priority: {highest_priority.priority})",
                applied_rules=[f"ABAC_ALLOW_P{highest_priority.priority}"]
            )
        else:
            return AuthorizationDecision(
                allowed=False,
                reason=f"Resource permission denies access (priority: {highest_priority.priority})",
                applied_rules=[f"ABAC_DENY_P{highest_priority.priority}"]
            )

    def _combine_decisions(
        self,
        rbac_decision: AuthorizationDecision,
        abac_decision: AuthorizationDecision,
    ) -> AuthorizationDecision:
        """
        Combine RBAC and ABAC decisions
        
        Logic:
        - If ABAC explicitly denies, deny (ABAC override)
        - If ABAC allows, allow regardless of RBAC (resource-specific override)
        - If ABAC has no rules, fall back to RBAC
        """
        combined_rules = rbac_decision.applied_rules + abac_decision.applied_rules
        
        # ABAC DENY has highest priority
        if abac_decision.applied_rules and any("DENY" in rule for rule in abac_decision.applied_rules):
            return AuthorizationDecision(
                allowed=False,
                reason=f"ABAC DENY overrides RBAC: {abac_decision.reason}",
                applied_rules=combined_rules
            )
        
        # ABAC ALLOW overrides RBAC DENY
        if abac_decision.allowed:
            return AuthorizationDecision(
                allowed=True,
                reason=f"ABAC ALLOW: {abac_decision.reason}",
                applied_rules=combined_rules
            )
        
        # No specific ABAC rules or conditions not met, fall back to RBAC
        if "ABAC_NO_RULES" in abac_decision.applied_rules or "ABAC_CONDITIONS_NOT_MET" in abac_decision.applied_rules:
            return AuthorizationDecision(
                allowed=rbac_decision.allowed,
                reason=f"RBAC fallback: {rbac_decision.reason}",
                applied_rules=combined_rules
            )
        
        # Default to most restrictive
        return AuthorizationDecision(
            allowed=False,
            reason="Combined decision: access denied",
            applied_rules=combined_rules
        )

    async def _get_role_entities(self, role_names: List[str]) -> List[Role]:
        """Helper to get Role entities from role names"""
        roles = []
        for name in role_names:
            role = await self.uow.roles.find_by_name(name)
            if role:
                roles.append(role)
        return roles

    async def get_accessible_resources(
        self,
        context: AuthorizationContext,
        permission_name: str,
        resource_type: Optional[str] = None,
    ) -> List[UUID]:
        """Get list of resource IDs that user can access with given permission"""
        async with self.uow:
            permission = await self.uow.permissions.find_by_name(permission_name)
            if not permission:
                return []
            
            # Get all resources (optionally filtered by type)
            if resource_type:
                from domain.entities.resource import ResourceType
                resources = await self.uow.resources.find_by_type(ResourceType(resource_type))
            else:
                resources = await self.uow.resources.find_active_resources()
            
            accessible_resources = []
            for resource in resources:
                decision = await self.is_authorized(
                    context.with_resource_attributes(**resource.metadata),
                    permission_name,
                    resource.id
                )
                if decision.allowed:
                    accessible_resources.append(resource.id)
            
            return accessible_resources