from abc import abstractmethod
from typing import Optional, List
from uuid import UUID

from domain.repositories.base_repository import Repository
from domain.entities.organization import Organization


class OrganizationRepository(Repository[Organization]):
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Organization]:
        pass

    @abstractmethod
    async def get_by_owner_id(self, owner_id: UUID) -> List[Organization]:
        pass

    @abstractmethod
    async def get_organizations_by_user_id(self, user_id: UUID) -> List[Organization]:
        pass

    @abstractmethod
    async def add_user_to_organization(self, organization_id: UUID, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def remove_user_from_organization(self, organization_id: UUID, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def is_user_in_organization(self, organization_id: UUID, user_id: UUID) -> bool:
        pass