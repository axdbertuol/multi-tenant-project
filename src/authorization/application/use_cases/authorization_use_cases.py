from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...domain.entities.authorization_context import AuthorizationContext
from ...domain.services.authorization_service import AuthorizationService
from ...domain.repositories.role_repository import RoleRepository
from ...domain.repositories.policy_repository import PolicyRepository
from ..dtos.authorization_dto import (
    AuthorizationRequestDTO,
    AuthorizationResponseDTO,
    BulkAuthorizationRequestDTO,
    BulkAuthorizationResponseDTO,
    UserPermissionsResponseDTO,
    RoleAssignmentDTO,
)


class AuthorizationUseCase:
    """Use case for authorization operations."""

    def __init__(
        self,
        authorization_service: AuthorizationService,
        role_repository: RoleRepository,
        policy_repository: PolicyRepository,
    ):
        self.authorization_service = authorization_service
        self.role_repository = role_repository
        self.policy_repository = policy_repository

    def check_authorization(
        self, request_dto: AuthorizationRequestDTO
    ) -> AuthorizationResponseDTO:
        """Check if a user is authorized to perform an action."""
        start_time = datetime.now(timezone.utc)

        # Create authorization context
        context = AuthorizationContext(
            user_id=request_dto.user_id,
            organization_id=request_dto.organization_id,
            resource_id=request_dto.resource_id,
            resource_type=request_dto.resource_type,
            action=request_dto.action,
            user_attributes=request_dto.user_attributes,
            resource_attributes=request_dto.resource_attributes,
            environment_attributes=request_dto.environment_attributes,
        )

        # Perform authorization check
        is_authorized, decision_info = self.authorization_service.is_authorized(context)

        end_time = datetime.now(timezone.utc)
        evaluation_time_ms = (end_time - start_time).total_seconds() * 1000

        return AuthorizationResponseDTO(
            user_id=request_dto.user_id,
            resource_type=request_dto.resource_type,
            action=request_dto.action,
            is_authorized=is_authorized,
            decision_reason=decision_info.get("reason", ""),
            rbac_result=decision_info.get("rbac_result"),
            abac_result=decision_info.get("abac_result"),
            applicable_roles=decision_info.get("roles", []),
            applicable_policies=decision_info.get("policies", []),
            evaluation_time_ms=evaluation_time_ms,
            evaluated_at=end_time,
        )

    def bulk_check_authorization(
        self, request_dto: BulkAuthorizationRequestDTO
    ) -> BulkAuthorizationResponseDTO:
        """Check authorization for multiple requests."""
        results = []

        for request in request_dto.requests:
            result = self.check_authorization(request)
            results.append(result)

        # Calculate summary statistics
        authorized_count = sum(1 for r in results if r.is_authorized)
        total_evaluation_time = sum(r.evaluation_time_ms for r in results)

        return BulkAuthorizationResponseDTO(
            results=results,
            total_requests=len(results),
            authorized_count=authorized_count,
            denied_count=len(results) - authorized_count,
            total_evaluation_time_ms=total_evaluation_time,
        )

    def get_user_permissions(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
    ) -> UserPermissionsResponseDTO:
        """Get all permissions for a user."""
        # Get user roles
        user_roles = self.role_repository.find_user_roles(user_id, organization_id)

        # Get permissions from roles
        all_permissions = []
        role_names = []

        for role in user_roles:
            role_names.append(role.name)
            role_permissions = self.role_repository.get_role_permissions(role.id)

            for permission in role_permissions:
                if resource_type is None or permission.resource_type == resource_type:
                    all_permissions.append(
                        {
                            "id": str(permission.id),
                            "name": permission.name,
                            "resource_type": permission.resource_type,
                            "permission_type": permission.permission_type,
                            "full_name": permission.full_name,
                            "source_role": role.name,
                        }
                    )

        # Remove duplicates while preserving source role info
        unique_permissions = {}
        for perm in all_permissions:
            key = f"{perm['resource_type']}:{perm['permission_type']}"
            if key not in unique_permissions:
                unique_permissions[key] = perm
            else:
                # Merge source roles
                existing_roles = unique_permissions[key].get(
                    "source_roles", [unique_permissions[key]["source_role"]]
                )
                if perm["source_role"] not in existing_roles:
                    existing_roles.append(perm["source_role"])
                unique_permissions[key]["source_roles"] = existing_roles
                del unique_permissions[key]["source_role"]

        return UserPermissionsResponseDTO(
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            roles=role_names,
            permissions=list(unique_permissions.values()),
            permission_count=len(unique_permissions),
        )

    def assign_role_to_user(self, assignment_dto: RoleAssignmentDTO) -> bool:
        """Assign a role to a user."""
        # Validate role exists
        role = self.role_repository.find_by_id(assignment_dto.role_id)
        if not role:
            raise ValueError("Role not found")

        # Check organization scope
        if (
            role.organization_id
            and role.organization_id != assignment_dto.organization_id
        ):
            raise ValueError("Role does not belong to the specified organization")

        # Assign role
        self.role_repository.assign_role_to_user(
            user_id=assignment_dto.user_id,
            role_id=assignment_dto.role_id,
            organization_id=assignment_dto.organization_id,
            assigned_by=assignment_dto.assigned_by,
            expires_at=assignment_dto.expires_at,
        )

        return True

    def remove_role_from_user(
        self, user_id: UUID, role_id: UUID, organization_id: Optional[UUID] = None
    ) -> bool:
        """Remove a role from a user."""
        return self.role_repository.remove_role_from_user(
            user_id=user_id, role_id=role_id, organization_id=organization_id
        )

    def get_user_roles(
        self, user_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get all roles assigned to a user."""
        roles = self.role_repository.find_user_roles(user_id, organization_id)

        return [
            {
                "id": str(role.id),
                "name": role.name,
                "description": role.description,
                "organization_id": str(role.organization_id)
                if role.organization_id
                else None,
                "is_system_role": role.is_system_role,
                "created_at": role.created_at.isoformat(),
            }
            for role in roles
        ]

    def check_user_has_permission(
        self,
        user_id: UUID,
        permission_name: str,
        resource_type: str,
        organization_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a user has a specific permission."""
        context = AuthorizationContext(
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            action=permission_name,
        )

        is_authorized, _ = self.authorization_service.is_authorized(context)
        return is_authorized

    def get_resource_policies(
        self,
        resource_type: str,
        action: Optional[str] = None,
        organization_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Get all policies applicable to a resource type."""
        if action:
            policies = self.policy_repository.find_by_resource_and_action(
                resource_type, action, organization_id
            )
        else:
            policies = self.policy_repository.find_by_resource_type(
                resource_type, organization_id
            )

        return [
            {
                "id": str(policy.id),
                "name": policy.name,
                "description": policy.description,
                "effect": policy.effect,
                "resource_type": policy.resource_type,
                "action": policy.action,
                "conditions": [
                    condition.model_dump() for condition in policy.conditions
                ],
                "priority": policy.priority,
                "is_active": policy.is_active,
            }
            for policy in policies
        ]
