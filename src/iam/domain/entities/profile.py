from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel, Field


class Profile(BaseModel):
    """
    Entidade de domínio para Perfis de Usuário.

    Um perfil define um conjunto de permissões sobre pastas específicas que pode ser
    reutilizado e atribuído a múltiplos usuários. Apenas Administradores e Gerenciadores
    podem criar perfis.
    """

    id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    is_system_profile: bool = False
    profile_metadata: dict = Field(default_factory=dict)

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        organization_id: UUID,
        created_by: UUID,
        is_system_profile: bool = False,
        profile_metadata: Optional[dict] = None,
    ) -> "Profile":
        """
        Cria um novo perfil.

        Args:
            name: Nome do perfil
            description: Descrição do perfil
            organization_id: ID da organização
            created_by: ID do usuário que criou o perfil
            is_system_profile: Se é um perfil do sistema
            profile_metadata: Metadados adicionais
        """
        return cls(
            id=uuid4(),
            name=name.strip(),
            description=description.strip(),
            organization_id=organization_id,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            is_active=True,
            is_system_profile=is_system_profile,
            profile_metadata=profile_metadata or {},
        )

    def update_name(self, name: str) -> "Profile":
        """Atualiza o nome do perfil."""
        if self.is_system_profile:
            raise ValueError("System profiles cannot be renamed")

        return self.model_copy(
            update={
                "name": name.strip(),
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def update_description(self, description: str) -> "Profile":
        """Atualiza a descrição do perfil."""
        if self.is_system_profile:
            raise ValueError("System profiles cannot have description changed")

        return self.model_copy(
            update={
                "description": description.strip(),
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def update_profile_metadata(self, profile_metadata: dict) -> "Profile":
        """Atualiza os metadados do perfil."""
        new_profile_metadata = {**self.profile_metadata, **profile_metadata}
        return self.model_copy(
            update={
                "profile_metadata": new_profile_metadata,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def deactivate(self) -> "Profile":
        """Desativa o perfil."""
        if self.is_system_profile:
            raise ValueError("System profiles cannot be deactivated")

        return self.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def activate(self) -> "Profile":
        """Ativa o perfil."""
        return self.model_copy(
            update={
                "is_active": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def can_be_deleted(self) -> tuple[bool, str]:
        """Verifica se o perfil pode ser deletado."""
        if self.is_system_profile:
            return False, "System profiles cannot be deleted"

        return True, "Profile can be deleted"

    def can_be_modified(self) -> tuple[bool, str]:
        """Verifica se o perfil pode ser modificado."""
        if self.is_system_profile:
            return False, "System profiles cannot be modified"

        if not self.is_active:
            return False, "Inactive profiles cannot be modified"

        return True, "Profile can be modified"

    def validate_name(self) -> tuple[bool, str]:
        """Valida o nome do perfil."""
        if not self.name or not self.name.strip():
            return False, "Profile name cannot be empty"

        if len(self.name.strip()) > 100:
            return False, "Profile name cannot exceed 100 characters"

        # Verificar caracteres especiais não permitidos
        forbidden_chars = ["<", ">", ":", '"', "|", "?", "*", "/", "\\"]
        if any(char in self.name for char in forbidden_chars):
            return False, f"Profile name cannot contain: {', '.join(forbidden_chars)}"

        return True, "Profile name is valid"

    def validate_description(self) -> tuple[bool, str]:
        """Valida a descrição do perfil."""
        if not self.description or not self.description.strip():
            return False, "Profile description cannot be empty"

        if len(self.description.strip()) > 500:
            return False, "Profile description cannot exceed 500 characters"

        return True, "Profile description is valid"

    def validate_profile(self) -> tuple[bool, List[str]]:
        """Valida o perfil completo."""
        errors = []

        # Validar nome
        name_valid, name_error = self.validate_name()
        if not name_valid:
            errors.append(name_error)

        # Validar descrição
        desc_valid, desc_error = self.validate_description()
        if not desc_valid:
            errors.append(desc_error)

        # Validar IDs não nulos
        if not self.organization_id:
            errors.append("Organization ID is required")

        if not self.created_by:
            errors.append("Created by is required")

        return len(errors) == 0, errors

    def has_profile_metadata_key(self, key: str) -> bool:
        """Verifica se existe uma chave específica nos metadados."""
        return key in self.profile_metadata

    def get_profile_metadata_value(self, key: str, default=None):
        """Obtém um valor específico dos metadados."""
        return self.profile_metadata.get(key, default)

    def get_creation_age_days(self) -> int:
        """Retorna a idade do perfil em dias."""
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.days

    def get_last_update_age_days(self) -> Optional[int]:
        """Retorna quantos dias desde a última atualização."""
        if not self.updated_at:
            return None

        delta = datetime.now(timezone.utc) - self.updated_at
        return delta.days

    def is_recently_created(self, days_threshold: int = 7) -> bool:
        """Verifica se o perfil foi criado recentemente."""
        return self.get_creation_age_days() <= days_threshold

    def is_recently_updated(self, days_threshold: int = 7) -> bool:
        """Verifica se o perfil foi atualizado recentemente."""
        if not self.updated_at:
            return False

        update_age = self.get_last_update_age_days()
        return update_age is not None and update_age <= days_threshold

    def get_display_name(self) -> str:
        """Retorna o nome de exibição do perfil."""
        return self.name

    def get_status(self) -> str:
        """Retorna o status atual do perfil."""
        if not self.is_active:
            return "inactive"

        if self.is_system_profile:
            return "system"

        if self.is_recently_created():
            return "new"

        if self.is_recently_updated():
            return "updated"

        return "active"

    def to_summary_dict(self) -> dict:
        """Converte o perfil para um dicionário resumido."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "organization_id": str(self.organization_id),
            "is_active": self.is_active,
            "is_system_profile": self.is_system_profile,
            "status": self.get_status(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
