from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import delete, select, func, and_, or_, update
from sqlalchemy.orm import Session
from ...domain.entities.user_document_access import UserDocumentAccess
from ...domain.repositories.user_document_access_repository import UserDocumentAccessRepository
from ..database.models import UserDocumentAccessModel


class SqlAlchemyUserDocumentAccessRepository(UserDocumentAccessRepository):
    """SQLAlchemy implementation of UserDocumentAccessRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, access: UserDocumentAccess) -> UserDocumentAccess:
        """Save a user document access entity."""
        # Check if access exists
        existing = self.session.get(UserDocumentAccessModel, access.id)

        if existing:
            # Update existing access
            existing.user_id = access.user_id
            existing.area_id = access.area_id
            existing.organization_id = access.organization_id
            existing.access_level = access.access_level.value
            existing.granted_by = access.granted_by
            existing.granted_at = access.granted_at
            existing.expires_at = access.expires_at
            existing.is_active = access.is_active
            existing.revoked_at = access.revoked_at
            existing.revoked_by = access.revoked_by
            existing.notes = access.notes
            existing.extra_data = access.extra_data
            existing.updated_at = datetime.now(timezone.utc)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new access
            access_model = UserDocumentAccessModel(
                id=access.id,
                user_id=access.user_id,
                area_id=access.area_id,
                organization_id=access.organization_id,
                access_level=access.access_level.value,
                granted_by=access.granted_by,
                granted_at=access.granted_at,
                expires_at=access.expires_at,
                is_active=access.is_active,
                revoked_at=access.revoked_at,
                revoked_by=access.revoked_by,
                notes=access.notes,
                extra_data=access.extra_data,
                created_at=access.created_at,
                updated_at=access.updated_at,
            )

            self.session.add(access_model)
            self.session.flush()
            return self._to_domain_entity(access_model)

    def get_by_id(self, access_id: UUID) -> Optional[UserDocumentAccess]:
        """Get access by ID."""
        result = self.session.execute(
            select(UserDocumentAccessModel).where(UserDocumentAccessModel.id == access_id)
        )
        access_model = result.scalar_one_or_none()

        if access_model:
            return self._to_domain_entity(access_model)
        return None

    def get_by_user_and_area(self, user_id: UUID, area_id: UUID) -> Optional[UserDocumentAccess]:
        """Get access by user and area."""
        result = self.session.execute(
            select(UserDocumentAccessModel).where(
                and_(
                    UserDocumentAccessModel.user_id == user_id,
                    UserDocumentAccessModel.area_id == area_id,
                )
            )
        )
        access_model = result.scalar_one_or_none()

        if access_model:
            return self._to_domain_entity(access_model)
        return None

    def get_by_user(self, user_id: UUID) -> List[UserDocumentAccess]:
        """Get all access records for a user."""
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(UserDocumentAccessModel.user_id == user_id)
            .order_by(UserDocumentAccessModel.granted_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_active_by_user(self, user_id: UUID) -> List[UserDocumentAccess]:
        """Get active access records for a user."""
        current_time = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.user_id == user_id,
                    UserDocumentAccessModel.is_active == True,
                    or_(
                        UserDocumentAccessModel.expires_at.is_(None),
                        UserDocumentAccessModel.expires_at > current_time
                    )
                )
            )
            .order_by(UserDocumentAccessModel.granted_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_by_area(self, area_id: UUID) -> List[UserDocumentAccess]:
        """Get all access records for an area."""
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(UserDocumentAccessModel.area_id == area_id)
            .order_by(UserDocumentAccessModel.granted_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_active_by_area(self, area_id: UUID) -> List[UserDocumentAccess]:
        """Get active access records for an area."""
        current_time = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.area_id == area_id,
                    UserDocumentAccessModel.is_active == True,
                    or_(
                        UserDocumentAccessModel.expires_at.is_(None),
                        UserDocumentAccessModel.expires_at > current_time
                    )
                )
            )
            .order_by(UserDocumentAccessModel.granted_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_by_organization(self, organization_id: UUID) -> List[UserDocumentAccess]:
        """Get all access records for an organization."""
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(UserDocumentAccessModel.organization_id == organization_id)
            .order_by(UserDocumentAccessModel.granted_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_active_by_organization(self, organization_id: UUID) -> List[UserDocumentAccess]:
        """Get active access records for an organization."""
        current_time = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.organization_id == organization_id,
                    UserDocumentAccessModel.is_active == True,
                    or_(
                        UserDocumentAccessModel.expires_at.is_(None),
                        UserDocumentAccessModel.expires_at > current_time
                    )
                )
            )
            .order_by(UserDocumentAccessModel.granted_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_by_access_level(self, access_level: str, organization_id: UUID) -> List[UserDocumentAccess]:
        """Get access records by access level."""
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.access_level == access_level,
                    UserDocumentAccessModel.organization_id == organization_id,
                    UserDocumentAccessModel.is_active == True,
                )
            )
            .order_by(UserDocumentAccessModel.granted_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_expiring_soon(self, organization_id: UUID, days_ahead: int = 7) -> List[UserDocumentAccess]:
        """Get access records expiring within N days."""
        current_time = datetime.now(timezone.utc)
        future_time = current_time + timedelta(days=days_ahead)
        
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.organization_id == organization_id,
                    UserDocumentAccessModel.is_active == True,
                    UserDocumentAccessModel.expires_at.isnot(None),
                    UserDocumentAccessModel.expires_at.between(current_time, future_time)
                )
            )
            .order_by(UserDocumentAccessModel.expires_at)
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_expired(self, organization_id: UUID) -> List[UserDocumentAccess]:
        """Get expired access records."""
        current_time = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.organization_id == organization_id,
                    UserDocumentAccessModel.is_active == True,
                    UserDocumentAccessModel.expires_at.isnot(None),
                    UserDocumentAccessModel.expires_at < current_time
                )
            )
            .order_by(UserDocumentAccessModel.expires_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_by_granted_by(self, granted_by: UUID, organization_id: UUID) -> List[UserDocumentAccess]:
        """Get access records granted by a specific user."""
        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.granted_by == granted_by,
                    UserDocumentAccessModel.organization_id == organization_id,
                )
            )
            .order_by(UserDocumentAccessModel.granted_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_recently_granted(self, organization_id: UUID, days: int = 30) -> List[UserDocumentAccess]:
        """Get access records granted within the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.organization_id == organization_id,
                    UserDocumentAccessModel.granted_at >= cutoff_date,
                )
            )
            .order_by(UserDocumentAccessModel.granted_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def get_recently_revoked(self, organization_id: UUID, days: int = 30) -> List[UserDocumentAccess]:
        """Get access records revoked within the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = self.session.execute(
            select(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.organization_id == organization_id,
                    UserDocumentAccessModel.revoked_at.isnot(None),
                    UserDocumentAccessModel.revoked_at >= cutoff_date,
                )
            )
            .order_by(UserDocumentAccessModel.revoked_at.desc())
        )
        access_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in access_models]

    def revoke_access(self, access_id: UUID, revoked_by: UUID) -> bool:
        """Revoke access by setting it as inactive."""
        result = self.session.execute(
            update(UserDocumentAccessModel)
            .where(UserDocumentAccessModel.id == access_id)
            .values(
                is_active=False,
                revoked_at=datetime.now(timezone.utc),
                revoked_by=revoked_by,
                updated_at=datetime.now(timezone.utc),
            )
        )
        return result.rowcount > 0

    def revoke_user_access_to_area(self, user_id: UUID, area_id: UUID, revoked_by: UUID) -> bool:
        """Revoke user's access to a specific area."""
        result = self.session.execute(
            update(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.user_id == user_id,
                    UserDocumentAccessModel.area_id == area_id,
                    UserDocumentAccessModel.is_active == True,
                )
            )
            .values(
                is_active=False,
                revoked_at=datetime.now(timezone.utc),
                revoked_by=revoked_by,
                updated_at=datetime.now(timezone.utc),
            )
        )
        return result.rowcount > 0

    def revoke_all_user_access(self, user_id: UUID, revoked_by: UUID) -> int:
        """Revoke all access for a user."""
        result = self.session.execute(
            update(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.user_id == user_id,
                    UserDocumentAccessModel.is_active == True,
                )
            )
            .values(
                is_active=False,
                revoked_at=datetime.now(timezone.utc),
                revoked_by=revoked_by,
                updated_at=datetime.now(timezone.utc),
            )
        )
        return result.rowcount

    def cleanup_expired_access(self) -> int:
        """Mark expired access as inactive."""
        current_time = datetime.now(timezone.utc)
        
        result = self.session.execute(
            update(UserDocumentAccessModel)
            .where(
                and_(
                    UserDocumentAccessModel.is_active == True,
                    UserDocumentAccessModel.expires_at.isnot(None),
                    UserDocumentAccessModel.expires_at < current_time
                )
            )
            .values(
                is_active=False,
                updated_at=current_time,
            )
        )
        return result.rowcount

    def exists_active_access(self, user_id: UUID, area_id: UUID) -> bool:
        """Check if user has active access to area."""
        current_time = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(UserDocumentAccessModel.id).where(
                and_(
                    UserDocumentAccessModel.user_id == user_id,
                    UserDocumentAccessModel.area_id == area_id,
                    UserDocumentAccessModel.is_active == True,
                    or_(
                        UserDocumentAccessModel.expires_at.is_(None),
                        UserDocumentAccessModel.expires_at > current_time
                    )
                )
            )
        )
        return result.scalar_one_or_none() is not None

    def count_by_user(self, user_id: UUID) -> int:
        """Count access records for a user."""
        result = self.session.execute(
            select(func.count(UserDocumentAccessModel.id)).where(
                UserDocumentAccessModel.user_id == user_id
            )
        )
        return result.scalar()

    def count_active_by_user(self, user_id: UUID) -> int:
        """Count active access records for a user."""
        current_time = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(func.count(UserDocumentAccessModel.id)).where(
                and_(
                    UserDocumentAccessModel.user_id == user_id,
                    UserDocumentAccessModel.is_active == True,
                    or_(
                        UserDocumentAccessModel.expires_at.is_(None),
                        UserDocumentAccessModel.expires_at > current_time
                    )
                )
            )
        )
        return result.scalar()

    def count_by_area(self, area_id: UUID) -> int:
        """Count access records for an area."""
        result = self.session.execute(
            select(func.count(UserDocumentAccessModel.id)).where(
                UserDocumentAccessModel.area_id == area_id
            )
        )
        return result.scalar()

    def count_by_organization(self, organization_id: UUID) -> int:
        """Count access records for an organization."""
        result = self.session.execute(
            select(func.count(UserDocumentAccessModel.id)).where(
                UserDocumentAccessModel.organization_id == organization_id
            )
        )
        return result.scalar()

    def delete(self, access_id: UUID) -> bool:
        """Delete an access record."""
        result = self.session.execute(
            delete(UserDocumentAccessModel).where(UserDocumentAccessModel.id == access_id)
        )
        return result.rowcount > 0

    def _to_domain_entity(self, access_model: UserDocumentAccessModel) -> UserDocumentAccess:
        """Convert SQLAlchemy model to domain entity."""
        from ...domain.value_objects.access_level import AccessLevel
        
        return UserDocumentAccess(
            id=access_model.id,
            user_id=access_model.user_id,
            area_id=access_model.area_id,
            organization_id=access_model.organization_id,
            access_level=AccessLevel(access_model.access_level),
            granted_by=access_model.granted_by,
            granted_at=access_model.granted_at,
            expires_at=access_model.expires_at,
            is_active=access_model.is_active,
            revoked_at=access_model.revoked_at,
            revoked_by=access_model.revoked_by,
            notes=access_model.notes,
            extra_data=access_model.extra_data,
            created_at=access_model.created_at,
            updated_at=access_model.updated_at,
        )