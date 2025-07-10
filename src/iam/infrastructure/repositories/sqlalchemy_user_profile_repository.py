from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import delete, select, func, and_, or_
from sqlalchemy.orm import Session
from ...domain.entities.user_profile import UserProfile
from ...domain.repositories.user_profile_repository import UserProfileRepository
from ..database.models import UserProfileModel


class SqlAlchemyUserProfileRepository(UserProfileRepository):
    """SQLAlchemy implementation of UserProfileRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, user_profile: UserProfile) -> UserProfile:
        """Save a user profile assignment."""
        # Check if assignment exists
        existing = self.session.get(UserProfileModel, user_profile.id)

        if existing:
            # Update existing assignment
            existing.user_id = user_profile.user_id
            existing.profile_id = user_profile.profile_id
            existing.organization_id = user_profile.organization_id
            existing.assigned_by = user_profile.assigned_by
            existing.assigned_at = user_profile.assigned_at
            existing.expires_at = user_profile.expires_at
            existing.is_active = user_profile.is_active
            existing.revoked_at = user_profile.revoked_at
            existing.revoked_by = user_profile.revoked_by
            existing.notes = user_profile.notes
            existing.extra_data = user_profile.extra_data
            existing.updated_at = datetime.now(timezone.utc)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new assignment
            user_profile_model = UserProfileModel(
                id=user_profile.id,
                user_id=user_profile.user_id,
                profile_id=user_profile.profile_id,
                organization_id=user_profile.organization_id,
                assigned_by=user_profile.assigned_by,
                assigned_at=user_profile.assigned_at,
                expires_at=user_profile.expires_at,
                is_active=user_profile.is_active,
                revoked_at=user_profile.revoked_at,
                revoked_by=user_profile.revoked_by,
                notes=user_profile.notes,
                extra_data=user_profile.extra_data,
                created_at=user_profile.created_at,
                updated_at=user_profile.updated_at,
            )

            self.session.add(user_profile_model)
            self.session.flush()
            return self._to_domain_entity(user_profile_model)

    def get_by_id(self, assignment_id: UUID) -> Optional[UserProfile]:
        """Get assignment by ID."""
        result = self.session.execute(
            select(UserProfileModel).where(UserProfileModel.id == assignment_id)
        )
        model = result.scalar_one_or_none()

        if model:
            return self._to_domain_entity(model)
        return None

    def get_by_user(self, user_id: UUID) -> List[UserProfile]:
        """Get all assignments for a user."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(UserProfileModel.user_id == user_id)
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_by_profile(self, profile_id: UUID) -> List[UserProfile]:
        """Get all assignments for a profile."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(UserProfileModel.profile_id == profile_id)
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_by_organization(self, organization_id: UUID) -> List[UserProfile]:
        """Get all assignments for an organization."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(UserProfileModel.organization_id == organization_id)
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_by_user_and_profile(self, user_id: UUID, profile_id: UUID) -> Optional[UserProfile]:
        """Get assignment by user and profile."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.user_id == user_id,
                    UserProfileModel.profile_id == profile_id
                )
            )
            .order_by(UserProfileModel.assigned_at.desc())
        )
        model = result.scalar_one_or_none()

        if model:
            return self._to_domain_entity(model)
        return None

    def get_by_user_and_organization(self, user_id: UUID, organization_id: UUID) -> List[UserProfile]:
        """Get assignments by user and organization."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.user_id == user_id,
                    UserProfileModel.organization_id == organization_id
                )
            )
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_active_by_user(self, user_id: UUID) -> List[UserProfile]:
        """Get active assignments for a user."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.user_id == user_id,
                    UserProfileModel.is_active == True
                )
            )
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_active_by_profile(self, profile_id: UUID) -> List[UserProfile]:
        """Get active assignments for a profile."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.profile_id == profile_id,
                    UserProfileModel.is_active == True
                )
            )
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_active_by_organization(self, organization_id: UUID) -> List[UserProfile]:
        """Get active assignments for an organization."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.organization_id == organization_id,
                    UserProfileModel.is_active == True
                )
            )
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_active_by_user_and_organization(self, user_id: UUID, organization_id: UUID) -> List[UserProfile]:
        """Get active assignments by user and organization."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.user_id == user_id,
                    UserProfileModel.organization_id == organization_id,
                    UserProfileModel.is_active == True
                )
            )
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_by_assigned_by(self, assigned_by: UUID, organization_id: UUID) -> List[UserProfile]:
        """Get assignments by who assigned them."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.assigned_by == assigned_by,
                    UserProfileModel.organization_id == organization_id
                )
            )
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_expiring_assignments(self, organization_id: UUID, days: int = 7) -> List[UserProfile]:
        """Get assignments expiring within N days."""
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days)
        
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.organization_id == organization_id,
                    UserProfileModel.is_active == True,
                    UserProfileModel.expires_at.is_not(None),
                    UserProfileModel.expires_at <= cutoff_date
                )
            )
            .order_by(UserProfileModel.expires_at)
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_expired_assignments(self, organization_id: UUID) -> List[UserProfile]:
        """Get expired assignments."""
        now = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.organization_id == organization_id,
                    UserProfileModel.expires_at.is_not(None),
                    UserProfileModel.expires_at < now
                )
            )
            .order_by(UserProfileModel.expires_at)
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_assignment_history(self, user_id: UUID, profile_id: UUID) -> List[UserProfile]:
        """Get assignment history for user and profile."""
        result = self.session.execute(
            select(UserProfileModel)
            .where(
                and_(
                    UserProfileModel.user_id == user_id,
                    UserProfileModel.profile_id == profile_id
                )
            )
            .order_by(UserProfileModel.assigned_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def count_by_profile(self, profile_id: UUID) -> int:
        """Count assignments for a profile."""
        result = self.session.execute(
            select(func.count(UserProfileModel.id))
            .where(UserProfileModel.profile_id == profile_id)
        )
        return result.scalar()

    def count_active_by_profile(self, profile_id: UUID) -> int:
        """Count active assignments for a profile."""
        result = self.session.execute(
            select(func.count(UserProfileModel.id))
            .where(
                and_(
                    UserProfileModel.profile_id == profile_id,
                    UserProfileModel.is_active == True
                )
            )
        )
        return result.scalar()

    def count_by_user(self, user_id: UUID) -> int:
        """Count assignments for a user."""
        result = self.session.execute(
            select(func.count(UserProfileModel.id))
            .where(UserProfileModel.user_id == user_id)
        )
        return result.scalar()

    def count_active_by_user(self, user_id: UUID) -> int:
        """Count active assignments for a user."""
        result = self.session.execute(
            select(func.count(UserProfileModel.id))
            .where(
                and_(
                    UserProfileModel.user_id == user_id,
                    UserProfileModel.is_active == True
                )
            )
        )
        return result.scalar()

    def count_by_organization(self, organization_id: UUID) -> int:
        """Count assignments for an organization."""
        result = self.session.execute(
            select(func.count(UserProfileModel.id))
            .where(UserProfileModel.organization_id == organization_id)
        )
        return result.scalar()

    def delete(self, assignment_id: UUID) -> bool:
        """Delete an assignment."""
        result = self.session.execute(
            delete(UserProfileModel).where(UserProfileModel.id == assignment_id)
        )
        return result.rowcount > 0

    def delete_by_profile(self, profile_id: UUID) -> int:
        """Delete all assignments for a profile."""
        result = self.session.execute(
            delete(UserProfileModel).where(UserProfileModel.profile_id == profile_id)
        )
        return result.rowcount

    def delete_by_user(self, user_id: UUID) -> int:
        """Delete all assignments for a user."""
        result = self.session.execute(
            delete(UserProfileModel).where(UserProfileModel.user_id == user_id)
        )
        return result.rowcount

    def _to_domain_entity(self, model: UserProfileModel) -> UserProfile:
        """Convert SQLAlchemy model to domain entity."""
        return UserProfile(
            id=model.id,
            user_id=model.user_id,
            profile_id=model.profile_id,
            organization_id=model.organization_id,
            assigned_by=model.assigned_by,
            assigned_at=model.assigned_at,
            expires_at=model.expires_at,
            is_active=model.is_active,
            revoked_at=model.revoked_at,
            revoked_by=model.revoked_by,
            notes=model.notes,
            extra_data=model.extra_data,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )