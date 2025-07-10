from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel, Field

from ..value_objects.folder_permission_level import FolderPermissionLevel


class ProfileFolderPermission(BaseModel):
    """
    Entidade de domínio para Permissões de Pastas por Perfil.
    
    Define as permissões específicas que um perfil tem sobre uma pasta.
    Permite controle granular de acesso (ler, editar, completa) por pasta.
    """
    
    id: UUID
    profile_id: UUID
    folder_path: str = Field(..., description="Caminho da pasta")
    permission_level: FolderPermissionLevel
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    notes: Optional[str] = None
    extra_data: dict = Field(default_factory=dict)
    
    model_config = {"frozen": True}
    
    @classmethod
    def create(
        cls,
        profile_id: UUID,
        folder_path: str,
        permission_level: FolderPermissionLevel,
        organization_id: UUID,
        created_by: UUID,
        notes: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> "ProfileFolderPermission":
        """
        Cria uma nova permissão de pasta para perfil.
        
        Args:
            profile_id: ID do perfil
            folder_path: Caminho da pasta
            permission_level: Nível de permissão (READ, EDIT, FULL)
            organization_id: ID da organização
            created_by: ID do usuário que criou
            notes: Notas sobre a permissão
            extra_data: Metadados adicionais
        """
        # Validar formato do caminho
        if not cls._validate_folder_path(folder_path):
            raise ValueError(f"Invalid folder path format: {folder_path}")
        
        return cls(
            id=uuid4(),
            profile_id=profile_id,
            folder_path=folder_path.rstrip("/"),
            permission_level=permission_level,
            organization_id=organization_id,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            is_active=True,
            notes=notes,
            extra_data=extra_data or {},
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
    
    def update_permission_level(self, permission_level: FolderPermissionLevel) -> "ProfileFolderPermission":
        """Atualiza o nível de permissão."""
        return self.model_copy(
            update={
                "permission_level": permission_level,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def update_folder_path(self, folder_path: str) -> "ProfileFolderPermission":
        """Atualiza o caminho da pasta."""
        if not self._validate_folder_path(folder_path):
            raise ValueError(f"Invalid folder path format: {folder_path}")
        
        return self.model_copy(
            update={
                "folder_path": folder_path.rstrip("/"),
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def update_notes(self, notes: str) -> "ProfileFolderPermission":
        """Atualiza as notas da permissão."""
        return self.model_copy(
            update={
                "notes": notes,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def update_extra_data(self, extra_data: dict) -> "ProfileFolderPermission":
        """Atualiza os dados extras da permissão."""
        new_extra_data = {**self.extra_data, **extra_data}
        return self.model_copy(
            update={
                "extra_data": new_extra_data,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def deactivate(self) -> "ProfileFolderPermission":
        """Desativa a permissão."""
        return self.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def activate(self) -> "ProfileFolderPermission":
        """Ativa a permissão."""
        return self.model_copy(
            update={
                "is_active": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def can_perform_action(self, action: str) -> bool:
        """Verifica se a permissão permite uma ação específica."""
        if not self.is_active:
            return False
        
        return self.permission_level.can_perform_action(action)
    
    def can_access_folder(self, folder_path: str) -> bool:
        """Verifica se a permissão permite acesso a um caminho de pasta."""
        if not self.is_active:
            return False
        
        # Normalizar caminhos
        normalized_permission_path = self.folder_path.rstrip("/")
        normalized_folder_path = folder_path.rstrip("/")
        
        # Permissão para pasta exata
        if normalized_folder_path == normalized_permission_path:
            return True
        
        # Permissão para subpastas (recursivo)
        if normalized_folder_path.startswith(normalized_permission_path + "/"):
            return True
        
        return False
    
    def get_allowed_actions(self) -> List[str]:
        """Retorna as ações permitidas por esta permissão."""
        if not self.is_active:
            return []
        
        return self.permission_level.get_allowed_actions()
    
    def can_create_folders(self) -> bool:
        """Verifica se pode criar pastas."""
        return self.is_active and self.permission_level.can_create_folders()
    
    def can_edit_documents(self) -> bool:
        """Verifica se pode editar documentos."""
        return self.is_active and self.permission_level.can_edit_documents()
    
    def can_read_documents(self) -> bool:
        """Verifica se pode ler documentos."""
        return self.is_active and self.permission_level.can_read_documents()
    
    def can_use_rag(self) -> bool:
        """Verifica se pode usar RAG."""
        return self.is_active and self.permission_level.can_use_rag()
    
    def can_train_rag(self) -> bool:
        """Verifica se pode treinar RAG."""
        return self.is_active and self.permission_level.can_train_rag()
    
    def get_folder_depth(self) -> int:
        """Retorna a profundidade da pasta."""
        # Remove /documents/ e conta as barras
        relative_path = self.folder_path.replace("/documents/", "", 1)
        if not relative_path:
            return 0
        return relative_path.count("/") + 1
    
    def is_root_folder_permission(self) -> bool:
        """Verifica se é uma permissão para pasta raiz."""
        return self.folder_path == "/documents" or self.folder_path == "/documents/"
    
    def get_parent_folder_path(self) -> Optional[str]:
        """Retorna o caminho da pasta pai."""
        if self.is_root_folder_permission():
            return None
        
        parent_path = "/".join(self.folder_path.split("/")[:-1])
        return parent_path if parent_path != "/documents" else "/documents/"
    
    def is_subfolder_of(self, parent_folder_path: str) -> bool:
        """Verifica se esta permissão é para uma subpasta de outra."""
        normalized_parent = parent_folder_path.rstrip("/")
        normalized_current = self.folder_path.rstrip("/")
        
        return normalized_current.startswith(normalized_parent + "/")
    
    def is_parent_of(self, child_folder_path: str) -> bool:
        """Verifica se esta permissão é para uma pasta pai de outra."""
        normalized_current = self.folder_path.rstrip("/")
        normalized_child = child_folder_path.rstrip("/")
        
        return normalized_child.startswith(normalized_current + "/")
    
    def conflicts_with(self, other: "ProfileFolderPermission") -> bool:
        """Verifica se há conflito com outra permissão."""
        if not self.is_active or not other.is_active:
            return False
        
        if self.profile_id != other.profile_id:
            return False
        
        # Verifica se são para a mesma pasta
        if self.folder_path == other.folder_path:
            return True
        
        # Verifica se uma é subpasta da outra
        if self.is_subfolder_of(other.folder_path) or other.is_subfolder_of(self.folder_path):
            return True
        
        return False
    
    def validate_permission(self) -> tuple[bool, List[str]]:
        """Valida se a permissão está correta."""
        errors = []
        
        # Validar IDs
        if not self.profile_id:
            errors.append("Profile ID is required")
        
        if not self.organization_id:
            errors.append("Organization ID is required")
        
        if not self.created_by:
            errors.append("Created by is required")
        
        # Validar caminho da pasta
        if not self.folder_path:
            errors.append("Folder path is required")
        elif not self._validate_folder_path(self.folder_path):
            errors.append(f"Invalid folder path format: {self.folder_path}")
        
        # Validar nível de permissão
        if not self.permission_level:
            errors.append("Permission level is required")
        
        return len(errors) == 0, errors
    
    def get_relative_path(self) -> str:
        """Retorna o caminho relativo (sem /documents/)."""
        return self.folder_path.replace("/documents/", "", 1)
    
    def get_folder_name(self) -> str:
        """Retorna o nome da pasta."""
        return self.folder_path.split("/")[-1]
    
    def get_creation_age_days(self) -> int:
        """Retorna a idade da permissão em dias."""
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.days
    
    def get_last_update_age_days(self) -> Optional[int]:
        """Retorna quantos dias desde a última atualização."""
        if not self.updated_at:
            return None
        
        delta = datetime.now(timezone.utc) - self.updated_at
        return delta.days
    
    def is_recently_created(self, days_threshold: int = 7) -> bool:
        """Verifica se a permissão foi criada recentemente."""
        return self.get_creation_age_days() <= days_threshold
    
    def is_recently_updated(self, days_threshold: int = 7) -> bool:
        """Verifica se a permissão foi atualizada recentemente."""
        if not self.updated_at:
            return False
        
        update_age = self.get_last_update_age_days()
        return update_age is not None and update_age <= days_threshold
    
    def has_extra_data_key(self, key: str) -> bool:
        """Verifica se existe uma chave específica nos dados extras."""
        return key in self.extra_data
    
    def get_extra_data_value(self, key: str, default=None):
        """Obtém um valor específico dos dados extras."""
        return self.extra_data.get(key, default)
    
    def get_status(self) -> str:
        """Retorna o status atual da permissão."""
        if not self.is_active:
            return "inactive"
        
        if self.is_recently_created():
            return "new"
        
        if self.is_recently_updated():
            return "updated"
        
        return "active"
    
    def to_summary_dict(self) -> dict:
        """Converte a permissão para um dicionário resumido."""
        return {
            "id": str(self.id),
            "profile_id": str(self.profile_id),
            "folder_path": self.folder_path,
            "permission_level": self.permission_level.value,
            "permission_level_display": self.permission_level.get_display_name(),
            "organization_id": str(self.organization_id),
            "is_active": self.is_active,
            "status": self.get_status(),
            "allowed_actions": self.get_allowed_actions(),
            "can_create_folders": self.can_create_folders(),
            "can_edit_documents": self.can_edit_documents(),
            "can_read_documents": self.can_read_documents(),
            "can_use_rag": self.can_use_rag(),
            "can_train_rag": self.can_train_rag(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }