from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel


class UserProfile(BaseModel):
    """
    Entidade de domínio para relacionamento Many-to-Many entre Usuários e Perfis.
    
    Um usuário pode ter múltiplos perfis e um perfil pode ser atribuído a múltiplos usuários.
    Esta entidade representa essa atribuição com controle de tempo e metadados.
    """
    
    id: UUID
    user_id: UUID
    profile_id: UUID
    organization_id: UUID
    assigned_by: UUID
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    notes: Optional[str] = None
    extra_data: dict = {}
    
    model_config = {"frozen": True}
    
    @classmethod
    def create(
        cls,
        user_id: UUID,
        profile_id: UUID,
        organization_id: UUID,
        assigned_by: UUID,
        expires_at: Optional[datetime] = None,
        notes: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> "UserProfile":
        """
        Cria uma nova atribuição de perfil para usuário.
        
        Args:
            user_id: ID do usuário
            profile_id: ID do perfil
            organization_id: ID da organização
            assigned_by: ID do usuário que fez a atribuição
            expires_at: Data de expiração opcional
            notes: Notas sobre a atribuição
            extra_data: Metadados adicionais
        """
        return cls(
            id=uuid4(),
            user_id=user_id,
            profile_id=profile_id,
            organization_id=organization_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
            notes=notes,
            extra_data=extra_data or {},
        )
    
    def change_profile(self, new_profile_id: UUID, changed_by: UUID) -> "UserProfile":
        """
        Muda o perfil do usuário.
        
        Args:
            new_profile_id: ID do novo perfil
            changed_by: ID do usuário que fez a mudança
        """
        return self.model_copy(
            update={
                "profile_id": new_profile_id,
                "assigned_by": changed_by,
                "assigned_at": datetime.now(timezone.utc),
                "revoked_at": None,
                "revoked_by": None,
            }
        )
    
    def set_expiration(self, expires_at: datetime) -> "UserProfile":
        """Define data de expiração."""
        return self.model_copy(update={"expires_at": expires_at})
    
    def remove_expiration(self) -> "UserProfile":
        """Remove data de expiração."""
        return self.model_copy(update={"expires_at": None})
    
    def update_notes(self, notes: str) -> "UserProfile":
        """Atualiza as notas da atribuição."""
        return self.model_copy(update={"notes": notes})
    
    def update_extra_data(self, extra_data: dict) -> "UserProfile":
        """Atualiza os dados extras da atribuição."""
        new_extra_data = {**self.extra_data, **extra_data}
        return self.model_copy(update={"extra_data": new_extra_data})
    
    def deactivate(self) -> "UserProfile":
        """Desativa a atribuição."""
        return self.model_copy(update={"is_active": False})
    
    def activate(self) -> "UserProfile":
        """Ativa a atribuição."""
        return self.model_copy(
            update={
                "is_active": True,
                "revoked_at": None,
                "revoked_by": None,
            }
        )
    
    def revoke(self, revoked_by: UUID, reason: Optional[str] = None) -> "UserProfile":
        """
        Revoga a atribuição.
        
        Args:
            revoked_by: ID do usuário que revogou
            reason: Motivo da revogação
        """
        notes = self.notes or ""
        if reason:
            notes = f"{notes}\nRevogado: {reason}" if notes else f"Revogado: {reason}"
        
        return self.model_copy(
            update={
                "is_active": False,
                "revoked_at": datetime.now(timezone.utc),
                "revoked_by": revoked_by,
                "notes": notes,
            }
        )
    
    def reactivate(self, reactivated_by: UUID) -> "UserProfile":
        """
        Reativa uma atribuição revogada.
        
        Args:
            reactivated_by: ID do usuário que reativou
        """
        return self.model_copy(
            update={
                "is_active": True,
                "revoked_at": None,
                "revoked_by": None,
                "assigned_by": reactivated_by,
                "assigned_at": datetime.now(timezone.utc),
            }
        )
    
    def extend_expiration(self, new_expires_at: datetime) -> "UserProfile":
        """Estende a data de expiração."""
        return self.model_copy(update={"expires_at": new_expires_at})
    
    def is_expired(self) -> bool:
        """Verifica se a atribuição expirou."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self) -> bool:
        """Verifica se a atribuição está válida (ativa e não expirada)."""
        return self.is_active and not self.is_expired()
    
    def is_revoked(self) -> bool:
        """Verifica se a atribuição foi revogada."""
        return self.revoked_at is not None
    
    def days_until_expiry(self) -> Optional[int]:
        """Retorna quantos dias até a expiração."""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    def is_expiring_soon(self, days_ahead: int = 7) -> bool:
        """Verifica se a atribuição expira em breve."""
        if not self.expires_at:
            return False
        
        days_until = self.days_until_expiry()
        return days_until is not None and days_until <= days_ahead
    
    def get_assignment_duration(self) -> int:
        """Retorna a duração da atribuição em dias."""
        end_time = self.revoked_at or datetime.now(timezone.utc)
        delta = end_time - self.assigned_at
        return delta.days
    
    def can_be_modified(self) -> tuple[bool, str]:
        """Verifica se a atribuição pode ser modificada."""
        if not self.is_active:
            return False, "Inactive assignments cannot be modified"
        
        if self.is_expired():
            return False, "Expired assignments cannot be modified"
        
        return True, "Assignment can be modified"
    
    def can_be_deleted(self) -> tuple[bool, str]:
        """Verifica se a atribuição pode ser deletada."""
        # Atribuições podem ser deletadas se não estiverem ativas
        if not self.is_active:
            return True, "Inactive assignment can be deleted"
        
        # Verificar se é uma atribuição muito antiga
        duration = self.get_assignment_duration()
        if duration > 365:  # Mais de 1 ano
            return True, "Old assignment can be deleted"
        
        return False, "Active recent assignments should be revoked instead of deleted"
    
    def validate_assignment(self) -> tuple[bool, list[str]]:
        """Valida se a atribuição está correta."""
        errors = []
        
        # Verificar se os IDs não são nulos
        if not self.user_id:
            errors.append("User ID is required")
        
        if not self.profile_id:
            errors.append("Profile ID is required")
        
        if not self.organization_id:
            errors.append("Organization ID is required")
        
        if not self.assigned_by:
            errors.append("Assigned by is required")
        
        # Verificar se data de expiração está no futuro
        if self.expires_at and self.expires_at <= datetime.now(timezone.utc):
            errors.append("Expiration date must be in the future")
        
        # Verificar se data de atribuição é válida
        if self.assigned_at > datetime.now(timezone.utc):
            errors.append("Assignment date cannot be in the future")
        
        # Verificar consistência de revogação
        if self.revoked_at and not self.revoked_by:
            errors.append("Revoked assignments must have revoked_by")
        
        if self.revoked_by and not self.revoked_at:
            errors.append("Revoked_by requires revoked_at")
        
        return len(errors) == 0, errors
    
    def get_status(self) -> str:
        """Retorna o status atual da atribuição."""
        if not self.is_active:
            if self.is_revoked():
                return "revoked"
            return "inactive"
        
        if self.is_expired():
            return "expired"
        
        if self.is_expiring_soon():
            return "expiring_soon"
        
        return "active"
    
    def has_extra_data_key(self, key: str) -> bool:
        """Verifica se existe uma chave específica nos dados extras."""
        return key in self.extra_data
    
    def get_extra_data_value(self, key: str, default=None):
        """Obtém um valor específico dos dados extras."""
        return self.extra_data.get(key, default)
    
    def is_permanent_assignment(self) -> bool:
        """Verifica se é uma atribuição permanente (sem data de expiração)."""
        return self.expires_at is None
    
    def is_temporary_assignment(self) -> bool:
        """Verifica se é uma atribuição temporária (com data de expiração)."""
        return self.expires_at is not None
    
    def get_assignment_type(self) -> str:
        """Retorna o tipo de atribuição."""
        if self.is_permanent_assignment():
            return "permanent"
        return "temporary"
    
    def to_summary_dict(self) -> dict:
        """Converte a atribuição para um dicionário resumido."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "profile_id": str(self.profile_id),
            "organization_id": str(self.organization_id),
            "assigned_by": str(self.assigned_by),
            "assigned_at": self.assigned_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "status": self.get_status(),
            "assignment_type": self.get_assignment_type(),
            "days_until_expiry": self.days_until_expiry(),
            "is_expired": self.is_expired(),
            "is_expiring_soon": self.is_expiring_soon(),
        }