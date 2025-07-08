from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel, Field
import os


class DocumentFolder(BaseModel):
    """
    Entidade de domínio para Pastas de Documentos.
    
    Representa a estrutura hierárquica de pastas no sistema de documentos,
    com controle de acesso baseado em áreas.
    """
    
    id: UUID
    name: str
    path: str = Field(..., description="Caminho completo da pasta")
    area_id: UUID = Field(..., description="Área que controla esta pasta")
    organization_id: UUID
    parent_folder_id: Optional[UUID] = None  # Estrutura hierárquica
    allowed_areas: List[UUID] = Field(default_factory=list, description="Áreas que podem acessar")
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: UUID
    is_active: bool = True
    is_virtual: bool = False  # Se é uma pasta virtual ou física
    metadata: dict = Field(default_factory=dict)  # Metadados adicionais
    
    model_config = {"frozen": True}
    
    @classmethod
    def create(
        cls,
        name: str,
        path: str,
        area_id: UUID,
        organization_id: UUID,
        created_by: UUID,
        parent_folder_id: Optional[UUID] = None,
        allowed_areas: Optional[List[UUID]] = None,
        is_virtual: bool = False,
        metadata: Optional[dict] = None,
    ) -> "DocumentFolder":
        """Cria uma nova pasta de documentos."""
        # Validar formato do caminho
        if not cls._validate_folder_path(path):
            raise ValueError(f"Invalid folder path format: {path}")
        
        # Validar nome da pasta
        if not cls._validate_folder_name(name):
            raise ValueError(f"Invalid folder name: {name}")
        
        return cls(
            id=uuid4(),
            name=name,
            path=path,
            area_id=area_id,
            organization_id=organization_id,
            parent_folder_id=parent_folder_id,
            allowed_areas=allowed_areas or [area_id],  # Área principal sempre tem acesso
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            is_active=True,
            is_virtual=is_virtual,
            metadata=metadata or {},
        )
    
    @staticmethod
    def _validate_folder_path(path: str) -> bool:
        """Valida o formato do caminho da pasta."""
        # Deve começar com /documents/
        if not path.startswith("/documents/"):
            return False
        
        # Não deve conter caracteres inválidos
        invalid_chars = ["<", ">", ":", "\"", "|", "?", "*"]
        if any(char in path for char in invalid_chars):
            return False
        
        # Não deve ter espaços no início/fim ou barras duplas
        if path != path.strip() or "//" in path:
            return False
        
        # Não deve terminar com barra (exceto raiz)
        if path.endswith("/") and path != "/documents/":
            return False
        
        return True
    
    @staticmethod
    def _validate_folder_name(name: str) -> bool:
        """Valida o nome da pasta."""
        # Não deve estar vazio
        if not name or not name.strip():
            return False
        
        # Não deve conter caracteres inválidos
        invalid_chars = ["<", ">", ":", "\"", "|", "?", "*", "/", "\\"]
        if any(char in name for char in invalid_chars):
            return False
        
        # Não deve começar ou terminar com ponto
        if name.startswith(".") or name.endswith("."):
            return False
        
        return True
    
    def update_name(self, name: str) -> "DocumentFolder":
        """Atualiza o nome da pasta."""
        if not self._validate_folder_name(name):
            raise ValueError(f"Invalid folder name: {name}")
        
        # Atualizar path também
        parent_path = os.path.dirname(self.path)
        new_path = os.path.join(parent_path, name).replace("\\", "/")
        
        return self.model_copy(
            update={
                "name": name,
                "path": new_path,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def move_to_parent(self, new_parent_id: UUID, new_path: str) -> "DocumentFolder":
        """Move a pasta para um novo pai."""
        if new_parent_id == self.id:
            raise ValueError("Folder cannot be its own parent")
        
        if not self._validate_folder_path(new_path):
            raise ValueError(f"Invalid new path: {new_path}")
        
        return self.model_copy(
            update={
                "parent_folder_id": new_parent_id,
                "path": new_path,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def add_allowed_area(self, area_id: UUID) -> "DocumentFolder":
        """Adiciona uma área aos permitidos."""
        if area_id not in self.allowed_areas:
            new_allowed_areas = self.allowed_areas + [area_id]
            return self.model_copy(
                update={
                    "allowed_areas": new_allowed_areas,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        return self
    
    def remove_allowed_area(self, area_id: UUID) -> "DocumentFolder":
        """Remove uma área dos permitidos."""
        if area_id == self.area_id:
            raise ValueError("Cannot remove primary area from allowed areas")
        
        if area_id in self.allowed_areas:
            new_allowed_areas = [aid for aid in self.allowed_areas if aid != area_id]
            return self.model_copy(
                update={
                    "allowed_areas": new_allowed_areas,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        return self
    
    def set_allowed_areas(self, allowed_areas: List[UUID]) -> "DocumentFolder":
        """Define as áreas permitidas."""
        # Área principal sempre deve estar incluída
        if self.area_id not in allowed_areas:
            allowed_areas = [self.area_id] + allowed_areas
        
        return self.model_copy(
            update={
                "allowed_areas": allowed_areas,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def change_primary_area(self, new_area_id: UUID) -> "DocumentFolder":
        """Muda a área principal da pasta."""
        # Adicionar nova área aos permitidos se não estiver
        new_allowed_areas = self.allowed_areas.copy()
        if new_area_id not in new_allowed_areas:
            new_allowed_areas.append(new_area_id)
        
        return self.model_copy(
            update={
                "area_id": new_area_id,
                "allowed_areas": new_allowed_areas,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def update_metadata(self, metadata: dict) -> "DocumentFolder":
        """Atualiza os metadados da pasta."""
        new_metadata = {**self.metadata, **metadata}
        return self.model_copy(
            update={
                "metadata": new_metadata,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def deactivate(self) -> "DocumentFolder":
        """Desativa a pasta."""
        return self.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def activate(self) -> "DocumentFolder":
        """Ativa a pasta."""
        return self.model_copy(
            update={
                "is_active": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def can_be_accessed_by_area(self, area_id: UUID) -> bool:
        """Verifica se uma área pode acessar esta pasta."""
        return area_id in self.allowed_areas
    
    def has_parent(self) -> bool:
        """Verifica se a pasta tem um pai."""
        return self.parent_folder_id is not None
    
    def is_child_of(self, folder_hierarchy: List["DocumentFolder"], parent_id: UUID) -> bool:
        """Verifica se esta pasta é filha de outra pasta."""
        if not self.has_parent():
            return False
        
        folder_map = {folder.id: folder for folder in folder_hierarchy}
        
        current_parent_id = self.parent_folder_id
        visited = set()
        
        while current_parent_id and current_parent_id not in visited:
            if current_parent_id == parent_id:
                return True
            
            visited.add(current_parent_id)
            parent_folder = folder_map.get(current_parent_id)
            
            if not parent_folder:
                break
            
            current_parent_id = parent_folder.parent_folder_id
        
        return False
    
    def get_hierarchy_path(self, folder_hierarchy: List["DocumentFolder"]) -> List[UUID]:
        """Retorna o caminho completo da hierarquia."""
        if not self.has_parent():
            return [self.id]
        
        folder_map = {folder.id: folder for folder in folder_hierarchy}
        
        path = []
        current_folder = self
        visited = set()
        
        while current_folder and current_folder.id not in visited:
            path.insert(0, current_folder.id)
            visited.add(current_folder.id)
            
            if current_folder.parent_folder_id:
                current_folder = folder_map.get(current_folder.parent_folder_id)
            else:
                break
        
        return path
    
    def get_full_path_hierarchy(self, folder_hierarchy: List["DocumentFolder"]) -> List[str]:
        """Retorna todos os caminhos da hierarquia."""
        hierarchy_ids = self.get_hierarchy_path(folder_hierarchy)
        folder_map = {folder.id: folder for folder in folder_hierarchy}
        
        paths = []
        for folder_id in hierarchy_ids:
            folder = folder_map.get(folder_id)
            if folder:
                paths.append(folder.path)
        
        return paths
    
    def is_ancestor_of(self, folder_hierarchy: List["DocumentFolder"], child_folder: "DocumentFolder") -> bool:
        """Verifica se esta pasta é ancestral de outra pasta."""
        return child_folder.is_child_of(folder_hierarchy, self.id)
    
    def get_depth(self, folder_hierarchy: List["DocumentFolder"]) -> int:
        """Retorna a profundidade da pasta na hierarquia."""
        return len(self.get_hierarchy_path(folder_hierarchy)) - 1
    
    def validate_hierarchy(self, folder_hierarchy: List["DocumentFolder"]) -> tuple[bool, str]:
        """Valida se a hierarquia está correta."""
        if not self.has_parent():
            return True, "Folder has no parent"
        
        # Verificar ciclos
        if self.is_child_of(folder_hierarchy, self.id):
            return False, "Circular hierarchy detected"
        
        # Verificar se pai existe
        folder_map = {folder.id: folder for folder in folder_hierarchy}
        parent_folder = folder_map.get(self.parent_folder_id)
        
        if not parent_folder:
            return False, "Parent folder not found"
        
        # Verificar se pai está ativo
        if not parent_folder.is_active:
            return False, "Cannot have inactive parent folder"
        
        # Verificar se pai está na mesma organização
        if parent_folder.organization_id != self.organization_id:
            return False, "Parent folder must be in same organization"
        
        return True, "Hierarchy is valid"
    
    def get_relative_path(self) -> str:
        """Retorna o caminho relativo (sem /documents/)."""
        return self.path.replace("/documents/", "", 1)
    
    def is_root_folder(self) -> bool:
        """Verifica se é uma pasta raiz."""
        return self.parent_folder_id is None
    
    def get_folder_name_from_path(self) -> str:
        """Extrai o nome da pasta do caminho."""
        return os.path.basename(self.path)
    
    def is_accessible_by_areas(self, area_ids: List[UUID]) -> bool:
        """Verifica se qualquer das áreas pode acessar esta pasta."""
        return any(area_id in self.allowed_areas for area_id in area_ids)