from typing import Optional
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork

from ..entities.user import User
from ..entities.organization import Organization
from ..value_objects.email import Email
from ..repositories.user_repository import UserRepository
from ..repositories.organization_repository import OrganizationRepository


class UserDomainService:
    """Serviço de domínio para lógica de negócios específica do usuário."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._organization_repository: OrganizationRepository = uow.get_repository("organization")
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

        # Check if user is owner of an organization
        if user.organization_id:
            organization = self._organization_repository.get_by_id(user.organization_id)
            if organization and organization.is_owner(user_id):
                return False, "Cannot delete user who is owner of an organization. Transfer ownership first."

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

        # Check if user is owner of an organization
        if user.organization_id:
            organization = self._organization_repository.get_by_id(user.organization_id)
            if organization and organization.is_owner(user.id):
                return False, "Cannot deactivate user who is owner of an organization. Transfer ownership first."

        return True, "Can be deactivated"

    def can_user_join_organization(self, user_id: UUID, organization_id: UUID) -> tuple[bool, str]:
        """Verifica se o usuário pode ingressar em uma organização."""
        user = self._user_repository.get_by_id(user_id)
        if not user:
            return False, "User not found"

        if user.organization_id is not None:
            return False, "User already belongs to an organization"

        organization = self._organization_repository.get_by_id(organization_id)
        if not organization:
            return False, "Organization not found"

        if not organization.is_active:
            return False, "Cannot join inactive organization"

        # Check organization limits
        current_member_count = self._user_repository.count_users_by_organization(organization_id)
        if not organization.can_add_users(current_member_count + 1):
            return False, "Organization has reached maximum member limit"

        return True, "User can join organization"

    def can_user_leave_organization(self, user_id: UUID) -> tuple[bool, str]:
        """Verifica se o usuário pode sair de sua organização atual."""
        user = self._user_repository.get_by_id(user_id)
        if not user:
            return False, "User not found"

        if user.organization_id is None:
            return False, "User is not a member of any organization"

        organization = self._organization_repository.get_by_id(user.organization_id)
        if organization and organization.is_owner(user_id):
            return False, "Organization owner cannot leave. Transfer ownership first."

        return True, "User can leave organization"
