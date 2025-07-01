from typing import Optional
from uuid import UUID
import math

from shared.domain.repositories.unit_of_work import UnitOfWork

from ..dtos.organization_dto import (
    OrganizationCreateDTO,
    OrganizationUpdateDTO,
    OrganizationSettingsUpdateDTO,
    OrganizationResponseDTO,
    OrganizationListResponseDTO,
    OrganizationDetailResponseDTO,
    OrganizationMemberSummaryDTO,
)
from ...domain.entities.organization import Organization
from ...domain.entities.user_organization_role import (
    UserOrganizationRole,
    OrganizationRole,
)
from ...domain.repositories.organization_repository import OrganizationRepository
from ...domain.repositories.user_organization_role_repository import (
    UserOrganizationRoleRepository,
)
from ...domain.services.organization_domain_service import OrganizationDomainService
from ...domain.services.membership_service import MembershipService
from ...domain.value_objects.organization_name import OrganizationName


class OrganizationUseCase:
    """Use cases for organization management."""

    def __init__(self, uow: UnitOfWork):
        self._organization_repository: OrganizationRepository = uow.get_repository("organization")
        self._role_repository: UserOrganizationRoleRepository = uow.get_repository("user_organization_role")
        self._organization_domain_service = OrganizationDomainService(uow)
        self._membership_service = MembershipService(uow)
        self._uow = uow

    def create_organization(
        self, dto: OrganizationCreateDTO, owner_id: UUID
    ) -> OrganizationResponseDTO:
        """Create a new organization."""
        with self._uow:
            # Check if organization name is available
            org_name = OrganizationName(value=dto.name)
            is_available = self._organization_domain_service.is_organization_name_available(
                org_name
            )

            if not is_available:
                raise ValueError(f"Organization name '{dto.name}' is already in use")

            # Create organization entity
            organization = Organization.create(
                name=dto.name,
                owner_id=owner_id,
                description=dto.description,
                max_users=dto.max_users,
            )

            # Save organization
            saved_org = self._organization_repository.save(organization)

            # Create owner role
            self._membership_service.add_user_to_organization(
                user_id=owner_id,
                organization_id=saved_org.id,
                role=OrganizationRole.OWNER,
                assigned_by=owner_id,
            )

            # Get current user count
            user_count = self._role_repository.count_organization_users(saved_org.id)

        return OrganizationResponseDTO(
            **saved_org.model_dump(),
            current_user_count=user_count,
            max_users=dto.max_users,
            settings=saved_org.settings.model_dump(),
        )

    def get_organization_by_id(
        self, organization_id: UUID
    ) -> Optional[OrganizationResponseDTO]:
        """Get organization by ID."""
        organization = self._organization_repository.get_by_id(organization_id)

        if not organization:
            return None

        # Get current user count
        user_count = self._role_repository.count_organization_users(organization_id)

        return OrganizationResponseDTO(
            **organization.model_dump(),
            current_user_count=user_count,
            max_users=organization.settings.max_users,
            settings=organization.settings.model_dump(),
        )

    def get_organization_detail(
        self, organization_id: UUID
    ) -> Optional[OrganizationDetailResponseDTO]:
        """Get detailed organization information with members."""
        organization = self._organization_repository.get_by_id(organization_id)

        if not organization:
            return None

        # Get organization members
        user_roles = self._role_repository.get_user_roles_in_organization(
            organization_id
        )

        # Convert to member summary DTOs
        members = []
        roles_distribution = {}

        for role in user_roles:
            if role.is_valid():
                # This would typically require joining with user data
                member = OrganizationMemberSummaryDTO(
                    user_id=role.user_id,
                    user_name="User Name",  # Would fetch from iam service
                    user_email="user@example.com",  # Would fetch from iam service
                    role=role.role.value,
                    joined_at=role.assigned_at,
                    is_active=role.is_active,
                )
                members.append(member)

                # Count roles
                role_name = role.role.value
                roles_distribution[role_name] = roles_distribution.get(role_name, 0) + 1

        return OrganizationDetailResponseDTO(
            **organization.model_dump(),
            current_user_count=len(members),
            max_users=organization.settings.max_users,
            settings=organization.settings.model_dump(),
            members=members,
            member_count=len(members),
            roles_distribution=roles_distribution,
        )

    def update_organization(
        self, organization_id: UUID, dto: OrganizationUpdateDTO, updated_by: UUID
    ) -> OrganizationResponseDTO:
        """Update organization information."""
        with self._uow:
            organization = self._organization_repository.get_by_id(organization_id)

            if not organization:
                raise ValueError("Organization not found")

            # Check if user can modify organization
            user_role = self._role_repository.get_by_user_and_organization(
                updated_by, organization_id
            )

            if not user_role or not user_role.can_modify_organization():
                raise ValueError("User does not have permission to modify organization")

            updated_org = organization

            # Update name if provided
            if dto.name is not None:
                org_name = OrganizationName(value=dto.name)
                is_available = (
                    self._organization_domain_service.is_organization_name_available(
                        org_name, organization_id
                    )
                )
                if not is_available:
                    raise ValueError(f"Organization name '{dto.name}' is already in use")

                updated_org = updated_org.update_name(dto.name)

            # Update description if provided
            if dto.description is not None:
                updated_org = updated_org.update_description(dto.description)

            # Save updated organization
            saved_org = self._organization_repository.save(updated_org)

            # Get current user count
            user_count = self._role_repository.count_organization_users(organization_id)

        return OrganizationResponseDTO(
            **saved_org.model_dump(),
            current_user_count=user_count,
            max_users=saved_org.settings.max_users,
            settings=saved_org.settings.model_dump(),
        )

    def update_organization_settings(
        self,
        organization_id: UUID,
        dto: OrganizationSettingsUpdateDTO,
        updated_by: UUID,
    ) -> OrganizationResponseDTO:
        """Update organization settings."""
        with self._uow:
            organization = self._organization_repository.get_by_id(organization_id)

            if not organization:
                raise ValueError("Organization not found")

            # Check permissions
            user_role = self._role_repository.get_by_user_and_organization(
                updated_by, organization_id
            )

            if not user_role or not user_role.can_modify_organization():
                raise ValueError(
                    "User does not have permission to modify organization settings"
                )

            # Update settings
            updated_settings = organization.settings

            if dto.max_users is not None:
                # Validate new max_users doesn't violate current user count
                current_user_count = self._role_repository.count_organization_users(
                    organization_id
                )
                if dto.max_users < current_user_count:
                    raise ValueError(
                        f"Cannot reduce max users below current count: {current_user_count}"
                    )

                updated_settings = updated_settings.update_max_users(dto.max_users)

            if dto.allow_user_registration is not None:
                updated_settings = updated_settings.update_custom_setting(
                    "allow_user_registration", dto.allow_user_registration
                )

            if dto.require_email_verification is not None:
                updated_settings = updated_settings.update_custom_setting(
                    "require_email_verification", dto.require_email_verification
                )

            if dto.session_timeout_hours is not None:
                updated_settings = updated_settings.update_custom_setting(
                    "session_timeout_hours", dto.session_timeout_hours
                )

            if dto.features_enabled is not None:
                for feature, enabled in dto.features_enabled.items():
                    if enabled:
                        updated_settings = updated_settings.enable_feature(feature)
                    else:
                        updated_settings = updated_settings.disable_feature(feature)

            if dto.custom_settings is not None:
                for key, value in dto.custom_settings.items():
                    updated_settings = updated_settings.update_custom_setting(key, value)

            # Update organization with new settings
            updated_org = organization.update_settings(updated_settings)
            saved_org = self._organization_repository.save(updated_org)

            # Get current user count
            user_count = self._role_repository.count_organization_users(organization_id)

        return OrganizationResponseDTO(
            **saved_org.model_dump(),
            current_user_count=user_count,
            max_users=updated_settings.max_users,
            settings=updated_settings.model_dump(),
        )

    def deactivate_organization(
        self, organization_id: UUID, deactivated_by: UUID
    ) -> bool:
        """Deactivate an organization."""
        with self._uow:
            organization = self._organization_repository.get_by_id(organization_id)

            if not organization:
                raise ValueError("Organization not found")

            # Check if user is owner
            if not organization.is_owner(deactivated_by):
                raise ValueError("Only organization owner can deactivate the organization")

            # Check if organization can be safely deactivated
            (
                can_delete,
                reason,
            ) = self._organization_domain_service.can_organization_be_deleted(
                organization_id
            )

            if not can_delete:
                raise ValueError(f"Cannot deactivate organization: {reason}")

            # Deactivate organization
            updated_org = organization.deactivate()
            self._organization_repository.save(updated_org)

        return True

    def transfer_ownership(
        self, organization_id: UUID, current_owner_id: UUID, new_owner_id: UUID
    ) -> OrganizationResponseDTO:
        """Transfer organization ownership."""
        with self._uow:
            # Validate transfer
            (
                can_transfer,
                reason,
            ) = self._organization_domain_service.can_transfer_ownership(
                organization_id, current_owner_id, new_owner_id
            )

            if not can_transfer:
                raise ValueError(f"Cannot transfer ownership: {reason}")

            # Perform transfer
            self._membership_service.transfer_ownership(
                organization_id, current_owner_id, new_owner_id
            )

        # Return updated organization
        return self.get_organization_by_id(organization_id)

    def list_organizations(
        self, page: int = 1, page_size: int = 100, active_only: bool = True
    ) -> OrganizationListResponseDTO:
        """List organizations with pagination."""

        if page < 1:
            page = 1

        if page_size < 1 or page_size > 1000:
            page_size = 100

        offset = (page - 1) * page_size

        # Get organizations
        organizations = self._organization_repository.list_active_organizations(
            limit=page_size, offset=offset
        )

        # Get total count
        total = self._organization_repository.count_active_organizations()

        # Convert to DTOs
        org_dtos = []
        for org in organizations:
            user_count = self._role_repository.count_organization_users(org.id)
            org_dto = OrganizationResponseDTO(
                **org.model_dump(),
                current_user_count=user_count,
                max_users=org.settings.max_users,
                settings=org.settings.model_dump(),
            )
            org_dtos.append(org_dto)

        total_pages = math.ceil(total / page_size)

        return OrganizationListResponseDTO(
            organizations=org_dtos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_user_organizations(self, user_id: UUID) -> list[OrganizationResponseDTO]:
        """Get all organizations where user is a member."""
        organizations = self._organization_repository.get_user_organizations(user_id)

        org_dtos = []
        for org in organizations:
            user_count = self._role_repository.count_organization_users(org.id)
            org_dto = OrganizationResponseDTO(
                **org.model_dump(),
                current_user_count=user_count,
                max_users=org.settings.max_users,
                settings=org.settings.model_dump(),
            )
            org_dtos.append(org_dto)

        return org_dtos
