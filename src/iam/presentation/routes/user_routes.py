from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from uuid import UUID

from ...presentation.dependencies import get_user_use_case
from ...application.dtos.user_dto import (
    UserCreateDTO,
    UserUpdateDTO,
    UserChangePasswordDTO,
    UserResponseDTO,
    UserListResponseDTO,
)
from ...application.use_cases.user_use_cases import UserUseCase

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponseDTO)
def get_user_by_id(
    user_id: UUID,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Obtém um usuário pelo ID."""
    try:
        user = use_case.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=UserListResponseDTO)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    active_only: bool = Query(True, description="Show only active users"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Lista usuários com paginação."""
    try:
        return use_case.list_users(
            page=page,
            page_size=page_size,
            active_only=active_only,
            organization_id=organization_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/by-email/{email}", response_model=UserResponseDTO)
def get_user_by_email(
    email: str,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Obtém um usuário pelo email."""
    try:
        user = use_case.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{user_id}", response_model=UserResponseDTO)
def update_user(
    user_id: UUID,
    dto: UserUpdateDTO,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Atualiza as informações do usuário."""
    try:
        return use_case.update_user(user_id, dto)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{user_id}/change-password")
def change_password(
    user_id: UUID,
    dto: UserChangePasswordDTO,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Altera a senha do usuário."""
    try:
        use_case.change_password(user_id, dto)
        return {"message": "Password changed successfully"}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        if "incorrect" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{user_id}/activate", response_model=UserResponseDTO)
def activate_user(
    user_id: UUID,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Ativa a conta do usuário."""
    try:
        return use_case.activate_user(user_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{user_id}/deactivate", response_model=UserResponseDTO)
def deactivate_user(
    user_id: UUID,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Desativa a conta do usuário."""
    try:
        return use_case.deactivate_user(user_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Exclui a conta do usuário."""
    try:
        success = use_case.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/check-email/{email}")
def check_email_availability(
    email: str,
    excluding_user_id: Optional[UUID] = Query(
        None, description="Exclude this user ID from check"
    ),
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Verifica se o email está disponível para uso."""
    try:
        available = use_case.check_email_availability(email, excluding_user_id)
        return {"email": email, "available": available}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organization/{organization_id}", response_model=UserListResponseDTO)
def get_users_by_organization(
    organization_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    active_only: bool = Query(True, description="Show only active users"),
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Lista usuários de uma organização específica."""
    try:
        return use_case.list_users(
            page=page,
            page_size=page_size,
            active_only=active_only,
            organization_id=organization_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{user_id}/join-organization/{organization_id}", response_model=UserResponseDTO
)
def join_organization(
    user_id: UUID,
    organization_id: UUID,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Adiciona usuário a uma organização."""
    try:
        return use_case.join_organization(user_id, organization_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{user_id}/leave-organization", response_model=UserResponseDTO)
def leave_organization(
    user_id: UUID,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Remove usuário de sua organização."""
    try:
        return use_case.leave_organization(user_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
def create_user(
    dto: UserCreateDTO,
    use_case: UserUseCase = Depends(get_user_use_case),
):
    """Cria um novo usuário."""
    try:
        return use_case.create_user(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
