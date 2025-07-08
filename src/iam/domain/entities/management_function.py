from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum


class ManagementFunctionType(str, Enum):
    """Types of management functions."""
    ADMIN = "admin"
    GERENCIADOR = "gerenciador"
    MEMBRO = "membro"


class ManagementFunction(BaseModel):
    """
    Entidade de domínio para Funções de Gerenciamento.
    
    Controla exclusivamente permissões dentro da plataforma de gerenciamento.
    Substitui o uso de Role para contexto de gerenciamento.
    """
    
    id: UUID
    name: str  # "admin", "gerenciador", "membro"
    description: str
    organization_id: UUID
    permissions: List[str]  # Permissões específicas de gerenciamento
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: UUID
    is_active: bool = True
    is_system_function: bool = False
    
    model_config = {"frozen": True}
    
    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        organization_id: UUID,
        permissions: List[str],
        created_by: UUID,
        is_system_function: bool = False,
    ) -> "ManagementFunction":
        """Cria uma nova função de gerenciamento."""
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            organization_id=organization_id,
            permissions=permissions,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            is_active=True,
            is_system_function=is_system_function,
        )
    
    def update_description(self, description: str) -> "ManagementFunction":
        """Atualiza a descrição da função."""
        return self.model_copy(
            update={
                "description": description,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def update_permissions(self, permissions: List[str]) -> "ManagementFunction":
        """Atualiza as permissões da função."""
        if self.is_system_function:
            raise ValueError("System functions cannot have permissions modified")
        
        return self.model_copy(
            update={
                "permissions": permissions,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def add_permission(self, permission: str) -> "ManagementFunction":
        """Adiciona uma permissão à função."""
        if self.is_system_function:
            raise ValueError("System functions cannot have permissions modified")
        
        if permission not in self.permissions:
            new_permissions = self.permissions + [permission]
            return self.model_copy(
                update={
                    "permissions": new_permissions,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        return self
    
    def remove_permission(self, permission: str) -> "ManagementFunction":
        """Remove uma permissão da função."""
        if self.is_system_function:
            raise ValueError("System functions cannot have permissions modified")
        
        if permission in self.permissions:
            new_permissions = [p for p in self.permissions if p != permission]
            return self.model_copy(
                update={
                    "permissions": new_permissions,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        return self
    
    def has_permission(self, permission: str) -> bool:
        """Verifica se a função tem uma permissão específica."""
        if not self.is_active:
            return False
        
        # Verifica permissão exata
        if permission in self.permissions:
            return True
        
        # Verifica wildcards
        resource, action = permission.split(":", 1) if ":" in permission else (permission, "")
        
        # Verifica wildcard do recurso (ex: "management:*")
        if f"{resource}:*" in self.permissions:
            return True
        
        # Verifica wildcard global (ex: "*:*")
        if "*:*" in self.permissions:
            return True
        
        return False
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Verifica se a função tem qualquer uma das permissões especificadas."""
        return any(self.has_permission(perm) for perm in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Verifica se a função tem todas as permissões especificadas."""
        return all(self.has_permission(perm) for perm in permissions)
    
    def deactivate(self) -> "ManagementFunction":
        """Desativa a função."""
        if self.is_system_function:
            raise ValueError("System functions cannot be deactivated")
        
        return self.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def activate(self) -> "ManagementFunction":
        """Ativa a função."""
        return self.model_copy(
            update={
                "is_active": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def can_be_deleted(self) -> tuple[bool, str]:
        """Verifica se a função pode ser deletada."""
        if self.is_system_function:
            return False, "System functions cannot be deleted"
        
        return True, "Function can be deleted"
    
    def is_management_admin(self) -> bool:
        """Verifica se é uma função de administrador de gerenciamento."""
        return self.has_permission("management:*") or self.has_permission("*:*")
    
    def get_management_permissions(self) -> List[str]:
        """Retorna apenas as permissões de gerenciamento."""
        return [perm for perm in self.permissions if perm.startswith("management:")]
    
    def validate_permissions(self) -> tuple[bool, List[str]]:
        """Valida se as permissões da função são válidas."""
        errors = []
        
        # Lista de permissões válidas de gerenciamento
        valid_management_permissions = [
            "management:read",
            "management:create",
            "management:update",
            "management:delete",
            "management:manage",
            "management:*",
            "users:read",
            "users:create",
            "users:update",
            "users:delete",
            "users:manage",
            "users:*",
            "organizations:read",
            "organizations:update",
            "organizations:manage",
            "roles:read",
            "roles:create",
            "roles:update",
            "roles:delete",
            "roles:manage",
            "functions:read",
            "functions:create",
            "functions:update",
            "functions:delete",
            "functions:manage",
            "areas:read",
            "areas:create",
            "areas:update",
            "areas:delete",
            "areas:manage",
            "*:*",
        ]
        
        for permission in self.permissions:
            if permission not in valid_management_permissions:
                errors.append(f"Invalid management permission: {permission}")
        
        return len(errors) == 0, errors