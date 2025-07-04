from typing import List
from uuid import UUID

from ..entities.user_organization_role import UserOrganizationRole, OrganizationRole
from ..repositories.user_organization_role_repository import (
    UserOrganizationRoleRepository,
)
from ..repositories.organization_repository import OrganizationRepository


class MembershipService:
    """Domain service for organization membership logic."""

    def __init__(
        self,
        role_repository: UserOrganizationRoleRepository,
        organization_repository: OrganizationRepository,
    ):
        self._role_repository = role_repository
        self._organization_repository = organization_repository

    def add_user_to_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
        role: OrganizationRole,
        assigned_by: UUID,
    ) -> UserOrganizationRole:
        """Add user to organization with specified role."""
        # Check if user already has a role in this organization
        existing_role = self._role_repository.get_by_user_and_organization(
            user_id, organization_id
        )

        if existing_role and existing_role.is_valid():
            raise ValueError("User already has an active role in this organization")

        # Create new role assignment
        new_role = UserOrganizationRole.create(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            assigned_by=assigned_by,
        )

        return self._role_repository.save(new_role)

    def change_user_role(
        self,
        user_id: UUID,
        organization_id: UUID,
        new_role: OrganizationRole,
        changed_by: UUID,
    ) -> UserOrganizationRole:
        """Change user's role in organization."""
        current_role = self._role_repository.get_by_user_and_organization(
            user_id, organization_id
        )

        if not current_role or not current_role.is_valid():
            raise ValueError("User does not have an active role in this organization")

        # Prevent changing owner role without proper transfer
        if current_role.role == OrganizationRole.OWNER:
            raise ValueError(
                "Cannot change owner role. Use ownership transfer instead."
            )

        updated_role = current_role.change_role(new_role, changed_by)
        return self._role_repository.save(updated_role)

    def remove_user_from_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> bool:
        """Remove user from organization."""
        # Check if user is organization owner
        organization = self._organization_repository.get_by_id(organization_id)

        if organization and organization.is_owner(user_id):
            raise ValueError(
                "Cannot remove organization owner. Transfer ownership first."
            )

        return self._role_repository.remove_user_from_organization(
            user_id, organization_id
        )

    def get_user_permissions_in_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> List[str]:
        """Get list of permissions user has in organization."""
        role = self._role_repository.get_by_user_and_organization(
            user_id, organization_id
        )

        if not role or not role.is_valid():
            return []

        # Define permissions based on role
        permissions_map = {
            OrganizationRole.OWNER: [
                "manage_organization",
                "manage_users",
                "manage_roles",
                "view_analytics",
                "manage_settings",
                "delete_organization",
                "transfer_ownership",
            ],
            OrganizationRole.ADMIN: [
                "manage_users",
                "manage_roles",
                "view_analytics",
                "manage_settings",
            ],
            OrganizationRole.MEMBER: ["view_organization", "use_features"],
            OrganizationRole.VIEWER: ["view_organization"],
        }

        return permissions_map.get(role.role, [])

    def can_user_perform_action(
        self, user_id: UUID, organization_id: UUID, action: str
    ) -> bool:
        """Check if user can perform specific action in organization."""
        permissions = self.get_user_permissions_in_organization(
            user_id, organization_id
        )
        return action in permissions

    def transfer_ownership(
        self, organization_id: UUID, current_owner_id: UUID, new_owner_id: UUID
    ) -> tuple[UserOrganizationRole, UserOrganizationRole]:
        """Transfer organization ownership."""
        # Get current owner role
        owner_role = self._role_repository.get_by_user_and_organization(
            current_owner_id, organization_id
        )

        if not owner_role or owner_role.role != OrganizationRole.OWNER:
            raise ValueError("Current user is not the organization owner")

        # Get new owner's current role
        new_owner_role = self._role_repository.get_by_user_and_organization(
            new_owner_id, organization_id
        )

        if not new_owner_role or not new_owner_role.is_valid():
            raise ValueError("New owner must be an active member of the organization")

        # Update organization owner
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Organization not found")

        updated_organization = organization.transfer_ownership(new_owner_id)
        self._organization_repository.save(updated_organization)

        # Change roles
        demoted_owner = owner_role.change_role(OrganizationRole.ADMIN, new_owner_id)
        promoted_owner = new_owner_role.change_role(
            OrganizationRole.OWNER, current_owner_id
        )

        # Save role changes
        self._role_repository.save(demoted_owner)
        self._role_repository.save(promoted_owner)

        return demoted_owner, promoted_owner
