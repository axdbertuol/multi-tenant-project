from typing import List
from uuid import UUID

from ..entities.user import User
from ..repositories.user_repository import UserRepository
from ..repositories.organization_repository import OrganizationRepository
from ..repositories.role_repository import RoleRepository
from shared.domain.repositories.unit_of_work import UnitOfWork


class MembershipService:
    """Domain service for organization membership logic."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._organization_repository: OrganizationRepository = uow.get_repository(
            "organization"
        )
        self._role_repository: RoleRepository = uow.get_repository("role")
        self._uow = uow

    def add_user_to_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
        role: str,
        assigned_by: UUID,
    ) -> User:
        """Add user to organization with specified role."""
        # Get user and validate
        user = self._user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Check if user already belongs to an organization
        if user.organization_id is not None:
            raise ValueError("User already belongs to an organization")

        # Get organization and validate
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Add user to organization
        updated_user = user.join_organization(organization_id)
        self._user_repository.save(updated_user)

        # Add role assignment to user_role_assignment table
        # Find the role by name in the organization
        org_roles = self._role_repository.get_organization_roles(organization_id)
        role_to_assign = None
        for r in org_roles:
            if r.name.value == role:
                role_to_assign = r
                break

        if role_to_assign:
            self._role_repository.assign_role_to_user(
                user_id=user_id, role_id=role_to_assign.id, assigned_by=assigned_by
            )

        return updated_user

    def change_user_role(
        self,
        user_id: UUID,
        organization_id: UUID,
        new_role: str,
        changed_by: UUID,
    ) -> bool:
        """Change user's role in organization."""
        # Get user and validate membership
        user = self._user_repository.get_by_id(user_id)
        if not user or user.organization_id != organization_id:
            raise ValueError("User is not a member of this organization")

        # Get organization and validate
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Prevent changing owner role without proper transfer
        if organization.owner_id == user_id:
            raise ValueError(
                "Cannot change owner role. Use ownership transfer instead."
            )

        # Update role assignment in user_role_assignment table
        # First remove existing roles for this user
        self._role_repository.remove_all_user_roles(user_id)

        # Add new role
        org_roles = self._role_repository.get_organization_roles(organization_id)
        role_to_assign = None
        for r in org_roles:
            if r.name.value == new_role:
                role_to_assign = r
                break

        if role_to_assign:
            self._role_repository.assign_role_to_user(
                user_id=user_id, role_id=role_to_assign.id, assigned_by=changed_by
            )

        return True

    def remove_user_from_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> bool:
        """Remove user from organization."""
        # Get user and validate membership
        user = self._user_repository.get_by_id(user_id)
        if not user or user.organization_id != organization_id:
            raise ValueError("User is not a member of this organization")

        # Check if user is organization owner
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Organization not found")

        if organization.is_owner(user_id):
            raise ValueError(
                "Cannot remove organization owner. Transfer ownership first."
            )

        # Remove user from organization
        updated_user = user.leave_organization()
        self._user_repository.save(updated_user)

        # Remove role assignments from user_role_assignment table
        self._role_repository.remove_all_user_roles(user_id)

        return True

    def get_user_permissions_in_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> List[str]:
        """Get list of permissions user has in organization."""
        # Get user and validate membership
        user = self._user_repository.get_by_id(user_id)
        if not user or user.organization_id != organization_id:
            return []

        # Get organization
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            return []

        # Check if user is owner
        if organization.is_owner(user_id):
            return [
                "manage_organization",
                "manage_users",
                "manage_roles",
                "view_analytics",
                "manage_settings",
                "delete_organization",
                "transfer_ownership",
            ]

        # Get user's roles from user_role_assignment table
        user_roles = self._role_repository.get_user_roles_in_organization(
            user_id, organization_id
        )

        # Define permissions based on roles
        permissions = ["view_organization", "use_features"]  # Basic permissions

        for role in user_roles:
            if role.name.value == "admin":
                permissions.extend(
                    [
                        "manage_users",
                        "manage_roles",
                        "view_analytics",
                        "manage_settings",
                    ]
                )
            elif role.name.value == "moderator":
                permissions.extend(["manage_users", "view_analytics"])

        if not user_roles:
            # No roles assigned, return basic permissions
            return ["view_organization", "use_features"]

    def can_user_perform_action(
        self, user_id: UUID, organization_id: UUID, action: str
    ) -> bool:
        """Check if user can perform specific action in organization."""
        permissions = self.get_user_permissions_in_organization(
            user_id, organization_id
        )
        return action in permissions

    def get_user_roles_in_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> List[str]:
        """Get list of roles user has in organization."""
        # Get user and validate membership
        user = self._user_repository.get_by_id(user_id)
        if not user or user.organization_id != organization_id:
            return []

        # Get organization
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            return []

        # Check if user is owner
        if organization.is_owner(user_id):
            return ["owner"]

        # Get user's roles from user_role_assignment table
        user_roles = self._role_repository.get_user_roles_in_organization(
            user_id, organization_id
        )
        role_names = [role.name.value for role in user_roles]

        if not role_names:
            # No roles assigned, return basic member role
            return ["member"]

    def transfer_ownership(
        self, organization_id: UUID, current_owner_id: UUID, new_owner_id: UUID
    ) -> bool:
        """Transfer organization ownership."""
        # Get organization
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Validate current owner
        if not organization.is_owner(current_owner_id):
            raise ValueError("Current user is not the organization owner")

        # Get new owner and validate membership
        new_owner = self._user_repository.get_by_id(new_owner_id)
        if not new_owner or new_owner.organization_id != organization_id:
            raise ValueError("New owner must be an active member of the organization")

        # Update organization owner
        updated_organization = organization.transfer_ownership(new_owner_id)
        self._organization_repository.save(updated_organization)

        # Update role assignments in user_role_assignment table
        # Remove all roles from current owner
        self._role_repository.remove_all_user_roles(current_owner_id)

        # Remove all roles from new owner
        self._role_repository.remove_all_user_roles(new_owner_id)

        # Find owner and admin roles
        org_roles = self._role_repository.get_organization_roles(organization_id)
        owner_role = None
        admin_role = None

        for role in org_roles:
            if role.name.value == "owner":
                owner_role = role
            elif role.name.value == "admin":
                admin_role = role

        # Assign owner role to new owner
        if owner_role:
            self._role_repository.assign_role_to_user(
                user_id=new_owner_id,
                role_id=owner_role.id,
                assigned_by=current_owner_id,
            )

        # Assign admin role to demoted owner
        if admin_role:
            self._role_repository.assign_role_to_user(
                user_id=current_owner_id,
                role_id=admin_role.id,
                assigned_by=new_owner_id,
            )

        return True
