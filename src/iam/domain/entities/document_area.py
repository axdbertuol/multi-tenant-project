from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel, Field
import re


class DocumentArea(BaseModel):
    """
    Entidade de domínio para Áreas de Documentos.
    
    Controla acesso hierárquico a pastas/arquivos para o LLM.
    Exemplo: usuário na Área "RH" acessa pasta "RH" e todas as subpastas recursivamente.
    """
    
    id: UUID
    name: str  # "RH", "RH-junior", "Financeiro"
    description: str
    organization_id: UUID
    parent_area_id: Optional[UUID] = None  # Hierarquia de áreas
    folder_path: str = Field(..., description="Caminho da pasta no sistema")
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: UUID
    is_active: bool = True
    is_system_area: bool = False
    
    model_config = {"frozen": True}
    
    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        organization_id: UUID,
        folder_path: str,
        created_by: UUID,
        parent_area_id: Optional[UUID] = None,
        is_system_area: bool = False,
    ) -> "DocumentArea":
        """Cria uma nova área de documentos."""
        # Validar formato do caminho
        if not cls._validate_folder_path(folder_path):
            raise ValueError(f"Invalid folder path format: {folder_path}")
        
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            organization_id=organization_id,
            parent_area_id=parent_area_id,
            folder_path=folder_path,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            is_active=True,
            is_system_area=is_system_area,
        )
    
    @staticmethod
    def _validate_folder_path(folder_path: str) -> bool:
        """Valida o formato do caminho da pasta."""
        # Deve começar com /documents/
        if not folder_path.startswith("/documents/"):
            return False
        
        # Não deve conter caracteres inválidos
        invalid_chars = ["<", ">", ":", "\"", "|", "?", "*"]
        if any(char in folder_path for char in invalid_chars):
            return False
        
        # Não deve ter espaços no início/fim ou barras duplas
        if folder_path != folder_path.strip() or "//" in folder_path:
            return False
        
        return True
    
    def update_description(self, description: str) -> "DocumentArea":
        """Atualiza a descrição da área."""
        return self.model_copy(
            update={
                "description": description,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def update_folder_path(self, folder_path: str) -> "DocumentArea":
        """Atualiza o caminho da pasta."""
        if self.is_system_area:
            raise ValueError("System areas cannot have folder path modified")
        
        if not self._validate_folder_path(folder_path):
            raise ValueError(f"Invalid folder path format: {folder_path}")
        
        return self.model_copy(
            update={
                "folder_path": folder_path,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def set_parent_area(self, parent_area_id: UUID) -> "DocumentArea":
        """Define a área pai."""
        if parent_area_id == self.id:
            raise ValueError("Area cannot be its own parent")
        
        return self.model_copy(
            update={
                "parent_area_id": parent_area_id,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def remove_parent_area(self) -> "DocumentArea":
        """Remove a área pai."""
        return self.model_copy(
            update={
                "parent_area_id": None,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def deactivate(self) -> "DocumentArea":
        """Desativa a área."""
        if self.is_system_area:
            raise ValueError("System areas cannot be deactivated")
        
        return self.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def activate(self) -> "DocumentArea":
        """Ativa a área."""
        return self.model_copy(
            update={
                "is_active": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def has_parent(self) -> bool:
        """Verifica se a área tem um pai."""
        return self.parent_area_id is not None
    
    def is_child_of(self, area_hierarchy: List["DocumentArea"], parent_id: UUID) -> bool:
        """Verifica se esta área é filha de outra área."""
        if not self.has_parent():
            return False
        
        # Mapa para eficiência
        area_map = {area.id: area for area in area_hierarchy}
        
        current_parent_id = self.parent_area_id
        visited = set()  # Prevenir loops infinitos
        
        while current_parent_id and current_parent_id not in visited:
            if current_parent_id == parent_id:
                return True
            
            visited.add(current_parent_id)
            parent_area = area_map.get(current_parent_id)
            
            if not parent_area:
                break
            
            current_parent_id = parent_area.parent_area_id
        
        return False
    
    def get_hierarchy_path(self, area_hierarchy: List["DocumentArea"]) -> List[UUID]:
        """Retorna o caminho completo da hierarquia da raiz até esta área."""
        if not self.has_parent():
            return [self.id]
        
        area_map = {area.id: area for area in area_hierarchy}
        
        path = []
        current_area = self
        visited = set()
        
        while current_area and current_area.id not in visited:
            path.insert(0, current_area.id)  # Inserir no início para ordem raiz-folha
            visited.add(current_area.id)
            
            if current_area.parent_area_id:
                current_area = area_map.get(current_area.parent_area_id)
            else:
                break
        
        return path
    
    def get_folder_hierarchy_paths(self, area_hierarchy: List["DocumentArea"]) -> List[str]:
        """Retorna todos os caminhos de pastas da hierarquia (da raiz até esta área)."""
        hierarchy_ids = self.get_hierarchy_path(area_hierarchy)
        area_map = {area.id: area for area in area_hierarchy}
        
        paths = []
        for area_id in hierarchy_ids:
            area = area_map.get(area_id)
            if area:
                paths.append(area.folder_path)
        
        return paths
    
    def can_access_folder(self, folder_path: str) -> bool:
        """Verifica se esta área pode acessar um caminho de pasta específico."""
        # Normalizar caminhos
        normalized_area_path = self.folder_path.rstrip("/")
        normalized_folder_path = folder_path.rstrip("/")
        
        # Área pode acessar sua própria pasta
        if normalized_folder_path == normalized_area_path:
            return True
        
        # Área pode acessar subpastas (recursivamente)
        if normalized_folder_path.startswith(normalized_area_path + "/"):
            return True
        
        return False
    
    def get_accessible_paths(self, area_hierarchy: List["DocumentArea"]) -> List[str]:
        """Retorna todos os caminhos que esta área pode acessar (incluindo hierarquia)."""
        # Obter caminhos da hierarquia
        hierarchy_paths = self.get_folder_hierarchy_paths(area_hierarchy)
        
        # Área pode acessar suas próprias pastas e as de áreas pai
        accessible_paths = []
        
        for path in hierarchy_paths:
            accessible_paths.append(path)
            # Também incluir acesso recursivo às subpastas
            accessible_paths.append(path + "/*")
        
        return list(set(accessible_paths))  # Remover duplicatas
    
    def validate_hierarchy(self, area_hierarchy: List["DocumentArea"]) -> tuple[bool, str]:
        """Valida se a hierarquia está correta."""
        if not self.has_parent():
            return True, "Area has no parent"
        
        # Verificar se há ciclos
        if self.is_child_of(area_hierarchy, self.id):
            return False, "Circular hierarchy detected"
        
        # Verificar se área pai existe
        area_map = {area.id: area for area in area_hierarchy}
        parent_area = area_map.get(self.parent_area_id)
        
        if not parent_area:
            return False, "Parent area not found"
        
        # Verificar se área pai está ativa
        if not parent_area.is_active:
            return False, "Cannot have inactive parent area"
        
        # Verificar se área pai está na mesma organização
        if parent_area.organization_id != self.organization_id:
            return False, "Parent area must be in same organization"
        
        return True, "Hierarchy is valid"
    
    def can_be_deleted(self) -> tuple[bool, str]:
        """Verifica se a área pode ser deletada."""
        if self.is_system_area:
            return False, "System areas cannot be deleted"
        
        return True, "Area can be deleted"
    
    def get_normalized_path(self) -> str:
        """Retorna o caminho normalizado da pasta."""
        return self.folder_path.rstrip("/")
    
    def is_root_area(self) -> bool:
        """Verifica se é uma área raiz (sem pai)."""
        return self.parent_area_id is None