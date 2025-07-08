from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel


class UserFunctionArea(BaseModel):
    """
    Entidade de domínio para relacionamento entre Usuário, Função e Área.
    
    Esta entidade substitui UserOrganizationRole para o novo modelo onde:
    - Função controla permissões de gerenciamento
    - Área controla acesso a documentos
    """
    
    id: UUID
    user_id: UUID
    organization_id: UUID
    function_id: UUID  # Função de gerenciamento
    area_id: UUID  # Área de documentos
    assigned_by: UUID
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    notes: Optional[str] = None
    
    model_config = {"frozen": True}
    
    @classmethod
    def create(
        cls,
        user_id: UUID,
        organization_id: UUID,
        function_id: UUID,
        area_id: UUID,
        assigned_by: UUID,
        expires_at: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> "UserFunctionArea":
        """
        Cria uma nova atribuição de função e área para usuário.
        
        Args:
            user_id: UUID do usuário
            organization_id: UUID da organização
            function_id: UUID da função de gerenciamento
            area_id: UUID da área de documentos
            assigned_by: UUID do usuário que fez a atribuição
            expires_at: Data de expiração opcional
            notes: Notas opcionais sobre a atribuição
        """
        return cls(
            id=uuid4(),
            user_id=user_id,
            organization_id=organization_id,
            function_id=function_id,
            area_id=area_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
            notes=notes,
        )
    
    def change_function(self, new_function_id: UUID, changed_by: UUID) -> "UserFunctionArea":
        """
        Muda a função do usuário.
        
        Args:
            new_function_id: UUID da nova função
            changed_by: UUID do usuário que fez a mudança
        """
        return self.model_copy(
            update={
                "function_id": new_function_id,
                "assigned_by": changed_by,
                "assigned_at": datetime.now(timezone.utc),
            }
        )
    
    def change_area(self, new_area_id: UUID, changed_by: UUID) -> "UserFunctionArea":
        """
        Muda a área do usuário.
        
        Args:
            new_area_id: UUID da nova área
            changed_by: UUID do usuário que fez a mudança
        """
        return self.model_copy(
            update={
                "area_id": new_area_id,
                "assigned_by": changed_by,
                "assigned_at": datetime.now(timezone.utc),
            }
        )
    
    def change_function_and_area(
        self, 
        new_function_id: UUID, 
        new_area_id: UUID, 
        changed_by: UUID
    ) -> "UserFunctionArea":
        """
        Muda tanto a função quanto a área do usuário.
        
        Args:
            new_function_id: UUID da nova função
            new_area_id: UUID da nova área
            changed_by: UUID do usuário que fez a mudança
        """
        return self.model_copy(
            update={
                "function_id": new_function_id,
                "area_id": new_area_id,
                "assigned_by": changed_by,
                "assigned_at": datetime.now(timezone.utc),
            }
        )
    
    def set_expiration(self, expires_at: datetime) -> "UserFunctionArea":
        """Define data de expiração."""
        return self.model_copy(update={"expires_at": expires_at})
    
    def remove_expiration(self) -> "UserFunctionArea":
        """Remove data de expiração."""
        return self.model_copy(update={"expires_at": None})
    
    def update_notes(self, notes: str) -> "UserFunctionArea":
        """Atualiza as notas da atribuição."""
        return self.model_copy(update={"notes": notes})
    
    def deactivate(self) -> "UserFunctionArea":
        """Desativa a atribuição."""
        return self.model_copy(update={"is_active": False})
    
    def activate(self) -> "UserFunctionArea":
        """Ativa a atribuição."""
        return self.model_copy(
            update={
                "is_active": True,
                "revoked_at": None,
                "revoked_by": None,
            }
        )
    
    def revoke(self, revoked_by: UUID, reason: Optional[str] = None) -> "UserFunctionArea":
        """
        Revoga a atribuição.
        
        Args:
            revoked_by: UUID do usuário que revogou
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
    
    def reactivate(self, reactivated_by: UUID) -> "UserFunctionArea":
        """
        Reativa uma atribuição revogada.
        
        Args:
            reactivated_by: UUID do usuário que reativou
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
        # ou se forem muito antigas
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
        
        if not self.organization_id:
            errors.append("Organization ID is required")
        
        if not self.function_id:
            errors.append("Function ID is required")
        
        if not self.area_id:
            errors.append("Area ID is required")
        
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