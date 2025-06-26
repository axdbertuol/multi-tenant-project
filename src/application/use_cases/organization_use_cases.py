from typing import List, Optional
from uuid import UUID

from domain.entities.organization import Organization
from domain.repositories.unit_of_work import UnitOfWork
from application.dtos.organization_dto import (
    CreateOrganizationDto,
    UpdateOrganizationDto,
    TransferOwnershipDto,
    AddUserToOrganizationDto,
    OrganizationResponseDto
)


class OrganizationUseCases:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _to_response_dto(self, organization: Organization) -> OrganizationResponseDto:
        return OrganizationResponseDto(
            id=organization.id,
            name=organization.name,
            description=organization.description,
            owner_id=organization.owner_id,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
            is_active=organization.is_active
        )

    async def create_organization(self, owner_id: UUID, create_dto: CreateOrganizationDto) -> OrganizationResponseDto:
        async with self.uow:
            existing_org = await self.uow.organizations.get_by_name(create_dto.name)
            if existing_org:
                raise ValueError(f"Organization with name {create_dto.name} already exists")

            user = await self.uow.users.get_by_id(owner_id)
            if not user:
                raise ValueError(f"User with id {owner_id} does not exist")

            organization = Organization.create(
                name=create_dto.name,
                owner_id=owner_id,
                description=create_dto.description
            )
            created_org = await self.uow.organizations.create(organization)
            
            await self.uow.organizations.add_user_to_organization(created_org.id, owner_id)
            
            return self._to_response_dto(created_org)

    async def get_organization_by_id(self, organization_id: UUID) -> Optional[OrganizationResponseDto]:
        async with self.uow:
            organization = await self.uow.organizations.get_by_id(organization_id)
            return self._to_response_dto(organization) if organization else None

    async def get_organization_by_name(self, name: str) -> Optional[OrganizationResponseDto]:
        async with self.uow:
            organization = await self.uow.organizations.get_by_name(name)
            return self._to_response_dto(organization) if organization else None

    async def get_organizations_by_owner(self, owner_id: UUID) -> List[OrganizationResponseDto]:
        async with self.uow:
            organizations = await self.uow.organizations.get_by_owner_id(owner_id)
            return [self._to_response_dto(org) for org in organizations]

    async def get_user_organizations(self, user_id: UUID) -> List[OrganizationResponseDto]:
        async with self.uow:
            organizations = await self.uow.organizations.get_organizations_by_user_id(user_id)
            return [self._to_response_dto(org) for org in organizations]

    async def update_organization(self, organization_id: UUID, update_dto: UpdateOrganizationDto, requester_id: UUID) -> Optional[OrganizationResponseDto]:
        async with self.uow:
            organization = await self.uow.organizations.get_by_id(organization_id)
            if not organization:
                return None

            if organization.owner_id != requester_id:
                raise PermissionError("Only the organization owner can update the organization")

            updated_org = organization
            if update_dto.name:
                existing_org = await self.uow.organizations.get_by_name(update_dto.name)
                if existing_org and existing_org.id != organization_id:
                    raise ValueError(f"Organization with name {update_dto.name} already exists")
                updated_org = updated_org.update_name(update_dto.name)

            if update_dto.description is not None:
                updated_org = updated_org.update_description(update_dto.description)

            final_org = await self.uow.organizations.update(updated_org)
            return self._to_response_dto(final_org)

    async def transfer_ownership(self, organization_id: UUID, transfer_dto: TransferOwnershipDto, current_owner_id: UUID) -> Optional[OrganizationResponseDto]:
        async with self.uow:
            organization = await self.uow.organizations.get_by_id(organization_id)
            if not organization:
                return None

            if organization.owner_id != current_owner_id:
                raise PermissionError("Only the current owner can transfer ownership")

            new_owner = await self.uow.users.get_by_id(transfer_dto.new_owner_id)
            if not new_owner:
                raise ValueError(f"User with id {transfer_dto.new_owner_id} does not exist")

            is_member = await self.uow.organizations.is_user_in_organization(organization_id, transfer_dto.new_owner_id)
            if not is_member:
                await self.uow.organizations.add_user_to_organization(organization_id, transfer_dto.new_owner_id)

            transferred_org = organization.transfer_ownership(transfer_dto.new_owner_id)
            final_org = await self.uow.organizations.update(transferred_org)
            return self._to_response_dto(final_org)

    async def add_user_to_organization(self, organization_id: UUID, add_user_dto: AddUserToOrganizationDto, requester_id: UUID) -> bool:
        async with self.uow:
            organization = await self.uow.organizations.get_by_id(organization_id)
            if not organization:
                raise ValueError(f"Organization with id {organization_id} does not exist")

            if organization.owner_id != requester_id:
                raise PermissionError("Only the organization owner can add users")

            user = await self.uow.users.get_by_id(add_user_dto.user_id)
            if not user:
                raise ValueError(f"User with id {add_user_dto.user_id} does not exist")

            is_already_member = await self.uow.organizations.is_user_in_organization(organization_id, add_user_dto.user_id)
            if is_already_member:
                raise ValueError("User is already a member of this organization")

            await self.uow.organizations.add_user_to_organization(organization_id, add_user_dto.user_id)
            return True

    async def remove_user_from_organization(self, organization_id: UUID, user_id: UUID, requester_id: UUID) -> bool:
        async with self.uow:
            organization = await self.uow.organizations.get_by_id(organization_id)
            if not organization:
                raise ValueError(f"Organization with id {organization_id} does not exist")

            if organization.owner_id != requester_id and requester_id != user_id:
                raise PermissionError("Only the organization owner or the user themselves can remove membership")

            if organization.owner_id == user_id:
                raise ValueError("The organization owner cannot be removed from the organization")

            is_member = await self.uow.organizations.is_user_in_organization(organization_id, user_id)
            if not is_member:
                raise ValueError("User is not a member of this organization")

            await self.uow.organizations.remove_user_from_organization(organization_id, user_id)
            return True

    async def deactivate_organization(self, organization_id: UUID, requester_id: UUID) -> Optional[OrganizationResponseDto]:
        async with self.uow:
            organization = await self.uow.organizations.get_by_id(organization_id)
            if not organization:
                return None

            if organization.owner_id != requester_id:
                raise PermissionError("Only the organization owner can deactivate the organization")

            deactivated_org = organization.deactivate()
            updated_org = await self.uow.organizations.update(deactivated_org)
            return self._to_response_dto(updated_org)

    async def activate_organization(self, organization_id: UUID, requester_id: UUID) -> Optional[OrganizationResponseDto]:
        async with self.uow:
            organization = await self.uow.organizations.get_by_id(organization_id)
            if not organization:
                return None

            if organization.owner_id != requester_id:
                raise PermissionError("Only the organization owner can activate the organization")

            activated_org = organization.activate()
            updated_org = await self.uow.organizations.update(activated_org)
            return self._to_response_dto(updated_org)