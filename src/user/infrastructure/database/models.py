from shared.infrastructure.database.models.base import BaseModel as SQLBaseModel
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum


class SessionStatusEnum(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    LOGGED_OUT = "logged_out"
    REVOKED = "revoked"


class UserModel(SQLBaseModel):
    """SQLAlchemy model for User entity."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)


class UserSessionModel(SQLBaseModel):
    """SQLAlchemy model for UserSession entity."""

    __tablename__ = "user_sessions"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    session_token = Column(String(500), nullable=False, unique=True, index=True)
    status = Column(
        Enum(SessionStatusEnum),
        nullable=False,
        default=SessionStatusEnum.ACTIVE,
        index=True,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    last_activity_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    logout_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string for additional session data
