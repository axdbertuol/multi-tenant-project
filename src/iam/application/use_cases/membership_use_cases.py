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
from ...domain.repositories.organization_repository import OrganizationRepository
from ...domain.repositories.user_repository import UserRepository
from ...domain.services.organization_domain_service import OrganizationDomainService
from ...domain.services.membership_service import MembershipService


class MembershipUseCase:
    """Use cases for organization membership management."""

    def __init__(self, uow: UnitOfWork):
        self._organization_repository: OrganizationRepository = uow.get_repository(
            "organization"
        )
        self._user_repository: UserRepository = uow.get_repository(
            "user"
        )
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

            # Check if user exists
            user = self._user_repository.get_by_id(dto.user_id)
            if not user:
                raise ValueError("User not found")

            # Check if user is already in an organization
            if user.organization_id:
                raise ValueError("User is already a member of another organization")

            # Check if assigner has permission (must be owner or admin)
            assigner = self._user_repository.get_by_id(assigned_by)
            if not assigner or assigner.organization_id != organization_id:
                raise ValueError("Assigner is not a member of this organization")

            # Validate user addition
            can_add, reason = self._organization_domain_service.validate_user_addition(
                organization_id, dto.role
            )

            if not can_add:
                raise ValueError(f"Cannot add user: {reason}")

            # Add user to organization by updating user's organization_id
            user.organization_id = organization_id
            self._user_repository.save(user)

            # Add role assignment
            role = self._membership_service.add_user_to_organization(
                user_id=dto.user_id,
                organization_id=organization_id,
                role=dto.role,
                assigned_by=assigned_by,
            )

        return MembershipResponseDTO(
            **role.model_dump(),
            user_name=user.name.value,
            user_email=user.email.value,
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

            # Check if user exists and is member of this organization
            user = self._user_repository.get_by_id(user_id)
            if not user or user.organization_id != organization_id:
                raise ValueError("User is not a member of this organization")

            # Check permissions (only owner can update roles)
            updater = self._user_repository.get_by_id(updated_by)
            if not updater or updater.organization_id != organization_id:
                raise ValueError("Updater is not a member of this organization")

            if organization.owner_id != updated_by:
                raise ValueError("Only organization owner can update member roles")

            # Update role
            updated_role = self._membership_service.change_user_role(
                user_id=user_id,
                organization_id=organization_id,
                new_role=dto.role,
                changed_by=updated_by,
            )

        return MembershipResponseDTO(
            id=user.id,
            user_id=user.id,
            organization_id=organization_id,
            user_name=user.name.value,
            user_email=user.email.value,
            organization_name=organization.name.value,
            role=dto.role,
            assigned_at=user.created_at,
            is_active=user.is_active,
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

            # Check if user exists and is member of this organization
            user = self._user_repository.get_by_id(user_id)
            if not user or user.organization_id != organization_id:
                raise ValueError("User is not a member of this organization")

            # Check permissions
            remover = self._user_repository.get_by_id(removed_by)
            if not remover or remover.organization_id != organization_id:
                raise ValueError("Remover is not a member of this organization")

            is_self_removal = removed_by == user_id
            is_owner = organization.owner_id == removed_by

            if not is_owner and not is_self_removal:
                raise ValueError("User does not have permission to remove this member")

            # Check if user can leave organization (e.g., owner cannot leave without transfer)
            if is_self_removal:
                can_leave, reason = (
                    self._organization_domain_service.can_user_leave_organization(
                        user_id, organization_id
                    )
                )

                if not can_leave:
                    raise ValueError(f"Cannot leave organization: {reason}")

            # Remove user from organization by clearing organization_id
            user.organization_id = None
            self._user_repository.save(user)

            # Remove user roles
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

        # Get all users in organization
        users = self._user_repository.get_users_by_organization(organization_id)

        # Filter active users and paginate
        active_users = [user for user in users if user.is_active]
        total = len(active_users)

        offset = (page - 1) * page_size
        paginated_users = active_users[offset : offset + page_size]

        # Convert to DTOs
        membership_dtos = []
        for user in paginated_users:
            # Get user's roles in organization
            user_roles = self._membership_service.get_user_roles_in_organization(
                user.id, organization_id
            )
            
            # Create membership DTO
            dto = MembershipResponseDTO(
                id=user.id,
                user_id=user.id,
                organization_id=organization_id,
                user_name=user.name.value,
                user_email=user.email.value,
                organization_name=organization.name.value,
                role=user_roles[0] if user_roles else "member",  # Default role
                assigned_at=user.created_at,
                is_active=user.is_active,
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

        user = self._user_repository.get_by_id(user_id)
        if not user or user.organization_id != organization_id:
            return None

        # Get user's roles in organization
        user_roles = self._membership_service.get_user_roles_in_organization(
            user_id, organization_id
        )

        return MembershipResponseDTO(
            id=user.id,
            user_id=user.id,
            organization_id=organization_id,
            user_name=user.name.value,
            user_email=user.email.value,
            organization_name=organization.name.value,
            role=user_roles[0] if user_roles else "member",
            assigned_at=user.created_at,
            is_active=user.is_active,
        )

    def get_user_organizations(self, user_id: UUID) -> UserOrganizationsResponseDTO:
        """Get all organizations where user is a member."""

        user = self._user_repository.get_by_id(user_id)
        if not user or not user.organization_id:
            return UserOrganizationsResponseDTO(
                organizations=[],
                total=0,
                owned_count=0,
                member_count=0,
            )

        organization = self._organization_repository.get_by_id(user.organization_id)
        if not organization:
            return UserOrganizationsResponseDTO(
                organizations=[],
                total=0,
                owned_count=0,
                member_count=0,
            )

        # Get user's roles in organization
        user_roles = self._membership_service.get_user_roles_in_organization(
            user_id, user.organization_id
        )

        # Count organization members
        member_count = len(self._user_repository.get_users_by_organization(user.organization_id))

        is_owner = organization.owner_id == user_id
        
        org_summary = UserOrganizationSummaryDTO(
            organization_id=organization.id,
            organization_name=organization.name.value,
            role=user_roles[0] if user_roles else "member",
            is_owner=is_owner,
            joined_at=user.created_at,
            member_count=member_count,
            is_active=organization.is_active,
        )

        return UserOrganizationsResponseDTO(
            organizations=[org_summary],
            total=1,
            owned_count=1 if is_owner else 0,
            member_count=0 if is_owner else 1,
        )

    def transfer_ownership(
        self, organization_id: UUID, dto: OwnershipTransferDTO, current_owner_id: UUID
    ) -> MembershipResponseDTO:
        """Transfer organization ownership."""
        with self._uow:
            # Check if organization exists
            organization = self._organization_repository.get_by_id(organization_id)
            if not organization:
                raise ValueError("Organization not found")

            # Check if current user is owner
            if organization.owner_id != current_owner_id:
                raise ValueError("Only current owner can transfer ownership")

            # Check if new owner is member of organization
            new_owner = self._user_repository.get_by_id(dto.new_owner_id)
            if not new_owner or new_owner.organization_id != organization_id:
                raise ValueError("New owner must be a member of the organization")

            # Validate transfer
            can_transfer, reason = (
                self._organization_domain_service.can_transfer_ownership(
                    organization_id, current_owner_id, dto.new_owner_id
                )
            )

            if not can_transfer:
                raise ValueError(f"Cannot transfer ownership: {reason}")

            # Update organization owner
            organization.owner_id = dto.new_owner_id
            self._organization_repository.save(organization)

            # Update roles if needed
            self._membership_service.transfer_ownership(
                organization_id, current_owner_id, dto.new_owner_id
            )

        return MembershipResponseDTO(
            id=new_owner.id,
            user_id=new_owner.id,
            organization_id=organization_id,
            user_name=new_owner.name.value,
            user_email=new_owner.email.value,
            organization_name=organization.name.value,
            role="owner",
            assigned_at=new_owner.created_at,
            is_active=new_owner.is_active,
        )

    def invite_user(
        self, organization_id: UUID, dto: MembershipInviteDTO, invited_by: UUID
    ) -> bool:
        """Invite a user to join an organization."""

        # Check if organization exists
        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Check permissions (only owner can invite)
        inviter = self._user_repository.get_by_id(invited_by)
        if not inviter or inviter.organization_id != organization_id:
            raise ValueError("Inviter is not a member of this organization")

        if organization.owner_id != invited_by:
            raise ValueError("Only organization owner can invite members")

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
