from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from .user_dto import UserResponseDTO
from .session_dto import SessionResponseDTO


class LoginDTO(BaseModel):
    """DTO para login de usuário."""

    email: str = Field(..., description="Endereço de email do usuário")
    password: str = Field(..., description="Senha do usuário")
    remember_me: bool = Field(False, description="Duração estendida da sessão")
    user_agent: Optional[str] = Field(
        None, max_length=500, description="String do user agent"
    )
    ip_address: Optional[str] = Field(None, max_length=45, description="Endereço IP")


class AuthResponseDTO(BaseModel):
    """DTO para resposta de autenticação."""

    user: UserResponseDTO
    session: SessionResponseDTO
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class LogoutDTO2(BaseModel):
    session_id: UUID
    user_id: UUID


class LogoutDTO(BaseModel):
    """DTO para logout de usuário."""

    revoke_all_sessions: bool = Field(
        False, description="Revogar todas as sessões do usuário"
    )


class LogoutResponseDTO(BaseModel):
    success: bool = True
    message: str = "Sessão encerrada com sucesso"


class RefreshTokenDTO(BaseModel):
    """DTO para atualização de token."""

    refresh_token: str = Field(..., description="Token de atualização")


class PasswordResetRequestDTO(BaseModel):
    """DTO para solicitação de redefinição de senha."""

    email: str = Field(..., description="Endereço de email do usuário")


class PasswordResetConfirmDTO(BaseModel):
    """DTO para confirmação de redefinição de senha."""

    token: str = Field(..., description="Token de redefinição de senha")
    new_password: str = Field(..., min_length=8, description="Nova senha")
