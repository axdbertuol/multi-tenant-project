from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from .user_dto import UserResponseDTO
from .session_dto import SessionResponseDTO


class LoginDTO(BaseModel):
    """DTO for user login."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(False, description="Extended session duration")
    user_agent: Optional[str] = Field(
        None, max_length=500, description="User agent string"
    )
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")


class AuthResponseDTO(BaseModel):
    """DTO for authentication response."""

    user: UserResponseDTO
    session: SessionResponseDTO
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LogoutDTO2(BaseModel):
    session_id: UUID
    user_id: UUID


class LogoutDTO(BaseModel):
    """DTO for user logout."""

    revoke_all_sessions: bool = Field(False, description="Revoke all user sessions")


class LogoutResponseDTO(BaseModel):
    success: bool = True
    message: str = "Sessão encerrada com sucesso"


class RefreshTokenDTO(BaseModel):
    """DTO for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequestDTO(BaseModel):
    """DTO for password reset request."""

    email: str = Field(..., description="User email address")


class PasswordResetConfirmDTO(BaseModel):
    """DTO for password reset confirmation."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
