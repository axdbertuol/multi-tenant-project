from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class UserCreateDTO(BaseModel):
    """DTO para criação de um novo usuário."""
    email: str = Field(..., description="Endereço de email do usuário")
    name: str = Field(..., min_length=2, max_length=100, description="Nome completo do usuário")
    password: str = Field(..., min_length=8, description="Senha do usuário")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class UserUpdateDTO(BaseModel):
    """DTO para atualização de um usuário existente."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Nome completo do usuário")
    is_active: Optional[bool] = Field(None, description="Status de atividade do usuário")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else None


class UserChangePasswordDTO(BaseModel):
    """DTO para alteração da senha do usuário."""
    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(..., min_length=8, description="Nova senha")


class UserResponseDTO(BaseModel):
    """DTO para dados de resposta do usuário."""
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserListResponseDTO(BaseModel):
    """DTO para lista paginada de usuários."""
    users: list[UserResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int
