from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.document_area import DocumentArea


class DocumentAreaRepository(ABC):
    """
    Repositório abstrato para áreas de documentos.
    """
    
    @abstractmethod
    def save(self, area: DocumentArea) -> DocumentArea:
        """Salva uma área de documentos."""
        pass
    
    @abstractmethod
    def get_by_id(self, area_id: UUID) -> Optional[DocumentArea]:
        """Obtém uma área pelo ID."""
        pass
    
    @abstractmethod
    def get_by_name_and_organization(
        self, name: str, organization_id: UUID
    ) -> Optional[DocumentArea]:
        """Obtém uma área pelo nome e organização."""
        pass
    
    @abstractmethod
    def get_by_folder_path_and_organization(
        self, folder_path: str, organization_id: UUID
    ) -> Optional[DocumentArea]:
        """Obtém uma área pelo caminho da pasta e organização."""
        pass
    
    @abstractmethod
    def get_by_organization(self, organization_id: UUID) -> List[DocumentArea]:
        """Obtém todas as áreas de uma organização."""
        pass
    
    @abstractmethod
    def get_active_by_organization(self, organization_id: UUID) -> List[DocumentArea]:
        """Obtém todas as áreas ativas de uma organização."""
        pass
    
    @abstractmethod
    def get_by_parent_area(self, parent_area_id: UUID) -> List[DocumentArea]:
        """Obtém todas as áreas filhas de uma área pai."""
        pass
    
    @abstractmethod
    def get_root_areas(self, organization_id: UUID) -> List[DocumentArea]:
        """Obtém todas as áreas raiz (sem pai) de uma organização."""
        pass
    
    @abstractmethod
    def get_children(self, area_id: UUID) -> List[DocumentArea]:
        """Obtém todas as áreas filhas diretas de uma área."""
        pass
    
    @abstractmethod
    def get_descendants(self, area_id: UUID) -> List[DocumentArea]:
        """Obtém todas as áreas descendentes (recursivamente) de uma área."""
        pass
    
    @abstractmethod
    def get_ancestors(self, area_id: UUID) -> List[DocumentArea]:
        """Obtém todas as áreas ancestrais de uma área."""
        pass
    
    @abstractmethod
    def get_system_areas(self, organization_id: UUID) -> List[DocumentArea]:
        """Obtém todas as áreas do sistema de uma organização."""
        pass
    
    @abstractmethod
    def delete(self, area_id: UUID) -> bool:
        """Remove uma área."""
        pass
    
    @abstractmethod
    def exists_by_name_and_organization(
        self, name: str, organization_id: UUID
    ) -> bool:
        """Verifica se existe uma área com esse nome na organização."""
        pass
    
    @abstractmethod
    def exists_by_folder_path_and_organization(
        self, folder_path: str, organization_id: UUID
    ) -> bool:
        """Verifica se existe uma área com esse caminho na organização."""
        pass
    
    @abstractmethod
    def count_by_organization(self, organization_id: UUID) -> int:
        """Conta o número de áreas em uma organização."""
        pass
    
    @abstractmethod
    def get_areas_by_folder_pattern(
        self, folder_pattern: str, organization_id: UUID
    ) -> List[DocumentArea]:
        """Obtém áreas que correspondem a um padrão de pasta."""
        pass
    
    @abstractmethod
    def get_areas_accessible_to_folder(
        self, folder_path: str, organization_id: UUID
    ) -> List[DocumentArea]:
        """Obtém todas as áreas que podem acessar uma pasta específica."""
        pass