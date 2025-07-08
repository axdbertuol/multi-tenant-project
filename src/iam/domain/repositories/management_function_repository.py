from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.management_function import ManagementFunction


class ManagementFunctionRepository(ABC):
    """
    Repositório abstrato para funções de gerenciamento.
    """
    
    @abstractmethod
    def save(self, function: ManagementFunction) -> ManagementFunction:
        """Salva uma função de gerenciamento."""
        pass
    
    @abstractmethod
    def get_by_id(self, function_id: UUID) -> Optional[ManagementFunction]:
        """Obtém uma função pelo ID."""
        pass
    
    @abstractmethod
    def get_by_name_and_organization(
        self, name: str, organization_id: UUID
    ) -> Optional[ManagementFunction]:
        """Obtém uma função pelo nome e organização."""
        pass
    
    @abstractmethod
    def get_by_organization(self, organization_id: UUID) -> List[ManagementFunction]:
        """Obtém todas as funções de uma organização."""
        pass
    
    @abstractmethod
    def get_active_by_organization(self, organization_id: UUID) -> List[ManagementFunction]:
        """Obtém todas as funções ativas de uma organização."""
        pass
    
    @abstractmethod
    def get_system_functions(self, organization_id: UUID) -> List[ManagementFunction]:
        """Obtém todas as funções do sistema de uma organização."""
        pass
    
    @abstractmethod
    def delete(self, function_id: UUID) -> bool:
        """Remove uma função."""
        pass
    
    @abstractmethod
    def exists_by_name_and_organization(
        self, name: str, organization_id: UUID
    ) -> bool:
        """Verifica se existe uma função com esse nome na organização."""
        pass
    
    @abstractmethod
    def count_by_organization(self, organization_id: UUID) -> int:
        """Conta o número de funções em uma organização."""
        pass
    
    @abstractmethod
    def get_functions_with_permission(
        self, permission: str, organization_id: UUID
    ) -> List[ManagementFunction]:
        """Obtém todas as funções que têm uma permissão específica."""
        pass