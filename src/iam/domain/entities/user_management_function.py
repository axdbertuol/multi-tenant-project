from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel


class UserManagementFunction(BaseModel):
    """
    Entidade de domínio para atribuição de funções de gerenciamento a usuários.
    
    Esta entidade representa apenas a parte de gerenciamento de plataforma,
    separada do acesso a documentos que agora está no contexto Documents.
    """
    
    id: UUID
    user_id: UUID
    organization_id: UUID
    function_id: UUID
    assigned_by: UUID
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    metadata: dict = {}
    
    model_config = {"frozen": True}
    
    @classmethod
    def create(
        cls,
        user_id: UUID,
        organization_id: UUID,
        function_id: UUID,
        assigned_by: UUID,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> "UserManagementFunction":
        """Cria uma nova atribuição de função de gerenciamento."""
        return cls(
            id=uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            function_id=function_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
            metadata=metadata or {},
        )
    
    def update_function(self, function_id: UUID) -> "UserManagementFunction":
        """Atualiza a função de gerenciamento do usuário."""
        return self.model_copy(
            update={
                "function_id": function_id,
            }
        )
    
    def deactivate(self) -> "UserManagementFunction":
        """Desativa a atribuição da função."""
        return self.model_copy(
            update={
                "is_active": False,
            }
        )
    
    def activate(self) -> "UserManagementFunction":
        """Ativa a atribuição da função."""
        return self.model_copy(
            update={
                "is_active": True,
            }
        )
    
    def extend_expiration(self, new_expires_at: datetime) -> "UserManagementFunction":
        """Estende a data de expiração da atribuição."""
        return self.model_copy(
            update={
                "expires_at": new_expires_at,
            }
        )
    
    def remove_expiration(self) -> "UserManagementFunction":
        """Remove a data de expiração (atribuição permanente)."""
        return self.model_copy(
            update={
                "expires_at": None,
            }
        )
    
    def update_metadata(self, metadata: dict) -> "UserManagementFunction":
        """Atualiza os metadados da atribuição."""
        new_metadata = {**self.metadata, **metadata}
        return self.model_copy(
            update={
                "metadata": new_metadata,
            }
        )
    
    def is_expired(self) -> bool:
        """Verifica se a atribuição está expirada."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self) -> bool:
        """Verifica se a atribuição é válida (ativa e não expirada)."""
        return self.is_active and not self.is_expired()
    
    def days_until_expiration(self) -> Optional[int]:
        """Retorna quantos dias restam até a expiração."""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - datetime.now(timezone.utc)
        return delta.days if delta.days > 0 else 0
    
    def is_expiring_soon(self, days_threshold: int = 7) -> bool:
        """Verifica se a atribuição está próxima de expirar."""
        if not self.expires_at:
            return False
        
        days_left = self.days_until_expiration()
        return days_left is not None and days_left <= days_threshold
    
    def can_be_renewed(self) -> tuple[bool, str]:
        """Verifica se a atribuição pode ser renovada."""
        if not self.is_active:
            return False, "Cannot renew inactive assignment"
        
        return True, "Assignment can be renewed"
    
    def get_assignment_duration(self) -> int:
        """Retorna a duração da atribuição em dias."""
        if self.expires_at:
            return (self.expires_at - self.assigned_at).days
        return -1  # Atribuição permanente
    
    def has_metadata_key(self, key: str) -> bool:
        """Verifica se existe uma chave específica nos metadados."""
        return key in self.metadata
    
    def get_metadata_value(self, key: str, default=None):
        """Obtém um valor específico dos metadados."""
        return self.metadata.get(key, default)