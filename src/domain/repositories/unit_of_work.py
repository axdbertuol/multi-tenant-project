from abc import ABC, abstractmethod
from typing import AsyncContextManager

from domain.repositories.user_repository import UserRepository
from domain.repositories.user_session_repository import UserSessionRepository
from domain.repositories.organization_repository import OrganizationRepository


class UnitOfWork(ABC):
    users: UserRepository
    user_sessions: UserSessionRepository
    organizations: OrganizationRepository

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass