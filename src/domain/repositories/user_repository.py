from abc import abstractmethod
from typing import Optional

from domain.repositories.base_repository import Repository
from domain.entities.user import User


class UserRepository(Repository[User]):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass