from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from ...domain.entities.user_session import UserSession
from ...domain.repositories.user_session_repository import UserSessionRepository
from ...infrastructure.models.database_models import (
    UserSessionModel,
    SessionStatusEnum,
)


class SqlAlchemyUserSessionRepository(UserSessionRepository):
    """SQLAlchemy implementation of UserSessionRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, session_entity: UserSession) -> UserSession:
        """Save a user session entity."""
        # Check if session exists
        existing = self.session.get(UserSessionModel, session_entity.id)

        if existing:
            # Update existing session
            existing.user_id = session_entity.user_id
            existing.session_token = session_entity.session_token
            existing.status = SessionStatusEnum(session_entity.status)
            existing.expires_at = session_entity.expires_at
            existing.ip_address = session_entity.ip_address
            existing.user_agent = session_entity.user_agent
            existing.last_activity_at = session_entity.last_activity_at
            existing.logout_at = session_entity.logout_at
            existing.metadata = session_entity.metadata
            existing.updated_at = datetime.now(timezone.utc)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new session
            session_model = UserSessionModel(
                id=session_entity.id,
                user_id=session_entity.user_id,
                session_token=session_entity.session_token,
                status=SessionStatusEnum(session_entity.status),
                expires_at=session_entity.expires_at,
                ip_address=session_entity.ip_address,
                user_agent=session_entity.user_agent,
                last_activity_at=session_entity.last_activity_at,
                logout_at=session_entity.logout_at,
                metadata=session_entity.metadata,
                created_at=session_entity.created_at,
                updated_at=session_entity.updated_at,
            )

            self.session.add(session_model)
            self.session.flush()
            return self._to_domain_entity(session_model)

    def find_by_id(self, session_id: UUID) -> Optional[UserSession]:
        """Find a session by ID."""
        result = self.session.execute(
            select(UserSessionModel).where(UserSessionModel.id == session_id)
        )
        session_model = result.scalar_one_or_none()

        if session_model:
            return self._to_domain_entity(session_model)
        return None

    def find_by_token(self, session_token: str) -> Optional[UserSession]:
        """Find a session by token."""
        result = self.session.execute(
            select(UserSessionModel).where(
                UserSessionModel.session_token == session_token
            )
        )
        session_model = result.scalar_one_or_none()

        if session_model:
            return self._to_domain_entity(session_model)
        return None

    def find_active_by_user(self, user_id: UUID) -> List[UserSession]:
        """Find all active sessions for a user."""
        result = self.session.execute(
            select(UserSessionModel).where(
                UserSessionModel.user_id == user_id,
                UserSessionModel.status == SessionStatusEnum.ACTIVE,
                UserSessionModel.expires_at > datetime.now(timezone.utc),
            )
        )
        session_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in session_models]

    def find_expired_sessions(self) -> List[UserSession]:
        """Find all expired sessions."""
        result = self.session.execute(
            select(UserSessionModel).where(
                UserSessionModel.expires_at <= datetime.now(timezone.utc),
                UserSessionModel.status == SessionStatusEnum.ACTIVE,
            )
        )
        session_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in session_models]

    def find_user_sessions(
        self, user_id: UUID, status: Optional[str] = None, limit: int = 10
    ) -> List[UserSession]:
        """Find sessions for a user with optional status filter."""
        query = select(UserSessionModel).where(UserSessionModel.user_id == user_id)

        if status:
            query = query.where(UserSessionModel.status == SessionStatusEnum(status))

        query = query.order_by(UserSessionModel.last_activity_at.desc()).limit(limit)

        result = self.session.execute(query)
        session_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in session_models]

    def delete(self, session_id: UUID) -> bool:
        """Delete a session (hard delete)."""
        result = self.session.execute(
            delete(UserSessionModel).where(UserSessionModel.id == session_id)
        )
        return result.rowcount > 0

    def delete_user_sessions(self, user_id: UUID) -> int:
        """Delete all sessions for a user."""
        result = self.session.execute(
            delete(UserSessionModel).where(UserSessionModel.user_id == user_id)
        )
        return result.rowcount

    def revoke_session(self, session_id: UUID) -> bool:
        """Revoke a session by changing its status."""
        result = self.session.execute(
            update(UserSessionModel)
            .where(UserSessionModel.id == session_id)
            .values(
                status=SessionStatusEnum.REVOKED,
                logout_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        return result.rowcount > 0

    def revoke_user_sessions(
        self, user_id: UUID, exclude_session_id: Optional[UUID] = None
    ) -> int:
        """Revoke all sessions for a user, optionally excluding one session."""
        query = update(UserSessionModel).where(
            UserSessionModel.user_id == user_id,
            UserSessionModel.status == SessionStatusEnum.ACTIVE,
        )

        if exclude_session_id:
            query = query.where(UserSessionModel.id != exclude_session_id)

        query = query.values(
            status=SessionStatusEnum.REVOKED,
            logout_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = self.session.execute(query)
        return result.rowcount

    def update_activity(self, session_id: UUID, activity_time: datetime) -> bool:
        """Update session's last activity time."""
        result = self.session.execute(
            update(UserSessionModel)
            .where(UserSessionModel.id == session_id)
            .values(
                last_activity_at=activity_time, updated_at=datetime.now(timezone.utc)
            )
        )
        return result.rowcount > 0

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions by updating their status."""
        result = self.session.execute(
            update(UserSessionModel)
            .where(
                UserSessionModel.expires_at <= datetime.now(timezone.utc),
                UserSessionModel.status == SessionStatusEnum.ACTIVE,
            )
            .values(
                status=SessionStatusEnum.EXPIRED, updated_at=datetime.now(timezone.utc)
            )
        )
        return result.rowcount

    def _to_domain_entity(self, session_model: UserSessionModel) -> UserSession:
        """Convert SQLAlchemy model to domain entity."""
        return UserSession(
            id=session_model.id,
            user_id=session_model.user_id,
            session_token=session_model.session_token,
            status=session_model.status.value,
            expires_at=session_model.expires_at,
            ip_address=session_model.ip_address,
            user_agent=session_model.user_agent,
            last_activity_at=session_model.last_activity_at,
            logout_at=session_model.logout_at,
            metadata=session_model.metadata,
            created_at=session_model.created_at,
            updated_at=session_model.updated_at,
        )
