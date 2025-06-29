from typing import Optional
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork

from ..entities.user import User
from ..value_objects.email import Email
from ..repositories.user_repository import UserRepository


class UserDomainService:
    """Domain service for user-specific business logic."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._uow = uow

    def is_email_available(
        self, email: Email, excluding_user_id: Optional[UUID] = None
    ) -> bool:
        """Check if email is available for registration or update."""
        existing_user = self._user_repository.get_by_email(email)

        if not existing_user:
            return True

        # If excluding a specific user (for updates), check if it's the same user
        if excluding_user_id and existing_user.id == excluding_user_id:
            return True

        return False

    def can_user_be_deleted(self, user_id: UUID) -> tuple[bool, str]:
        """Check if user can be safely deleted and return reason if not."""
        user = self._user_repository.get_by_id(user_id)

        if not user:
            return False, "User not found"

        # Add business rules for user deletion
        # For example: check if user is the only admin of an organization

        return True, "Can be deleted"

    def validate_user_activation(self, user: User) -> tuple[bool, str]:
        """Validate if user can be activated."""
        if user.is_active:
            return False, "User is already active"

        # Add more business rules as needed
        return True, "Can be activated"

    def validate_user_deactivation(self, user: User) -> tuple[bool, str]:
        """Validate if user can be deactivated."""
        if not user.is_active:
            return False, "User is already inactive"

        # Add business rules (e.g., check if user is sole admin of organizations)
        return True, "Can be deactivated"
