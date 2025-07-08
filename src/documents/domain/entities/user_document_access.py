from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel


class UserDocumentAccess(BaseModel):
    """
    Entidade de domínio para acesso de usuários a documentos.
    
    Representa a atribuição de áreas de documentos a usuários, separada das 
    funções de gerenciamento que ficam no contexto IAM.
    """
    
    id: UUID
    user_id: UUID
    organization_id: UUID
    area_id: UUID
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
        area_id: UUID,
        assigned_by: UUID,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> "UserDocumentAccess":
        """Cria um novo acesso de usuário a documentos."""
        return cls(
            id=uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            area_id=area_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
            metadata=metadata or {},
        )
    
    def update_area(self, area_id: UUID) -> "UserDocumentAccess":
        """Atualiza a área de acesso do usuário."""
        return self.model_copy(
            update={
                "area_id": area_id,
            }
        )
    
    def deactivate(self) -> "UserDocumentAccess":
        """Desativa o acesso do usuário."""
        return self.model_copy(
            update={
                "is_active": False,
            }
        )
    
    def activate(self) -> "UserDocumentAccess":
        """Ativa o acesso do usuário."""
        return self.model_copy(
            update={
                "is_active": True,
            }
        )
    
    def extend_expiration(self, new_expires_at: datetime) -> "UserDocumentAccess":
        """Estende a data de expiração do acesso."""
        return self.model_copy(
            update={
                "expires_at": new_expires_at,
            }
        )
    
    def remove_expiration(self) -> "UserDocumentAccess":
        """Remove a data de expiração (acesso permanente)."""
        return self.model_copy(
            update={
                "expires_at": None,
            }
        )
    
    def update_metadata(self, metadata: dict) -> "UserDocumentAccess":
        """Atualiza os metadados do acesso."""
        new_metadata = {**self.metadata, **metadata}
        return self.model_copy(
            update={
                "metadata": new_metadata,
            }
        )
    
    def is_expired(self) -> bool:
        """Verifica se o acesso está expirado."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self) -> bool:
        """Verifica se o acesso é válido (ativo e não expirado)."""
        return self.is_active and not self.is_expired()
    
    def days_until_expiration(self) -> Optional[int]:
        """Retorna quantos dias restam até a expiração."""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - datetime.now(timezone.utc)
        return delta.days if delta.days > 0 else 0
    
    def is_expiring_soon(self, days_threshold: int = 7) -> bool:
        """Verifica se o acesso está próximo de expirar."""
        if not self.expires_at:
            return False
        
        days_left = self.days_until_expiration()
        return days_left is not None and days_left <= days_threshold
    
    def can_be_renewed(self) -> tuple[bool, str]:
        """Verifica se o acesso pode ser renovado."""
        if not self.is_active:
            return False, "Cannot renew inactive access"
        
        return True, "Access can be renewed"
    
    def get_assignment_duration(self) -> int:
        """Retorna a duração da atribuição em dias."""
        if self.expires_at:
            return (self.expires_at - self.assigned_at).days
        return -1  # Acesso permanente
    
    def has_metadata_key(self, key: str) -> bool:
        """Verifica se existe uma chave específica nos metadados."""
        return key in self.metadata
    
    def get_metadata_value(self, key: str, default=None):
        """Obtém um valor específico dos metadados."""
        return self.metadata.get(key, default)