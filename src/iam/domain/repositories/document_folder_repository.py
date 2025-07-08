from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.document_folder import DocumentFolder


class DocumentFolderRepository(ABC):
    """
    Repositório abstrato para pastas de documentos.
    """
    
    @abstractmethod
    def save(self, folder: DocumentFolder) -> DocumentFolder:
        """Salva uma pasta de documentos."""
        pass
    
    @abstractmethod
    def get_by_id(self, folder_id: UUID) -> Optional[DocumentFolder]:
        """Obtém uma pasta pelo ID."""
        pass
    
    @abstractmethod
    def get_by_path_and_organization(
        self, path: str, organization_id: UUID
    ) -> Optional[DocumentFolder]:
        """Obtém uma pasta pelo caminho e organização."""
        pass
    
    @abstractmethod
    def get_by_area(self, area_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas de uma área."""
        pass
    
    @abstractmethod
    def get_by_organization(self, organization_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas de uma organização."""
        pass
    
    @abstractmethod
    def get_active_by_organization(self, organization_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas ativas de uma organização."""
        pass
    
    @abstractmethod
    def get_by_parent_folder(self, parent_folder_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas filhas de uma pasta pai."""
        pass
    
    @abstractmethod
    def get_root_folders(self, organization_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas raiz (sem pai) de uma organização."""
        pass
    
    @abstractmethod
    def get_children(self, folder_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas filhas diretas de uma pasta."""
        pass
    
    @abstractmethod
    def get_descendants(self, folder_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas descendentes (recursivamente) de uma pasta."""
        pass
    
    @abstractmethod
    def get_ancestors(self, folder_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas ancestrais de uma pasta."""
        pass
    
    @abstractmethod
    def get_folders_accessible_by_area(
        self, area_id: UUID
    ) -> List[DocumentFolder]:
        """Obtém todas as pastas acessíveis por uma área."""
        pass
    
    @abstractmethod
    def get_folders_accessible_by_areas(
        self, area_ids: List[UUID]
    ) -> List[DocumentFolder]:
        """Obtém todas as pastas acessíveis por uma lista de áreas."""
        pass
    
    @abstractmethod
    def get_virtual_folders(self, organization_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas virtuais de uma organização."""
        pass
    
    @abstractmethod
    def get_physical_folders(self, organization_id: UUID) -> List[DocumentFolder]:
        """Obtém todas as pastas físicas de uma organização."""
        pass
    
    @abstractmethod
    def delete(self, folder_id: UUID) -> bool:
        """Remove uma pasta."""
        pass
    
    @abstractmethod
    def exists_by_path_and_organization(
        self, path: str, organization_id: UUID
    ) -> bool:
        """Verifica se existe uma pasta com esse caminho na organização."""
        pass
    
    @abstractmethod
    def count_by_organization(self, organization_id: UUID) -> int:
        """Conta o número de pastas em uma organização."""
        pass
    
    @abstractmethod
    def count_by_area(self, area_id: UUID) -> int:
        """Conta o número de pastas em uma área."""
        pass
    
    @abstractmethod
    def get_folders_by_path_pattern(
        self, path_pattern: str, organization_id: UUID
    ) -> List[DocumentFolder]:
        """Obtém pastas que correspondem a um padrão de caminho."""
        pass
    
    @abstractmethod
    def get_folders_with_area_access(
        self, area_ids: List[UUID], organization_id: UUID
    ) -> List[DocumentFolder]:
        """Obtém pastas que têm acesso às áreas especificadas."""
        pass