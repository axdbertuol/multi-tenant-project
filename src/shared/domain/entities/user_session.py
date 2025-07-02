from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class SessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    LOGGED_OUT = "logged_out"
    REVOKED = "revoked"


class UserSession(BaseModel):
    id: UUID
    user_id: UUID
    session_token: str
    status: SessionStatus
    login_at: datetime
    logout_at: Optional[datetime] = None
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls,
        user_id: UUID,
        session_token: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "UserSession":
        now = datetime.utcnow()
        return cls(
            id=uuid4(),
            user_id=user_id,
            session_token=session_token,
            status=SessionStatus.ACTIVE,
            login_at=now,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
        )

    def logout(self) -> "UserSession":
        """Mark session as logged out."""
        return self.model_copy(
            update={
                "status": SessionStatus.LOGGED_OUT,
                "logout_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

    def expire(self) -> "UserSession":
        """Mark session as expired."""
        return self.model_copy(
            update={"status": SessionStatus.EXPIRED, "updated_at": datetime.utcnow()}
        )

    def revoke(self) -> "UserSession":
        """Mark session as revoked (admin action)."""
        return self.model_copy(
            update={
                "status": SessionStatus.REVOKED,
                "logout_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

    def is_active(self) -> bool:
        """Check if session is currently active."""
        if self.status != SessionStatus.ACTIVE:
            return False

        return datetime.utcnow() < self.expires_at

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() >= self.expires_at

    def get_session_duration(self) -> Optional[int]:
        """Get session duration in seconds. Returns None if still active."""
        if not self.logout_at:
            return None

        duration = self.logout_at - self.login_at
        return int(duration.total_seconds())

    def extend_session(self, new_expires_at: datetime) -> "UserSession":
        """Extend session expiration time."""
        if self.status != SessionStatus.ACTIVE:
            raise ValueError("Cannot extend inactive session")

        return self.model_copy(
            update={"expires_at": new_expires_at, "updated_at": datetime.utcnow()}
        )
