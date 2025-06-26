from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from domain.entities.user_session import SessionStatus


class SessionInfoDto(BaseModel):
    id: UUID
    user_id: UUID
    status: SessionStatus
    login_at: datetime
    logout_at: Optional[datetime]
    expires_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_current: bool = False
    session_duration: Optional[int] = None


class UserSessionsResponseDto(BaseModel):
    sessions: List[SessionInfoDto]
    total_sessions: int
    active_sessions: int


class LogoutDto(BaseModel):
    revoke_all_sessions: bool = False


class LogoutResponseDto(BaseModel):
    message: str
    revoked_sessions_count: int


class SessionStatsDto(BaseModel):
    total_sessions: int
    active_sessions: int
    expired_sessions: int
    logged_out_sessions: int
    revoked_sessions: int