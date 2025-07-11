from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel, Field

from ..value_objects.email import Email
from ..value_objects.password import Password


class User(BaseModel):
    """Entidade de domínio do Usuário."""

    id: UUID
    email: Email
    name: str
    password: Password
    organization_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    is_verified: bool = True
    last_login_at: Optional[datetime] = None
    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls,
        email: str,
        name: str,
        password: str,
        organization_id: Optional[UUID] = None,
    ) -> "User":
        """Cria uma nova instância de Usuário."""
        return cls(
            id=uuid4(),
            email=Email(value=email),
            name=name,
            password=Password.create(password),
            organization_id=organization_id,
            created_at=datetime.now(timezone.utc),
            is_active=True,
            is_verified=True,
        )

    def update_name(self, name: str) -> "User":
        """Atualiza o nome do usuário."""
        return self.model_copy(
            update={"name": name, "updated_at": datetime.now(timezone.utc)}
        )

    def deactivate(self) -> "User":
        """Desativa a conta do usuário."""
        return self.model_copy(
            update={"is_active": False, "updated_at": datetime.now(timezone.utc)}
        )

    def activate(self) -> "User":
        """Ativa a conta do usuário."""
        return self.model_copy(
            update={"is_active": True, "updated_at": datetime.now(timezone.utc)}
        )

    def change_password(self, new_password: str) -> "User":
        """Altera a senha do usuário."""
        return self.model_copy(
            update={
                "password": Password.create(new_password),
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def verify_password(self, plain_password: str) -> bool:
        """Verifica se a senha fornecida corresponde à senha hash do usuário."""
        return self.password.verify(plain_password)

    def update_last_login(self, login_time: datetime) -> "User":
        """Atualiza o timestamp do último login do usuário."""
        return self.model_copy(
            update={
                "last_login_at": login_time,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def join_organization(self, organization_id: UUID) -> "User":
        """Adiciona o usuário a uma organização."""
        if self.organization_id is not None:
            raise ValueError("User is already a member of an organization")

        return self.model_copy(
            update={
                "organization_id": organization_id,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def leave_organization(self) -> "User":
        """Remove o usuário de sua organização atual."""
        if self.organization_id is None:
            raise ValueError("User is not a member of any organization")

        return self.model_copy(
            update={"organization_id": None, "updated_at": datetime.now(timezone.utc)}
        )

    def can_access_organization(self, organization_id: UUID) -> bool:
        """Regra de domínio: O usuário pode acessar a organização à qual pertence."""
        return self.is_active and self.organization_id == organization_id

    def is_member_of_organization(self, organization_id: UUID) -> bool:
        """Verifica se o usuário é membro de uma organização específica."""
        return self.organization_id == organization_id

    def has_organization(self) -> bool:
        """Verifica se o usuário pertence a alguma organização."""
        return self.organization_id is not None
