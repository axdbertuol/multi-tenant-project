from typing import Optional
from uuid import UUID
import math

from shared.domain.repositories.unit_of_work import UnitOfWork

from ..dtos.user_dto import (
    UserCreateDTO,
    UserUpdateDTO,
    UserChangePasswordDTO,
    UserResponseDTO,
    UserListResponseDTO,
)
from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository
from ...domain.services.user_domain_service import UserDomainService
from ...domain.value_objects.email import Email


class UserUseCase:
    """Casos de uso para gerenciamento de usuários."""

    def __init__(self, uow: UnitOfWork):
        self._user_repository: UserRepository = uow.get_repository("user")
        self._user_domain_service = UserDomainService(uow)
        self._uow = uow

    def create_user(self, dto: UserCreateDTO) -> UserResponseDTO:
        """Cria um novo usuário."""
        with self._uow:
            # Check if email is available
            email_vo = Email(value=dto.email)
            is_available = self._user_domain_service.is_email_available(email_vo)

            if not is_available:
                raise ValueError(f"Email {dto.email} is already in use")

            # Create user entity
            user = User.create(email=dto.email, name=dto.name, password=dto.password)

            # Save user
            saved_user = self._user_repository.save(user)

        return UserResponseDTO.model_validate(saved_user)

    def get_user_by_id(self, user_id: UUID) -> Optional[UserResponseDTO]:
        """Obtém um usuário pelo ID."""
        user = self._user_repository.get_by_id(user_id)

        if not user:
            return None

        return UserResponseDTO.model_validate(user)

    def get_user_by_email(self, email: str) -> Optional[UserResponseDTO]:
        """Obtém um usuário pelo email."""
        email_vo = Email(value=email)
        user = self._user_repository.get_by_email(email_vo)

        if not user:
            return None

        return UserResponseDTO.model_validate(user)

    def update_user(self, user_id: UUID, dto: UserUpdateDTO) -> UserResponseDTO:
        """Atualiza as informações do usuário."""
        with self._uow:
            user = self._user_repository.get_by_id(user_id)

            if not user:
                raise ValueError("User not found")

            updated_user = user

            # Update name if provided
            if dto.name is not None:
                updated_user = updated_user.update_name(dto.name)

            # Update active status if provided
            if dto.is_active is not None:
                if dto.is_active and not user.is_active:
                    can_activate, reason = (
                        self._user_domain_service.validate_user_activation(user)
                    )
                    if not can_activate:
                        raise ValueError(f"Cannot activate user: {reason}")
                    updated_user = updated_user.activate()
                elif not dto.is_active and user.is_active:
                    can_deactivate, reason = (
                        self._user_domain_service.validate_user_deactivation(user)
                    )
                    if not can_deactivate:
                        raise ValueError(f"Cannot deactivate user: {reason}")
                    updated_user = updated_user.deactivate()

            # Save updated user
            saved_user = self._user_repository.save(updated_user)

        return UserResponseDTO.model_validate(saved_user)

    def change_password(self, user_id: UUID, dto: UserChangePasswordDTO) -> bool:
        """Altera a senha do usuário."""
        with self._uow:
            user = self._user_repository.get_by_id(user_id)

            if not user:
                raise ValueError("User not found")

            # Verify current password
            if not user.verify_password(dto.current_password):
                raise ValueError("Current password is incorrect")

            # Update password
            updated_user = user.change_password(dto.new_password)
            self._user_repository.save(updated_user)

        return True

    def deactivate_user(self, user_id: UUID) -> UserResponseDTO:
        """Desativa a conta do usuário."""
        with self._uow:
            user = self._user_repository.get_by_id(user_id)

            if not user:
                raise ValueError("User not found")

            can_deactivate, reason = self._user_domain_service.validate_user_deactivation(
                user
            )
            if not can_deactivate:
                raise ValueError(f"Cannot deactivate user: {reason}")

            updated_user = user.deactivate()
            saved_user = self._user_repository.save(updated_user)

        return UserResponseDTO.model_validate(saved_user)

    def activate_user(self, user_id: UUID) -> UserResponseDTO:
        """Ativa a conta do usuário."""
        with self._uow:
            user = self._user_repository.get_by_id(user_id)

            if not user:
                raise ValueError("User not found")

            can_activate, reason = self._user_domain_service.validate_user_activation(user)
            if not can_activate:
                raise ValueError(f"Cannot activate user: {reason}")

            updated_user = user.activate()
            saved_user = self._user_repository.save(updated_user)

        return UserResponseDTO.model_validate(saved_user)

    def delete_user(self, user_id: UUID) -> bool:
        """Exclui a conta do usuário."""
        with self._uow:
            can_delete, reason = self._user_domain_service.can_user_be_deleted(user_id)

            if not can_delete:
                raise ValueError(f"Cannot delete user: {reason}")

            result = self._user_repository.delete(user_id)

        return result

    def list_users(
        self, page: int = 1, page_size: int = 100, active_only: bool = True
    ) -> UserListResponseDTO:
        """Lista usuários com paginação."""

        if page < 1:
            page = 1

        if page_size < 1 or page_size > 1000:
            page_size = 100

        offset = (page - 1) * page_size

        # Get users
        users = self._user_repository.list_active_users(limit=page_size, offset=offset)

        # Get total count
        total = self._user_repository.count_active_users()

        # Convert to DTOs
        user_dtos = [UserResponseDTO.model_validate(user) for user in users]

        total_pages = math.ceil(total / page_size)

        return UserListResponseDTO(
            users=user_dtos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def check_email_availability(
        self, email: str, excluding_user_id: Optional[UUID] = None
    ) -> bool:
        """Verifica se o email está disponível para uso."""
        email_vo = Email(value=email)
        return self._user_domain_service.is_email_available(email_vo, excluding_user_id)

