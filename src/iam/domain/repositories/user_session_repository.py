from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.user_session import UserSession


class UserSessionRepository(ABC):
    """Interface do repositório de sessão de usuário para o contexto delimitado de Usuário."""

    @abstractmethod
    def save(self, session: UserSession) -> UserSession:
        """Salva ou atualiza uma sessão de usuário."""
        pass

    @abstractmethod
    def get_by_id(self, session_id: UUID) -> Optional[UserSession]:
        """Obtém uma sessão pelo ID."""
        pass

    @abstractmethod
    def get_by_token(self, token: str) -> Optional[UserSession]:
        """Obtém uma sessão pelo token."""
        pass

    @abstractmethod
    def get_active_by_user_id(self, user_id: UUID) -> List[UserSession]:
        """Obtém todas as sessões ativas para um usuário."""
        pass

    @abstractmethod
    def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """Revoga todas as sessões de um usuário. Retorna a contagem de sessões revogadas."""
        pass

    @abstractmethod
    def cleanup_expired_sessions(self) -> int:
        """Limpa sessões expiradas. Retorna a contagem de sessões limpas."""
        pass

    @abstractmethod
    def delete(self, session_id: UUID) -> bool:
        """Exclui uma sessão pelo ID."""
        pass
