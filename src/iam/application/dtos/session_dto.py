from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SessionCreateDTO(BaseModel):
    """DTO para criação de uma nova sessão de usuário."""

    user_id: UUID = Field(..., description="ID do Usuário")
    duration_hours: int = Field(
        24, ge=1, le=720, description="Duração da sessão em horas"
    )
    user_agent: Optional[str] = Field(
        None, max_length=500, description="String do user agent"
    )
    ip_address: Optional[str] = Field(None, max_length=45, description="Endereço IP")


class SessionResponseDTO(BaseModel):
    """DTO para dados de resposta da sessão."""

    id: UUID
    user_id: UUID
    session_token: str
    expires_at: datetime
    created_at: datetime
    # is_active: bool
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    is_expired: bool
    is_valid: bool

    model_config = {"from_attributes": True}


class SessionListResponseDTO(BaseModel):
    """DTO para lista paginada de sessões de usuário."""

    sessions: list[SessionResponseDTO]
    total: int
    active_count: int
