from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..entities.user_document_access import UserDocumentAccess


class UserDocumentAccessRepository(ABC):
    """
    Repositório abstrato para acesso de usuários a documentos.
    """
    
    @abstractmethod
    def save(self, access: UserDocumentAccess) -> UserDocumentAccess:
        """Salva um acesso de usuário a documentos."""
        pass
    
    @abstractmethod
    def get_by_id(self, access_id: UUID) -> Optional[UserDocumentAccess]:
        """Obtém um acesso pelo ID."""
        pass
    
    @abstractmethod
    def get_by_user_and_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> Optional[UserDocumentAccess]:
        """Obtém o acesso atual de um usuário em uma organização."""
        pass
    
    @abstractmethod
    def get_by_user(self, user_id: UUID) -> List[UserDocumentAccess]:
        """Obtém todos os acessos de um usuário."""
        pass
    
    @abstractmethod
    def get_active_by_user(self, user_id: UUID) -> List[UserDocumentAccess]:
        """Obtém todos os acessos ativos de um usuário."""
        pass
    
    @abstractmethod
    def get_by_area(self, area_id: UUID) -> List[UserDocumentAccess]:
        """Obtém todos os acessos de uma área."""
        pass
    
    @abstractmethod
    def get_by_area_and_organization(
        self, area_id: UUID, organization_id: UUID
    ) -> List[UserDocumentAccess]:
        """Obtém todos os acessos de uma área em uma organização."""
        pass
    
    @abstractmethod
    def get_by_organization(self, organization_id: UUID) -> List[UserDocumentAccess]:
        """Obtém todos os acessos de uma organização."""
        pass
    
    @abstractmethod
    def get_active_by_organization(self, organization_id: UUID) -> List[UserDocumentAccess]:
        """Obtém todos os acessos ativos de uma organização."""
        pass
    
    @abstractmethod
    def get_expiring_accesses(
        self, days_ahead: int = 7
    ) -> List[UserDocumentAccess]:
        """Obtém acessos que expiram em X dias."""
        pass
    
    @abstractmethod
    def get_expired_accesses(self) -> List[UserDocumentAccess]:
        """Obtém acessos que já expiraram."""
        pass
    
    @abstractmethod
    def get_access_history(
        self, user_id: UUID, organization_id: UUID
    ) -> List[UserDocumentAccess]:
        """Obtém histórico de acessos de um usuário em uma organização."""
        pass
    
    @abstractmethod
    def delete(self, access_id: UUID) -> bool:
        """Remove um acesso."""
        pass
    
    @abstractmethod
    def exists_active_access(
        self, user_id: UUID, organization_id: UUID
    ) -> bool:
        """Verifica se existe um acesso ativo para um usuário na organização."""
        pass
    
    @abstractmethod
    def count_by_area(self, area_id: UUID) -> int:
        """Conta o número de acessos de uma área."""
        pass
    
    @abstractmethod
    def count_by_organization(self, organization_id: UUID) -> int:
        """Conta o número de acessos de uma organização."""
        pass
    
    @abstractmethod
    def get_users_by_area(
        self, area_id: UUID, organization_id: UUID
    ) -> List[UUID]:
        """Obtém IDs de usuários que têm acesso a uma área específica."""
        pass
    
    @abstractmethod
    def get_accesses_by_assigned_by(
        self, assigned_by: UUID
    ) -> List[UserDocumentAccess]:
        """Obtém acessos atribuídos por um usuário específico."""
        pass
    
    @abstractmethod
    def get_accesses_modified_after(
        self, timestamp: datetime
    ) -> List[UserDocumentAccess]:
        """Obtém acessos modificados após uma data específica."""
        pass
    
    @abstractmethod
    def cleanup_expired_accesses(self) -> int:
        """Remove ou desativa acessos expirados. Retorna número de acessos afetados."""
        pass
    
    @abstractmethod
    def get_accesses_expiring_soon(
        self, days_threshold: int = 7
    ) -> List[UserDocumentAccess]:
        """Obtém acessos que expiram em breve."""
        pass
    
    @abstractmethod
    def revoke_user_access(
        self, user_id: UUID, organization_id: UUID
    ) -> bool:
        """Revoga o acesso de um usuário a uma organização."""
        pass
    
    @abstractmethod
    def get_areas_accessible_by_user(
        self, user_id: UUID, organization_id: UUID
    ) -> List[UUID]:
        """Obtém IDs de áreas acessíveis por um usuário."""
        pass