from enum import Enum
from typing import List


class FolderPermissionLevel(str, Enum):
    """
    Níveis de permissão para pastas em perfis de usuário.
    
    Define os três níveis de acesso que um perfil pode ter sobre uma pasta:
    - READ: Apenas leitura de documentos e RAG
    - EDIT: Leitura e edição de documentos e RAG
    - FULL: Permissão completa (criar pastas, ler, editar, RAG)
    """
    
    READ = "read"
    EDIT = "edit"
    FULL = "full"
    
    def get_display_name(self) -> str:
        """Retorna o nome de exibição do nível de permissão."""
        display_names = {
            self.READ: "Leitura",
            self.EDIT: "Edição",
            self.FULL: "Completa",
        }
        return display_names.get(self, self.value)
    
    def get_description(self) -> str:
        """Retorna a descrição detalhada do nível de permissão."""
        descriptions = {
            self.READ: "Permite apenas ler documentos na pasta e usar RAG com conteúdo dessa pasta",
            self.EDIT: "Permite ler e editar documentos na pasta e usar RAG",
            self.FULL: "Permite criar pastas, ler, editar documentos e usar RAG",
        }
        return descriptions.get(self, "Nível de permissão desconhecido")
    
    def get_allowed_actions(self) -> List[str]:
        """Retorna as ações permitidas para este nível de permissão."""
        actions_map = {
            self.READ: [
                "document:read",
                "document:download",
                "rag:query",
                "ai:query",
            ],
            self.EDIT: [
                "document:read",
                "document:download",
                "document:update",
                "document:share",
                "rag:query",
                "ai:query",
            ],
            self.FULL: [
                "document:read",
                "document:download",
                "document:create",
                "document:update",
                "document:delete",
                "document:share",
                "document:manage",
                "folder:create",
                "folder:update",
                "folder:delete",
                "rag:query",
                "rag:train",
                "ai:query",
                "ai:train",
            ],
        }
        return actions_map.get(self, [])
    
    def can_perform_action(self, action: str) -> bool:
        """Verifica se este nível de permissão permite uma ação específica."""
        allowed_actions = self.get_allowed_actions()
        
        # Verifica ação exata
        if action in allowed_actions:
            return True
        
        # Verifica wildcards
        if ":" in action:
            resource, action_type = action.split(":", 1)
            
            # Verifica se há permissão wildcard para o recurso
            if f"{resource}:*" in allowed_actions:
                return True
        
        return False
    
    def can_create_folders(self) -> bool:
        """Verifica se pode criar pastas."""
        return self == self.FULL
    
    def can_edit_documents(self) -> bool:
        """Verifica se pode editar documentos."""
        return self in [self.EDIT, self.FULL]
    
    def can_read_documents(self) -> bool:
        """Verifica se pode ler documentos."""
        return self in [self.READ, self.EDIT, self.FULL]
    
    def can_use_rag(self) -> bool:
        """Verifica se pode usar RAG."""
        return self in [self.READ, self.EDIT, self.FULL]
    
    def can_train_rag(self) -> bool:
        """Verifica se pode treinar RAG."""
        return self == self.FULL
    
    def is_higher_than(self, other: "FolderPermissionLevel") -> bool:
        """Verifica se este nível é superior ao outro."""
        hierarchy = {
            self.READ: 1,
            self.EDIT: 2,
            self.FULL: 3,
        }
        return hierarchy.get(self, 0) > hierarchy.get(other, 0)
    
    def is_lower_than(self, other: "FolderPermissionLevel") -> bool:
        """Verifica se este nível é inferior ao outro."""
        return other.is_higher_than(self)
    
    def is_equal_to(self, other: "FolderPermissionLevel") -> bool:
        """Verifica se este nível é igual ao outro."""
        return self == other
    
    @classmethod
    def get_all_levels(cls) -> List["FolderPermissionLevel"]:
        """Retorna todos os níveis de permissão disponíveis."""
        return [cls.READ, cls.EDIT, cls.FULL]
    
    @classmethod
    def get_levels_for_role(cls, role_name: str) -> List["FolderPermissionLevel"]:
        """Retorna os níveis de permissão disponíveis para uma role específica."""
        # Administradores e Gerenciadores podem criar perfis com qualquer nível
        if role_name.lower() in ["administrador", "gerenciador"]:
            return cls.get_all_levels()
        
        # Outras roles não podem criar perfis
        return []
    
    @classmethod
    def get_default_level(cls) -> "FolderPermissionLevel":
        """Retorna o nível de permissão padrão."""
        return cls.READ
    
    @classmethod
    def from_string(cls, value: str) -> "FolderPermissionLevel":
        """Cria um nível de permissão a partir de uma string."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid folder permission level: {value}")
    
    def to_dict(self) -> dict:
        """Converte o nível de permissão para um dicionário."""
        return {
            "value": self.value,
            "display_name": self.get_display_name(),
            "description": self.get_description(),
            "allowed_actions": self.get_allowed_actions(),
            "can_create_folders": self.can_create_folders(),
            "can_edit_documents": self.can_edit_documents(),
            "can_read_documents": self.can_read_documents(),
            "can_use_rag": self.can_use_rag(),
            "can_train_rag": self.can_train_rag(),
        }