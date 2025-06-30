from typing import Optional
from uuid import UUID
import math

from shared.domain.repositories.unit_of_work import UnitOfWork

from ..dtos.membership_dto import (
    MembershipCreateDTO,
    MembershipUpdateDTO,
    MembershipResponseDTO,
    MembershipListResponseDTO,
    OwnershipTransferDTO,
    MembershipInviteDTO,
    UserOrganizationSummaryDTO,
    UserOrganizationsResponseDTO,
)
from ...domain.entities.user_organization_role import (
    OrganizationRole,
)
from ...domain.repositories.organization_repository import OrganizationRepository
from ...domain.repositories.user_organization_role_repository import (
    UserOrganizationRoleRepository,
)
from ...domain.services.organization_domain_service import OrganizationDomainService
from ...domain.services.membership_service import MembershipService


class MembershipUseCase:
    """Use cases for organization membership management."""

    def __init__(self, uow: UnitOfWork):
        self._organization_repository: OrganizationRepository = uow.get_repository("organization")
        self._role_repository: UserOrganizationRoleRepository = uow.get_repository("user_organization_role")
        self._organization_domain_service = OrganizationDomainService(uow)
        self._membership_service = MembershipService(uow)
        self._uow = uow

    def add_member(
        self, organization_id: UUID, dto: MembershipCreateDTO, assigned_by: UUID
    ) -> MembershipResponseDTO:
        """Add a user to an organization."""
        with self._uow:
            # Check if organization exists
            organization = self._organization_repository.get_by_id(organization_id)
            if not organization:
                raise ValueError("Organization not found")

            # Check if user can manage members
            assigner_role = self._role_repository.get_by_user_and_organization(
                assigned_by, organization_id
            )

            if not assigner_role or not assigner_role.can_manage_users():
                raise ValueError(
                    "User does not have permission to manage organization members"
                )

            # Validate user addition
            can_add, reason = self._organization_domain_service.validate_user_addition(
                organization_id, dto.role
            )

            if not can_add:
                raise ValueError(f"Cannot add user: {reason}")

            # Add user to organization
            role = self._membership_service.add_user_to_organization(
                user_id=dto.user_id,
                organization_id=organization_id,
                role=dto.role,
                assigned_by=assigned_by,
            )

        return MembershipResponseDTO(
            **role.model_dump(),
            user_name="User Name",  # Would fetch from user service
            user_email="user@example.com",  # Would fetch from user service
            organization_name=organization.name.value,
        )

    def update_member_role(
        self,
        organization_id: UUID,
        user_id: UUID,
        dto: MembershipUpdateDTO,
        updated_by: UUID,
    ) -> MembershipResponseDTO:
        """Update a member's role in an organization."""
        with self._uow:
            # Check if organization exists
            organization = self._organization_repository.get_by_id(organization_id)
            if not organization:
                raise ValueError("Organization not found")

            # Check permissions
            updater_role = self._role_repository.get_by_user_and_organization(
                updated_by, organization_id
            )

            if not updater_role or not updater_role.can_manage_users():
                raise ValueError(
                    "User does not have permission to manage organization members"
                )

            # Update role
            updated_role = self._membership_service.change_user_role(
                user_id=user_id,
                organization_id=organization_id,
                new_role=dto.role,
                changed_by=updated_by,
            )

        return MembershipResponseDTO(
            **updated_role.model_dump(),
            user_name="User Name",  # Would fetch from user service
            user_email="user@example.com",  # Would fetch from user service
            organization_name=organization.name.value,
        )

    def remove_member(
        self, organization_id: UUID, user_id: UUID, removed_by: UUID
    ) -> bool:
        """Remove a user from an organization."""
        with self._uow:
            # Check if organization exists
            organization = self._organization_repository.get_by_id(organization_id)
            if not organization:
                raise ValueError("Organization not found")

            # Check permissions (can remove others or themselves)
            remover_role = self._role_repository.get_by_user_and_organization(
                removed_by, organization_id
            )

            can_remove_others = remover_role and remover_role.can_manage_users()
            is_self_removal = removed_by == user_id

            if not can_remove_others and not is_self_removal:
                raise ValueError("User does not have permission to remove this member")

            # Check if user can leave organization
            if is_self_removal:
                can_leave, reason = (
                    self._organization_domain_service.can_user_leave_organization(
                        user_id, organization_id
                    )
                )

                if not can_leave:
                    raise ValueError(f"Cannot leave organization: {reason}")

            # Remove user from organization
            result = self._membership_service.remove_user_from_organization(
                user_id, organization_id
            )

        return result

    def get_organization_members(
        self, organization_id: UUID, page: int = 1, page_size: int = 100
    ) -> MembershipListResponseDTO:
        """Get paginated list of organization members."""

        if page < 1:
            page = 1

        if page_size < 1 or page_size > 1000:
            page_size = 100

        # Get organization to verify it exists
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Get all user roles in organization
        user_roles = self._role_repository.get_user_roles_in_organization(
            organization_id
        )

        # Filter active roles and paginate
        active_roles = [role for role in user_roles if role.is_valid()]
        total = len(active_roles)

        offset = (page - 1) * page_size
        paginated_roles = active_roles[offset : offset + page_size]

        # Convert to DTOs
        membership_dtos = []
        for role in paginated_roles:
            dto = MembershipResponseDTO(
                **role.model_dump(),
                user_name="User Name",  # Would fetch from user service
                user_email="user@example.com",  # Would fetch from user service
                organization_name=organization.name.value,
            )
            membership_dtos.append(dto)

        total_pages = math.ceil(total / page_size)

        return MembershipListResponseDTO(
            memberships=membership_dtos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_user_membership(
        self, user_id: UUID, organization_id: UUID
    ) -> Optional[MembershipResponseDTO]:
        """Get user's membership in a specific organization."""

        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            return None

        role = self._role_repository.get_by_user_and_organization(
            user_id, organization_id
        )

        if not role or not role.is_valid():
            return None

        return MembershipResponseDTO(
            **role.model_dump(),
            user_name="User Name",  # Would fetch from user service
            user_email="user@example.com",  # Would fetch from user service
            organization_name=organization.name.value,
        )

    def get_user_organizations(self, user_id: UUID) -> UserOrganizationsResponseDTO:
        """Get all organizations where user is a member."""

        user_roles = self._role_repository.get_user_organizations(user_id)

        organizations = []
        owned_count = 0

        for role in user_roles:
            if role.is_valid():
                organization = self._organization_repository.get_by_id(
                    role.organization_id
                )

                if organization:
                    member_count = self._role_repository.count_organization_users(
                        organization.id
                    )

                    is_owner = role.role == OrganizationRole.OWNER
                    if is_owner:
                        owned_count += 1

                    org_summary = UserOrganizationSummaryDTO(
                        organization_id=organization.id,
                        organization_name=organization.name.value,
                        role=role.role.value,
                        is_owner=is_owner,
                        joined_at=role.assigned_at,
                        member_count=member_count,
                        is_active=organization.is_active,
                    )
                    organizations.append(org_summary)

        return UserOrganizationsResponseDTO(
            organizations=organizations,
            total=len(organizations),
            owned_count=owned_count,
            member_count=len(organizations) - owned_count,
        )

    def transfer_ownership(
        self, organization_id: UUID, dto: OwnershipTransferDTO, current_owner_id: UUID
    ) -> MembershipResponseDTO:
        """Transfer organization ownership."""
        with self._uow:
            # Validate transfer
            can_transfer, reason = self._organization_domain_service.can_transfer_ownership(
                organization_id, current_owner_id, dto.new_owner_id
            )

            if not can_transfer:
                raise ValueError(f"Cannot transfer ownership: {reason}")

            # Perform transfer
            old_role, new_role = self._membership_service.transfer_ownership(
                organization_id, current_owner_id, dto.new_owner_id
            )

            # Get organization for response
            organization = self._organization_repository.get_by_id(organization_id)

        return MembershipResponseDTO(
            **new_role.model_dump(),
            user_name="New Owner Name",  # Would fetch from user service
            user_email="newowner@example.com",  # Would fetch from user service
            organization_name=organization.name.value,
        )

    def invite_user(
        self, organization_id: UUID, dto: MembershipInviteDTO, invited_by: UUID
    ) -> bool:
        """Invite a user to join an organization."""

        # Check if organization exists
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Check permissions
        inviter_role = self._role_repository.get_by_user_and_organization(
            invited_by, organization_id
        )

        if not inviter_role or not inviter_role.can_manage_users():
            raise ValueError("User does not have permission to invite members")

        # Validate user addition
        can_add, reason = self._organization_domain_service.validate_user_addition(
            organization_id, dto.role
        )

        if not can_add:
            raise ValueError(f"Cannot invite user: {reason}")

        # In a real implementation, this would:
        # 1. Create an invitation record
        # 2. Send an email invitation
        # 3. Generate invitation token

        return True

    def get_user_permissions(self, user_id: UUID, organization_id: UUID) -> list[str]:
        """Get user's permissions in an organization."""

        return self._membership_service.get_user_permissions_in_organization(
            user_id, organization_id
        )

    def check_user_permission(
        self, user_id: UUID, organization_id: UUID, action: str
    ) -> bool:
        """Check if user can perform specific action in organization."""

        return self._membership_service.can_user_perform_action(
            user_id, organization_id, action
        )
