from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from application.dtos.user_dto import CreateUserDto, UpdateUserDto, UserResponseDto
from application.services.user_service import UserService
from infrastructure.database.dependencies import get_unit_of_work
from infrastructure.repositories.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(uow: SQLAlchemyUnitOfWork = Depends(get_unit_of_work)) -> UserService:
    return UserService(uow)


@router.post("/", response_model=UserResponseDto, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=UserResponseDto, status_code=status.HTTP_201_CREATED)  # Sem trailing slash
async def create_user(
    create_dto: CreateUserDto,
    user_service: UserService = Depends(get_user_service)
):
    try:
        return await user_service.create_user(create_dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=UserResponseDto)
async def get_user_by_id(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/", response_model=List[UserResponseDto])
async def get_all_users(
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_all_users()


@router.put("/{user_id}", response_model=UserResponseDto)
async def update_user(
    user_id: UUID,
    update_dto: UpdateUserDto,
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.update_user(user_id, update_dto)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.patch("/{user_id}/deactivate", response_model=UserResponseDto)
async def deactivate_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.deactivate_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}/activate", response_model=UserResponseDto)
async def activate_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.activate_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user