from typing import List, Optional
from uuid import UUID

from domain.repositories.unit_of_work import UnitOfWork
from application.dtos.user_dto import CreateUserDto, UpdateUserDto, UserResponseDto
from application.use_cases.user_use_cases import UserUseCases


class UserService:
    def __init__(self, uow: UnitOfWork):
        self.user_use_cases = UserUseCases(uow)

    async def create_user(self, create_dto: CreateUserDto) -> UserResponseDto:
        return await self.user_use_cases.create_user(create_dto)

    async def get_user_by_id(self, user_id: UUID) -> Optional[UserResponseDto]:
        return await self.user_use_cases.get_user_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[UserResponseDto]:
        return await self.user_use_cases.get_user_by_email(email)

    async def get_all_users(self) -> List[UserResponseDto]:
        return await self.user_use_cases.get_all_users()

    async def update_user(self, user_id: UUID, update_dto: UpdateUserDto) -> Optional[UserResponseDto]:
        return await self.user_use_cases.update_user(user_id, update_dto)

    async def delete_user(self, user_id: UUID) -> bool:
        return await self.user_use_cases.delete_user(user_id)

    async def deactivate_user(self, user_id: UUID) -> Optional[UserResponseDto]:
        return await self.user_use_cases.deactivate_user(user_id)

    async def activate_user(self, user_id: UUID) -> Optional[UserResponseDto]:
        return await self.user_use_cases.activate_user(user_id)