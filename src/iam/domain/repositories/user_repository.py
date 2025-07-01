from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.user import User
from ..value_objects.email import Email


class UserRepository(ABC):
    """Interface do repositório de usuários para o contexto delimitado de Usuário."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Salva ou atualiza um usuário."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Obtém um usuário pelo ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[User]:
        """Obtém um usuário pelo email."""
        pass

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool:
        """Verifica se o usuário existe pelo email."""
        pass

    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """Exclui um usuário pelo ID."""
        pass

    @abstractmethod
    def list_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Lista usuários ativos com paginação."""
        pass

    @abstractmethod
    def count_active_users(self) -> int:
        """Conta o total de usuários ativos."""
        pass
