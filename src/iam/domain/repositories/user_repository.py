from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple
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

    @abstractmethod
    def update_last_login(self, user_id: UUID, login_time: datetime) -> bool:
        """Atualiza o horário do último login do usuário."""
        pass

    @abstractmethod
    def get_users_by_organization(self, organization_id: UUID) -> List[User]:
        """Encontra todos os usuários de uma organização."""
        pass

    @abstractmethod
    def count_users_by_organization(self, organization_id: UUID) -> int:
        """Conta usuários de uma organização."""
        pass

    @abstractmethod
    def get_users_without_organization(self) -> List[User]:
        """Encontra todos os usuários sem organização."""
        pass

    @abstractmethod
    def find_paginated(
        self,
        offset: int = 0,
        limit: int = 20,
        email_filter: Optional[str] = None,
        name_filter: Optional[str] = None,
        is_active: Optional[bool] = None,
        organization_id: Optional[UUID] = None,
        has_organization: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        """Encontra usuários com paginação e filtros."""
        pass
