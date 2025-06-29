from typing import Optional, List
from uuid import UUID

from ..entities.organization import Organization
from ..entities.user_organization_role import UserOrganizationRole, OrganizationRole
from ..value_objects.organization_name import OrganizationName
from ..repositories.organization_repository import OrganizationRepository
from ..repositories.user_organization_role_repository import (
    UserOrganizationRoleRepository,
)


class OrganizationDomainService:
    """Domain service for organization-specific business logic."""

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        role_repository: UserOrganizationRoleRepository,
    ):
        self._organization_repository = organization_repository
        self._role_repository = role_repository

    def is_organization_name_available(
        self, name: OrganizationName, excluding_org_id: Optional[UUID] = None
    ) -> bool:
        """Check if organization name is available."""
        existing_org = self._organization_repository.get_by_name(name)

        if not existing_org:
            return True

        # If excluding a specific org (for updates), check if it's the same org
        if excluding_org_id and existing_org.id == excluding_org_id:
            return True

        return False

    def can_organization_be_deleted(self, organization_id: UUID) -> tuple[bool, str]:
        """Check if organization can be safely deleted."""
        organization = self._organization_repository.get_by_id(organization_id)

        if not organization:
            return False, "Organization not found"

        # Check if organization has active members
        user_count = self._role_repository.count_organization_users(organization_id)

        if user_count > 1:  # Owner + other members
            return (
                False,
                f"Organization has {user_count} active members and cannot be deleted",
            )

        return True, "Can be deleted"

    def can_user_leave_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> tuple[bool, str]:
        """Check if user can leave organization."""
        organization = self._organization_repository.get_by_id(organization_id)

        if not organization:
            return False, "Organization not found"

        # Owner cannot leave organization
        if organization.is_owner(user_id):
            return False, "Organization owner cannot leave. Transfer ownership first."

        user_role = self._role_repository.get_by_user_and_organization(
            user_id, organization_id
        )

        if not user_role:
            return False, "User is not a member of this organization"

        return True, "User can leave organization"

    def can_transfer_ownership(
        self, organization_id: UUID, current_owner_id: UUID, new_owner_id: UUID
    ) -> tuple[bool, str]:
        """Check if ownership can be transferred."""
        organization = self._organization_repository.get_by_id(organization_id)

        if not organization:
            return False, "Organization not found"

        if not organization.is_owner(current_owner_id):
            return False, "Only organization owner can transfer ownership"

        # Check if new owner is a member of the organization
        new_owner_role = self._role_repository.get_by_user_and_organization(
            new_owner_id, organization_id
        )

        if not new_owner_role or not new_owner_role.is_valid():
            return False, "New owner must be an active member of the organization"

        return True, "Ownership can be transferred"

    def validate_user_addition(
        self, organization_id: UUID, role: OrganizationRole
    ) -> tuple[bool, str]:
        """Validate if a new user can be added to organization."""
        organization = self._organization_repository.get_by_id(organization_id)

        if not organization:
            return False, "Organization not found"

        if not organization.is_active:
            return False, "Cannot add users to inactive organization"

        current_user_count = self._role_repository.count_organization_users(
            organization_id
        )

        if not organization.can_add_users(current_user_count):
            return (
                False,
                f"Organization has reached maximum user limit of {organization.settings.max_users}",
            )

        return True, "User can be added to organization"
