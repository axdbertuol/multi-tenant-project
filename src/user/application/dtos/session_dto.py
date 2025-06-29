from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SessionCreateDTO(BaseModel):
    """DTO for creating a new user session."""
    user_id: UUID = Field(..., description="User ID")
    duration_hours: int = Field(24, ge=1, le=720, description="Session duration in hours")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent string")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")


class SessionResponseDTO(BaseModel):
    """DTO for session response data."""
    id: UUID
    user_id: UUID
    token: str
    expires_at: datetime
    created_at: datetime
    is_active: bool
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    is_expired: bool
    is_valid: bool
    
    model_config = {"from_attributes": True}


class SessionListResponseDTO(BaseModel):
    """DTO for user sessions list response."""
    sessions: list[SessionResponseDTO]
    total: int
    active_count: int