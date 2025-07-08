from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..entities.user_management_function import UserManagementFunction


class UserManagementFunctionRepository(ABC):
    """
    Repositório abstrato para atribuições de funções de gerenciamento a usuários.
    """
    
    @abstractmethod
    def save(self, assignment: UserManagementFunction) -> UserManagementFunction:
        """Salva uma atribuição de função de gerenciamento."""
        pass
    
    @abstractmethod
    def get_by_id(self, assignment_id: UUID) -> Optional[UserManagementFunction]:
        """Obtém uma atribuição pelo ID."""
        pass
    
    @abstractmethod
    def get_by_user_and_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> Optional[UserManagementFunction]:
        """Obtém a atribuição atual de um usuário em uma organização."""
        pass
    
    @abstractmethod
    def get_by_user(self, user_id: UUID) -> List[UserManagementFunction]:
        """Obtém todas as atribuições de um usuário."""
        pass
    
    @abstractmethod
    def get_active_by_user(self, user_id: UUID) -> List[UserManagementFunction]:
        """Obtém todas as atribuições ativas de um usuário."""
        pass
    
    @abstractmethod
    def get_by_function(self, function_id: UUID) -> List[UserManagementFunction]:
        """Obtém todas as atribuições de uma função."""
        pass
    
    @abstractmethod
    def get_by_function_and_organization(
        self, function_id: UUID, organization_id: UUID
    ) -> List[UserManagementFunction]:
        """Obtém todas as atribuições de uma função em uma organização."""
        pass
    
    @abstractmethod
    def get_by_organization(self, organization_id: UUID) -> List[UserManagementFunction]:
        """Obtém todas as atribuições de uma organização."""
        pass
    
    @abstractmethod
    def get_active_by_organization(self, organization_id: UUID) -> List[UserManagementFunction]:
        """Obtém todas as atribuições ativas de uma organização."""
        pass
    
    @abstractmethod
    def get_expiring_assignments(
        self, days_ahead: int = 7
    ) -> List[UserManagementFunction]:
        """Obtém atribuições que expiram em X dias."""
        pass
    
    @abstractmethod
    def get_expired_assignments(self) -> List[UserManagementFunction]:
        """Obtém atribuições que já expiraram."""
        pass
    
    @abstractmethod
    def get_assignment_history(
        self, user_id: UUID, organization_id: UUID
    ) -> List[UserManagementFunction]:
        """Obtém histórico de atribuições de um usuário em uma organização."""
        pass
    
    @abstractmethod
    def delete(self, assignment_id: UUID) -> bool:
        """Remove uma atribuição."""
        pass
    
    @abstractmethod
    def exists_active_assignment(
        self, user_id: UUID, organization_id: UUID
    ) -> bool:
        """Verifica se existe uma atribuição ativa para um usuário na organização."""
        pass
    
    @abstractmethod
    def count_by_function(self, function_id: UUID) -> int:
        """Conta o número de atribuições de uma função."""
        pass
    
    @abstractmethod
    def count_by_organization(self, organization_id: UUID) -> int:
        """Conta o número de atribuições de uma organização."""
        pass
    
    @abstractmethod
    def get_users_by_function(
        self, function_id: UUID, organization_id: UUID
    ) -> List[UUID]:
        """Obtém IDs de usuários que têm uma função específica."""
        pass
    
    @abstractmethod
    def get_assignments_by_assigned_by(
        self, assigned_by: UUID
    ) -> List[UserManagementFunction]:
        """Obtém atribuições feitas por um usuário específico."""
        pass
    
    @abstractmethod
    def get_assignments_modified_after(
        self, timestamp: datetime
    ) -> List[UserManagementFunction]:
        """Obtém atribuições modificadas após uma data específica."""
        pass
    
    @abstractmethod
    def cleanup_expired_assignments(self) -> int:
        """Remove ou desativa atribuições expiradas. Retorna número de atribuições afetadas."""
        pass
    
    @abstractmethod
    def get_assignments_expiring_soon(
        self, days_threshold: int = 7
    ) -> List[UserManagementFunction]:
        """Obtém atribuições que expiram em breve."""
        pass
    
    @abstractmethod
    def revoke_user_assignment(
        self, user_id: UUID, organization_id: UUID
    ) -> bool:
        """Revoga a atribuição de um usuário a uma organização."""
        pass
    
    @abstractmethod
    def get_functions_by_user(
        self, user_id: UUID, organization_id: UUID
    ) -> List[UUID]:
        """Obtém IDs de funções atribuídas a um usuário."""
        pass