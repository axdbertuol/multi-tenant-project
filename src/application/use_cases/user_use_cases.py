from typing import List, Optional
from uuid import UUID

from domain.entities.user import User
from domain.repositories.unit_of_work import UnitOfWork
from application.dtos.user_dto import CreateUserDto, UpdateUserDto, UserResponseDto


class UserUseCases:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _to_response_dto(self, user: User) -> UserResponseDto:
        return UserResponseDto(
            id=user.id,
            email=str(user.email.value),
            name=user.name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active
        )

    async def create_user(self, create_dto: CreateUserDto) -> UserResponseDto:
        async with self.uow:
            existing_user = await self.uow.users.get_by_email(create_dto.email)
            if existing_user:
                raise ValueError(f"User with email {create_dto.email} already exists")

            user = User.create(email=create_dto.email, name=create_dto.name)
            created_user = await self.uow.users.create(user)
            return self._to_response_dto(created_user)

    async def get_user_by_id(self, user_id: UUID) -> Optional[UserResponseDto]:
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            return self._to_response_dto(user) if user else None

    async def get_user_by_email(self, email: str) -> Optional[UserResponseDto]:
        async with self.uow:
            user = await self.uow.users.get_by_email(email)
            return self._to_response_dto(user) if user else None

    async def get_all_users(self) -> List[UserResponseDto]:
        async with self.uow:
            users = await self.uow.users.get_all()
            return [self._to_response_dto(user) for user in users]

    async def update_user(self, user_id: UUID, update_dto: UpdateUserDto) -> Optional[UserResponseDto]:
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                return None

            updated_user = user
            if update_dto.name:
                updated_user = user.update_name(update_dto.name)

            final_user = await self.uow.users.update(updated_user)
            return self._to_response_dto(final_user)

    async def delete_user(self, user_id: UUID) -> bool:
        async with self.uow:
            return await self.uow.users.delete(user_id)

    async def deactivate_user(self, user_id: UUID) -> Optional[UserResponseDto]:
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                return None

            deactivated_user = user.deactivate()
            updated_user = await self.uow.users.update(deactivated_user)
            return self._to_response_dto(updated_user)

    async def activate_user(self, user_id: UUID) -> Optional[UserResponseDto]:
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                return None

            activated_user = user.activate()
            updated_user = await self.uow.users.update(activated_user)
            return self._to_response_dto(updated_user)