from enum import Enum
from typing import List


class AccessLevel(str, Enum):
    """
    Value Object para níveis de acesso a documentos.
    
    Define os diferentes níveis de permissão que um usuário pode ter
    sobre áreas de documentos.
    """
    
    READ = "read"
    WRITE = "write"
    FULL = "full"
    
    def get_allowed_actions(self) -> List[str]:
        """Retorna as ações permitidas para este nível de acesso."""
        if self == AccessLevel.READ:
            return ["read", "download", "view"]
        elif self == AccessLevel.WRITE:
            return ["read", "download", "view", "upload", "create", "edit"]
        elif self == AccessLevel.FULL:
            return ["read", "download", "view", "upload", "create", "edit", "delete", "manage"]
        return []
    
    def can_perform_action(self, action: str) -> bool:
        """Verifica se este nível permite uma ação específica."""
        return action.lower() in self.get_allowed_actions()
    
    def can_read(self) -> bool:
        """Verifica se pode ler documentos."""
        return self in [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.FULL]
    
    def can_write(self) -> bool:
        """Verifica se pode escrever/editar documentos."""
        return self in [AccessLevel.WRITE, AccessLevel.FULL]
    
    def can_delete(self) -> bool:
        """Verifica se pode deletar documentos."""
        return self == AccessLevel.FULL
    
    def can_manage(self) -> bool:
        """Verifica se pode gerenciar permissões."""
        return self == AccessLevel.FULL
    
    def can_create_folders(self) -> bool:
        """Verifica se pode criar pastas."""
        return self in [AccessLevel.WRITE, AccessLevel.FULL]
    
    def is_higher_than(self, other: "AccessLevel") -> bool:
        """Verifica se este nível é superior a outro."""
        hierarchy = {
            AccessLevel.READ: 1,
            AccessLevel.WRITE: 2,
            AccessLevel.FULL: 3
        }
        return hierarchy.get(self, 0) > hierarchy.get(other, 0)
    
    def is_lower_than(self, other: "AccessLevel") -> bool:
        """Verifica se este nível é inferior a outro."""
        return other.is_higher_than(self)
    
    def get_display_name(self) -> str:
        """Retorna nome amigável para exibição."""
        display_names = {
            AccessLevel.READ: "Somente Leitura",
            AccessLevel.WRITE: "Leitura e Escrita",
            AccessLevel.FULL: "Acesso Completo"
        }
        return display_names.get(self, self.value)
    
    def get_description(self) -> str:
        """Retorna descrição detalhada do nível."""
        descriptions = {
            AccessLevel.READ: "Pode visualizar e baixar documentos",
            AccessLevel.WRITE: "Pode visualizar, baixar, criar e editar documentos",
            AccessLevel.FULL: "Pode realizar todas as operações incluindo deletar e gerenciar permissões"
        }
        return descriptions.get(self, "Nível de acesso não definido")
    
    @classmethod
    def get_all_levels(cls) -> List["AccessLevel"]:
        """Retorna todos os níveis de acesso disponíveis."""
        return [cls.READ, cls.WRITE, cls.FULL]
    
    @classmethod
    def get_minimum_level_for_action(cls, action: str) -> "AccessLevel":
        """Retorna o nível mínimo necessário para uma ação."""
        action = action.lower()
        
        if action in ["delete", "manage"]:
            return cls.FULL
        elif action in ["upload", "create", "edit"]:
            return cls.WRITE
        elif action in ["read", "download", "view"]:
            return cls.READ
        else:
            return cls.FULL  # Por segurança, exigir acesso completo para ações desconhecidas