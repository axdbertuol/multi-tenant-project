from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from domain.entities.user_session import UserSession, SessionStatus
from domain.repositories.user_session_repository import UserSessionRepository
from infrastructure.database.models import UserSessionModel, SessionStatusEnum
from infrastructure.repositories.base_sqlalchemy_repository import SQLAlchemyRepository


class UserSessionRepositoryImpl(SQLAlchemyRepository[UserSession, UserSessionModel], UserSessionRepository):
    def __init__(self, db: Session):
        super().__init__(db, UserSessionModel)

    def _to_domain(self, model: UserSessionModel) -> UserSession:
        return UserSession(
            id=model.id,
            user_id=model.user_id,
            session_token=model.session_token,
            status=SessionStatus(model.status.value),
            login_at=model.login_at,
            logout_at=model.logout_at,
            expires_at=model.expires_at,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, session: UserSession) -> UserSessionModel:
        return UserSessionModel(
            id=session.id,
            user_id=session.user_id,
            session_token=session.session_token,
            status=SessionStatusEnum(session.status.value),
            login_at=session.login_at,
            logout_at=session.logout_at,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def _update_model(self, model: UserSessionModel, session: UserSession) -> UserSessionModel:
        model.status = SessionStatusEnum(session.status.value)
        model.logout_at = session.logout_at
        model.expires_at = session.expires_at
        model.ip_address = session.ip_address
        model.user_agent = session.user_agent
        model.updated_at = session.updated_at
        return model

    async def get_by_session_token(self, session_token: str) -> Optional[UserSession]:
        model = self.db.query(UserSessionModel).filter(
            UserSessionModel.session_token == session_token
        ).first()
        return self._to_domain(model) if model else None

    async def get_active_sessions_by_user_id(self, user_id: UUID) -> List[UserSession]:
        models = self.db.query(UserSessionModel).filter(
            and_(
                UserSessionModel.user_id == user_id,
                UserSessionModel.status == SessionStatusEnum.ACTIVE,
                UserSessionModel.expires_at > datetime.utcnow()
            )
        ).all()
        return [self._to_domain(model) for model in models]

    async def get_all_sessions_by_user_id(self, user_id: UUID) -> List[UserSession]:
        models = self.db.query(UserSessionModel).filter(
            UserSessionModel.user_id == user_id
        ).order_by(UserSessionModel.login_at.desc()).all()
        return [self._to_domain(model) for model in models]

    async def expire_sessions_by_user_id(self, user_id: UUID) -> int:
        count = self.db.query(UserSessionModel).filter(
            and_(
                UserSessionModel.user_id == user_id,
                UserSessionModel.status == SessionStatusEnum.ACTIVE
            )
        ).update({
            UserSessionModel.status: SessionStatusEnum.EXPIRED,
            UserSessionModel.logout_at: datetime.utcnow(),
            UserSessionModel.updated_at: datetime.utcnow()
        })
        self.db.commit()
        return count

    async def cleanup_expired_sessions(self) -> int:
        # Mark expired sessions based on expires_at timestamp
        count = self.db.query(UserSessionModel).filter(
            and_(
                UserSessionModel.status == SessionStatusEnum.ACTIVE,
                UserSessionModel.expires_at <= datetime.utcnow()
            )
        ).update({
            UserSessionModel.status: SessionStatusEnum.EXPIRED,
            UserSessionModel.updated_at: datetime.utcnow()
        })
        self.db.commit()
        return count