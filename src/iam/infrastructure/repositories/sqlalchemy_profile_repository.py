from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import delete, select, func, and_
from sqlalchemy.orm import Session
from ...domain.entities.profile import Profile
from ...domain.repositories.profile_repository import ProfileRepository
from ..database.models import ProfileModel


class SqlAlchemyProfileRepository(ProfileRepository):
    """SQLAlchemy implementation of ProfileRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, profile: Profile) -> Profile:
        """Save a profile entity."""
        # Check if profile exists
        existing = self.session.get(ProfileModel, profile.id)

        if existing:
            # Update existing profile
            existing.name = profile.name
            existing.description = profile.description
            existing.organization_id = profile.organization_id
            existing.created_by = profile.created_by
            existing.is_active = profile.is_active
            existing.is_system_profile = profile.is_system_profile
            existing.profile_metadata = profile.profile_metadata
            existing.updated_at = datetime.now(timezone.utc)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new profile
            profile_model = ProfileModel(
                id=profile.id,
                name=profile.name,
                description=profile.description,
                organization_id=profile.organization_id,
                created_by=profile.created_by,
                is_active=profile.is_active,
                is_system_profile=profile.is_system_profile,
                profile_metadata=profile.profile_metadata,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            )

            self.session.add(profile_model)
            self.session.flush()
            return self._to_domain_entity(profile_model)

    def get_by_id(self, profile_id: UUID) -> Optional[Profile]:
        """Get profile by ID."""
        result = self.session.execute(
            select(ProfileModel).where(ProfileModel.id == profile_id)
        )
        profile_model = result.scalar_one_or_none()

        if profile_model:
            return self._to_domain_entity(profile_model)
        return None

    def get_by_name(self, name: str, organization_id: UUID) -> Optional[Profile]:
        """Get profile by name within organization."""
        result = self.session.execute(
            select(ProfileModel).where(
                and_(
                    ProfileModel.name == name,
                    ProfileModel.organization_id == organization_id,
                )
            )
        )
        profile_model = result.scalar_one_or_none()

        if profile_model:
            return self._to_domain_entity(profile_model)
        return None

    def get_by_organization(self, organization_id: UUID) -> List[Profile]:
        """Get all profiles for an organization."""
        result = self.session.execute(
            select(ProfileModel)
            .where(ProfileModel.organization_id == organization_id)
            .order_by(ProfileModel.name)
        )
        profile_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in profile_models]

    def get_active_by_organization(self, organization_id: UUID) -> List[Profile]:
        """Get active profiles for an organization."""
        result = self.session.execute(
            select(ProfileModel)
            .where(
                and_(
                    ProfileModel.organization_id == organization_id,
                    ProfileModel.is_active == True,
                )
            )
            .order_by(ProfileModel.name)
        )
        profile_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in profile_models]

    def get_profiles_by_status(
        self, is_active: bool, organization_id: UUID
    ) -> List[Profile]:
        """Get profiles by active status within organization."""
        result = self.session.execute(
            select(ProfileModel)
            .where(
                and_(
                    ProfileModel.is_active == is_active,
                    ProfileModel.organization_id == organization_id,
                )
            )
            .order_by(ProfileModel.name)
        )
        profile_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in profile_models]

    def get_profiles_created_by(
        self, created_by: UUID, organization_id: UUID
    ) -> List[Profile]:
        """Get profiles created by a specific user."""
        result = self.session.execute(
            select(ProfileModel)
            .where(
                and_(
                    ProfileModel.created_by == created_by,
                    ProfileModel.organization_id == organization_id,
                )
            )
            .order_by(ProfileModel.created_at.desc())
        )
        profile_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in profile_models]

    def get_system_profiles(self) -> List[Profile]:
        """Get all system profiles."""
        result = self.session.execute(
            select(ProfileModel)
            .where(ProfileModel.is_system_profile == True)
            .order_by(ProfileModel.name)
        )
        profile_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in profile_models]

    def get_recently_created(
        self, organization_id: UUID, days: int = 30
    ) -> List[Profile]:
        """Get profiles created within the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = self.session.execute(
            select(ProfileModel)
            .where(
                and_(
                    ProfileModel.organization_id == organization_id,
                    ProfileModel.created_at >= cutoff_date,
                )
            )
            .order_by(ProfileModel.created_at.desc())
        )
        profile_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in profile_models]

    def exists_by_name(self, name: str, organization_id: UUID) -> bool:
        """Check if profile with name exists in organization."""
        result = self.session.execute(
            select(ProfileModel.id).where(
                and_(
                    ProfileModel.name == name,
                    ProfileModel.organization_id == organization_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    def count_by_organization(self, organization_id: UUID) -> int:
        """Count profiles in organization."""
        result = self.session.execute(
            select(func.count(ProfileModel.id)).where(
                ProfileModel.organization_id == organization_id
            )
        )
        return result.scalar()

    def count_active_by_organization(self, organization_id: UUID) -> int:
        """Count active profiles in organization."""
        result = self.session.execute(
            select(func.count(ProfileModel.id)).where(
                and_(
                    ProfileModel.organization_id == organization_id,
                    ProfileModel.is_active == True,
                )
            )
        )
        return result.scalar()

    def find_by_name_pattern(
        self, pattern: str, organization_id: UUID
    ) -> List[Profile]:
        """Find profiles by name pattern."""
        result = self.session.execute(
            select(ProfileModel)
            .where(
                and_(
                    ProfileModel.name.ilike(f"%{pattern}%"),
                    ProfileModel.organization_id == organization_id,
                )
            )
            .order_by(ProfileModel.name)
        )
        profile_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in profile_models]

    def delete(self, profile_id: UUID) -> bool:
        """Delete a profile."""
        result = self.session.execute(
            delete(ProfileModel).where(ProfileModel.id == profile_id)
        )
        return result.rowcount > 0

    def _to_domain_entity(self, profile_model: ProfileModel) -> Profile:
        """Convert SQLAlchemy model to domain entity."""
        return Profile(
            id=profile_model.id,
            name=profile_model.name,
            description=profile_model.description,
            organization_id=profile_model.organization_id,
            created_by=profile_model.created_by,
            is_active=profile_model.is_active,
            is_system_profile=profile_model.is_system_profile,
            profile_metadata=profile_model.profile_metadata,
            created_at=profile_model.created_at,
            updated_at=profile_model.updated_at,
        )
