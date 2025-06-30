from typing import Optional
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork

from ..entities.user import User
from ..value_objects.email import Email
from ..repositories.user_repository import UserRepository


class UserDomainService:
    """Serviço de domínio para lógica de negócios específica do usuário."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._uow = uow

    def is_email_available(
        self, email: Email, excluding_user_id: Optional[UUID] = None
    ) -> bool:
        """Verifica se o email está disponível para registro ou atualização."""
        existing_user = self._user_repository.get_by_email(email)

        if not existing_user:
            return True

        # If excluding a specific user (for updates), check if it's the same user
        if excluding_user_id and existing_user.id == excluding_user_id:
            return True

        return False

    def can_user_be_deleted(self, user_id: UUID) -> tuple[bool, str]:
        """Verifica se o usuário pode ser excluído com segurança e retorna o motivo, se não."""
        user = self._user_repository.get_by_id(user_id)

        if not user:
            return False, "User not found"

        # Add business rules for user deletion
        # For example: check if user is the only admin of an organization

        return True, "Can be deleted"

    def validate_user_activation(self, user: User) -> tuple[bool, str]:
        """Valida se o usuário pode ser ativado."""
        if user.is_active:
            return False, "User is already active"

        # Add more business rules as needed
        return True, "Can be activated"

    def validate_user_deactivation(self, user: User) -> tuple[bool, str]:
        """Valida se o usuário pode ser desativado."""
        if not user.is_active:
            return False, "User is already inactive"

        # Add business rules (e.g., check if user is sole admin of organizations)
        return True, "Can be deactivated"
