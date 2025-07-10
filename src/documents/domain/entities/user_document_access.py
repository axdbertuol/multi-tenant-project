from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel, Field

from ..value_objects.access_level import AccessLevel


class UserDocumentAccess(BaseModel):
    """
    Entidade de domínio para acesso de usuários a documentos.
    
    Representa a atribuição de áreas de documentos a usuários com controle
    granular de níveis de acesso.
    """
    
    id: UUID
    user_id: UUID
    area_id: UUID
    organization_id: UUID
    access_level: AccessLevel
    granted_by: UUID
    granted_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    notes: Optional[str] = None
    extra_data: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"frozen": True}
    
    @classmethod
    def create(
        cls,
        user_id: UUID,
        area_id: UUID,
        organization_id: UUID,
        access_level: AccessLevel,
        granted_by: UUID,
        expires_at: Optional[datetime] = None,
        notes: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> "UserDocumentAccess":
        """Cria um novo acesso de usuário a documentos."""
        now = datetime.now(timezone.utc)
        
        return cls(
            id=uuid4(),
            user_id=user_id,
            area_id=area_id,
            organization_id=organization_id,
            access_level=access_level,
            granted_by=granted_by,
            granted_at=now,
            expires_at=expires_at,
            is_active=True,
            notes=notes,
            extra_data=extra_data or {},
            created_at=now,
        )
    
    def change_access_level(self, new_access_level: AccessLevel) -> "UserDocumentAccess":
        """Altera o nível de acesso."""
        return self.model_copy(
            update={
                "access_level": new_access_level,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def extend_access(self, new_expires_at: Optional[datetime]) -> "UserDocumentAccess":
        """Estende ou remove data de expiração."""
        return self.model_copy(
            update={
                "expires_at": new_expires_at,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def update_notes(self, notes: str) -> "UserDocumentAccess":
        """Atualiza as notas do acesso."""
        return self.model_copy(
            update={
                "notes": notes,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def update_extra_data(self, extra_data: dict) -> "UserDocumentAccess":
        """Atualiza os dados extras do acesso."""
        new_extra_data = {**self.extra_data, **extra_data}
        return self.model_copy(
            update={
                "extra_data": new_extra_data,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def revoke(self, revoked_by: UUID, reason: Optional[str] = None) -> "UserDocumentAccess":
        """Revoga o acesso."""
        notes = self.notes or ""
        if reason:
            notes = f"{notes}\nRevogado: {reason}" if notes else f"Revogado: {reason}"
        
        return self.model_copy(
            update={
                "is_active": False,
                "revoked_at": datetime.now(timezone.utc),
                "revoked_by": revoked_by,
                "notes": notes,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def reactivate(self, reactivated_by: UUID) -> "UserDocumentAccess":
        """Reativa um acesso revogado."""
        return self.model_copy(
            update={
                "is_active": True,
                "revoked_at": None,
                "revoked_by": None,
                "granted_by": reactivated_by,
                "granted_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def deactivate(self) -> "UserDocumentAccess":
        """Desativa o acesso."""
        return self.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def activate(self) -> "UserDocumentAccess":
        """Ativa o acesso."""
        return self.model_copy(
            update={
                "is_active": True,
                "revoked_at": None,
                "revoked_by": None,
                "updated_at": datetime.now(timezone.utc),
            }
        )
    
    def is_expired(self) -> bool:
        """Verifica se o acesso expirou."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self) -> bool:
        """Verifica se o acesso está válido (ativo e não expirado)."""
        return self.is_active and not self.is_expired()
    
    def is_revoked(self) -> bool:
        """Verifica se o acesso foi revogado."""
        return self.revoked_at is not None
    
    def days_until_expiry(self) -> Optional[int]:
        """Retorna quantos dias até a expiração."""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    def is_expiring_soon(self, days_ahead: int = 7) -> bool:
        """Verifica se o acesso expira em breve."""
        if not self.expires_at:
            return False
        
        days_until = self.days_until_expiry()
        return days_until is not None and days_until <= days_ahead
    
    def get_access_duration(self) -> int:
        """Retorna a duração do acesso em dias."""
        end_time = self.revoked_at or datetime.now(timezone.utc)
        delta = end_time - self.granted_at
        return delta.days
    
    def can_perform_action(self, action: str) -> bool:
        """Verifica se o acesso permite uma ação específica."""
        if not self.is_valid():
            return False
        
        return self.access_level.can_perform_action(action)
    
    def get_allowed_actions(self) -> List[str]:
        """Retorna as ações permitidas por este acesso."""
        if not self.is_valid():
            return []
        
        return self.access_level.get_allowed_actions()
    
    def can_be_modified(self) -> tuple[bool, str]:
        """Verifica se o acesso pode ser modificado."""
        if not self.is_active:
            return False, "Inactive access cannot be modified"
        
        if self.is_expired():
            return False, "Expired access cannot be modified"
        
        return True, "Access can be modified"
    
    def can_be_deleted(self) -> tuple[bool, str]:
        """Verifica se o acesso pode ser deletado."""
        # Acessos podem ser deletados se não estiverem ativos
        if not self.is_active:
            return True, "Inactive access can be deleted"
        
        # Verificar se é um acesso muito antigo
        duration = self.get_access_duration()
        if duration > 365:  # Mais de 1 ano
            return True, "Old access can be deleted"
        
        return False, "Active recent access should be revoked instead of deleted"
    
    def validate_access(self) -> tuple[bool, List[str]]:
        """Valida se o acesso está correto."""
        errors = []
        
        # Verificar se os IDs não são nulos
        if not self.user_id:
            errors.append("User ID is required")
        
        if not self.area_id:
            errors.append("Area ID is required")
        
        if not self.organization_id:
            errors.append("Organization ID is required")
        
        if not self.granted_by:
            errors.append("Granted by is required")
        
        # Verificar se data de expiração está no futuro
        if self.expires_at and self.expires_at <= datetime.now(timezone.utc):
            errors.append("Expiration date must be in the future")
        
        # Verificar se data de concessão é válida
        if self.granted_at > datetime.now(timezone.utc):
            errors.append("Grant date cannot be in the future")
        
        # Verificar consistência de revogação
        if self.revoked_at and not self.revoked_by:
            errors.append("Revoked access must have revoked_by")
        
        if self.revoked_by and not self.revoked_at:
            errors.append("Revoked_by requires revoked_at")
        
        return len(errors) == 0, errors
    
    def get_status(self) -> str:
        """Retorna o status atual do acesso."""
        if not self.is_active:
            if self.is_revoked():
                return "revoked"
            return "inactive"
        
        if self.is_expired():
            return "expired"
        
        if self.is_expiring_soon():
            return "expiring_soon"
        
        return "active"
    
    def is_permanent_access(self) -> bool:
        """Verifica se é um acesso permanente (sem data de expiração)."""
        return self.expires_at is None
    
    def is_temporary_access(self) -> bool:
        """Verifica se é um acesso temporário (com data de expiração)."""
        return self.expires_at is not None
    
    def get_access_type(self) -> str:
        """Retorna o tipo de acesso."""
        if self.is_permanent_access():
            return "permanent"
        return "temporary"
    
    def to_summary_dict(self) -> dict:
        """Converte o acesso para um dicionário resumido."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "area_id": str(self.area_id),
            "organization_id": str(self.organization_id),
            "access_level": self.access_level.value,
            "access_level_display": self.access_level.get_display_name(),
            "granted_by": str(self.granted_by),
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "status": self.get_status(),
            "access_type": self.get_access_type(),
            "days_until_expiry": self.days_until_expiry(),
            "is_expired": self.is_expired(),
            "is_expiring_soon": self.is_expiring_soon(),
        }