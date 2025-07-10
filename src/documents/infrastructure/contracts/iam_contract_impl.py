"""IAM Contract implementation for Documents context."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ...application.contracts.iam_contract import (
    IAMContract, 
    UserInfo,
    ManagementFunctionInfo,
    UserManagementAssignment,
)
from src.iam.infrastructure.iam_unit_of_work import IAMUnitOfWork


class IAMContractImpl(IAMContract):
    """
    Implementation of IAM Contract that integrates with the existing IAM context.
    
    This implementation provides real integration with the IAM bounded context
    through its Unit of Work and repositories.
    """

    def __init__(self, iam_uow: IAMUnitOfWork):
        self.iam_uow = iam_uow

    def get_user_info(self, user_id: UUID) -> Optional[UserInfo]:
        """Get user information by ID."""
        try:
            with self.iam_uow:
                user_repo = self.iam_uow.get_repository("user")
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    return None

                # Get user's primary organization (first active membership)
                user_org_role_repo = self.iam_uow.get_repository("user_organization_role")
                user_org_roles = user_org_role_repo.get_by_user(user_id)
                
                primary_org_id = None
                if user_org_roles:
                    active_roles = [role for role in user_org_roles if role.is_active]
                    if active_roles:
                        primary_org_id = active_roles[0].organization_id

                return UserInfo(
                    id=user.id,
                    email=user.email.value,
                    name=user.full_name,
                    organization_id=primary_org_id,
                    is_active=user.is_active,
                )
        except Exception:
            return None

    def verify_user_active(self, user_id: UUID, organization_id: UUID) -> bool:
        """Verify if user is active in the organization."""
        try:
            with self.iam_uow:
                user_org_role_repo = self.iam_uow.get_repository("user_organization_role")
                user_org_roles = user_org_role_repo.get_by_user_and_organization(
                    user_id, organization_id
                )
                
                # Check if user has any active role in the organization
                active_roles = [role for role in user_org_roles if role.is_active]
                return len(active_roles) > 0
        except Exception:
            return False

    def get_management_function_info(self, function_id: UUID) -> Optional[ManagementFunctionInfo]:
        """Get management function information by ID."""
        # TODO: Implement when management functions are defined in IAM context
        # For now, return a placeholder
        return None

    def get_user_management_assignment(
        self, user_id: UUID, organization_id: UUID
    ) -> Optional[UserManagementAssignment]:
        """Get user's management function assignment for an organization."""
        try:
            with self.iam_uow:
                user_org_role_repo = self.iam_uow.get_repository("user_organization_role")
                user_org_roles = user_org_role_repo.get_by_user_and_organization(
                    user_id, organization_id
                )
                
                if not user_org_roles:
                    return None

                # Find the most privileged active role
                active_roles = [role for role in user_org_roles if role.is_active]
                if not active_roles:
                    return None

                # Get role details for the most recent assignment
                role_repo = self.iam_uow.get_repository("role")
                primary_role = active_roles[0]
                role = role_repo.get_by_id(primary_role.role_id)
                
                if not role:
                    return None

                # Get role permissions
                permissions = []
                # TODO: Implement permission retrieval when role-permission mapping is available
                
                return UserManagementAssignment(
                    user_id=user_id,
                    organization_id=organization_id,
                    function_id=role.id,
                    function_name=role.name.value,
                    permissions=permissions,
                    assigned_at=primary_role.assigned_at,
                    is_active=primary_role.is_active,
                )
        except Exception:
            return None

    def verify_management_permission(
        self, user_id: UUID, organization_id: UUID, permission: str
    ) -> bool:
        """Verify if user has a specific management permission."""
        try:
            with self.iam_uow:
                user_org_role_repo = self.iam_uow.get_repository("user_organization_role")
                role_repo = self.iam_uow.get_repository("role")
                
                user_org_roles = user_org_role_repo.get_by_user_and_organization(
                    user_id, organization_id
                )
                
                active_roles = [role for role in user_org_roles if role.is_active]
                if not active_roles:
                    return False

                # Check if any of the user's roles grants the permission
                for user_role in active_roles:
                    role = role_repo.get_by_id(user_role.role_id)
                    if role and role.name.value in ["admin", "owner", "manager"]:
                        # Grant broad permissions to administrative roles
                        return True
                    
                    # TODO: Implement detailed permission checking when role-permission system is available
                    
                return False
        except Exception:
            return False

    def get_organization_users(self, organization_id: UUID) -> List[UserInfo]:
        """Get all users in an organization."""
        try:
            with self.iam_uow:
                user_org_role_repo = self.iam_uow.get_repository("user_organization_role")
                user_repo = self.iam_uow.get_repository("user")
                
                user_org_roles = user_org_role_repo.get_by_organization(organization_id)
                
                users = []
                seen_user_ids = set()
                
                for user_role in user_org_roles:
                    if not user_role.is_active or user_role.user_id in seen_user_ids:
                        continue
                        
                    user = user_repo.get_by_id(user_role.user_id)
                    if user and user.is_active:
                        users.append(UserInfo(
                            id=user.id,
                            email=user.email.value,
                            name=user.full_name,
                            organization_id=organization_id,
                            is_active=user.is_active,
                        ))
                        seen_user_ids.add(user.id)
                
                return users
        except Exception:
            return []

    def verify_organization_access(self, user_id: UUID, organization_id: UUID) -> bool:
        """Verify if user has access to an organization."""
        return self.verify_user_active(user_id, organization_id)