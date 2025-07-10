from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, update, select
from sqlalchemy.orm import Session
from ...domain.entities.user_session import UserSession
from ...domain.repositories.user_session_repository import UserSessionRepository
from ..database.models import SessionStatusEnum, UserSessionModel


class SqlAlchemyUserSessionRepository(UserSessionRepository):
    """Implementação SQLAlchemy de UserSessionRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, session_entity: UserSession) -> UserSession:
        """Salva uma entidade de sessão de usuário."""
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
            existing.extra_data = session_entity.extra_data
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
                extra_data=session_entity.extra_data,
                created_at=session_entity.created_at,
                updated_at=session_entity.updated_at,
            )

            self.session.add(session_model)
            self.session.flush()
            return self._to_domain_entity(session_model)

    def get_by_id(self, session_id: UUID) -> Optional[UserSession]:
        """Encontra uma sessão pelo ID."""
        result = self.session.execute(
            select(UserSessionModel).where(UserSessionModel.id == session_id)
        )
        session_model = result.scalar_one_or_none()

        if session_model:
            return self._to_domain_entity(session_model)
        return None

    def get_by_token(self, session_token: str) -> Optional[UserSession]:
        """Encontra uma sessão pelo token."""
        result = self.session.execute(
            select(UserSessionModel).where(
                UserSessionModel.session_token == session_token
            )
        )
        session_model = result.scalar_one_or_none()

        if session_model:
            return self._to_domain_entity(session_model)
        return None

    def get_active_by_user_id(self, user_id: UUID) -> List[UserSession]:
        """Encontra todas as sessões ativas para um usuário."""
        result = self.session.execute(
            select(UserSessionModel).where(
                UserSessionModel.user_id == user_id,
                UserSessionModel.status == SessionStatusEnum.ACTIVE,
                UserSessionModel.expires_at > datetime.now(timezone.utc),
            )
        )
        session_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in session_models]

    def get_expired_sessions(self) -> List[UserSession]:
        """Encontra todas as sessões expiradas."""
        result = self.session.execute(
            select(UserSessionModel).where(
                UserSessionModel.expires_at <= datetime.now(timezone.utc),
                UserSessionModel.status == SessionStatusEnum.ACTIVE,
            )
        )
        session_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in session_models]

    def get_user_sessions(
        self, user_id: UUID, status: Optional[str] = None, limit: int = 10
    ) -> List[UserSession]:
        """Encontra sessões para um usuário com filtro de status opcional."""
        query = select(UserSessionModel).where(UserSessionModel.user_id == user_id)

        if status:
            query = query.where(UserSessionModel.status == SessionStatusEnum(status))

        query = query.order_by(UserSessionModel.last_activity_at.desc()).limit(limit)

        result = self.session.execute(query)
        session_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in session_models]

    def delete(self, session_id: UUID) -> bool:
        """Exclui uma sessão (exclusão física)."""
        result = self.session.execute(
            delete(UserSessionModel).where(UserSessionModel.id == session_id)
        )
        return result.rowcount > 0

    def delete_user_sessions(self, user_id: UUID) -> int:
        """Exclui todas as sessões de um usuário."""
        result = self.session.execute(
            delete(UserSessionModel).where(UserSessionModel.user_id == user_id)
        )
        return result.rowcount

    def revoke_session(self, session_id: UUID) -> bool:
        """Revoga uma sessão alterando seu status."""
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

    def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """Revoga todas as sessões de um usuário."""
        query = update(UserSessionModel).where(
            UserSessionModel.user_id == user_id,
            UserSessionModel.status == SessionStatusEnum.ACTIVE,
        ).values(
            status=SessionStatusEnum.REVOKED,
            logout_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = self.session.execute(query)
        return result.rowcount

    def revoke_user_sessions(
        self, user_id: UUID, exclude_session_id: Optional[UUID] = None
    ) -> int:
        """Revoga todas as sessões de um usuário, opcionalmente excluindo uma sessão."""
        if exclude_session_id is None:
            return self.revoke_all_user_sessions(user_id)
        
        query = update(UserSessionModel).where(
            UserSessionModel.user_id == user_id,
            UserSessionModel.status == SessionStatusEnum.ACTIVE,
            UserSessionModel.id != exclude_session_id
        ).values(
            status=SessionStatusEnum.REVOKED,
            logout_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = self.session.execute(query)
        return result.rowcount

    def update_activity(self, session_id: UUID, activity_time: datetime) -> bool:
        """Atualiza o horário da última atividade da sessão."""
        result = self.session.execute(
            update(UserSessionModel)
            .where(UserSessionModel.id == session_id)
            .values(
                last_activity_at=activity_time, updated_at=datetime.now(timezone.utc)
            )
        )
        return result.rowcount > 0

    def cleanup_expired_sessions(self) -> int:
        """Limpa sessões expiradas atualizando seu status."""
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
        """Converte o modelo SQLAlchemy para a entidade de domínio."""
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
            extra_data=session_model.extra_data,
            created_at=session_model.created_at,
            updated_at=session_model.updated_at,
        )
