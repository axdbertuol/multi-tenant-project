from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import delete, select, func, and_, or_
from sqlalchemy.orm import Session
from ...domain.entities.profile_folder_permission import ProfileFolderPermission
from ...domain.value_objects.folder_permission_level import FolderPermissionLevel
from ...domain.repositories.profile_folder_permission_repository import ProfileFolderPermissionRepository
from ..database.models import ProfileFolderPermissionModel, FolderPermissionLevelEnum


class SqlAlchemyProfileFolderPermissionRepository(ProfileFolderPermissionRepository):
    """SQLAlchemy implementation of ProfileFolderPermissionRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, permission: ProfileFolderPermission) -> ProfileFolderPermission:
        """Save a profile folder permission."""
        # Check if permission exists
        existing = self.session.get(ProfileFolderPermissionModel, permission.id)

        if existing:
            # Update existing permission
            existing.profile_id = permission.profile_id
            existing.folder_path = permission.folder_path
            existing.permission_level = FolderPermissionLevelEnum(permission.permission_level.value)
            existing.organization_id = permission.organization_id
            existing.created_by = permission.created_by
            existing.is_active = permission.is_active
            existing.notes = permission.notes
            existing.extra_data = permission.extra_data
            existing.updated_at = datetime.now(timezone.utc)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new permission
            permission_model = ProfileFolderPermissionModel(
                id=permission.id,
                profile_id=permission.profile_id,
                folder_path=permission.folder_path,
                permission_level=FolderPermissionLevelEnum(permission.permission_level.value),
                organization_id=permission.organization_id,
                created_by=permission.created_by,
                is_active=permission.is_active,
                notes=permission.notes,
                extra_data=permission.extra_data,
                created_at=permission.created_at,
                updated_at=permission.updated_at,
            )

            self.session.add(permission_model)
            self.session.flush()
            return self._to_domain_entity(permission_model)

    def get_by_id(self, permission_id: UUID) -> Optional[ProfileFolderPermission]:
        """Get permission by ID."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(ProfileFolderPermissionModel.id == permission_id)
        )
        model = result.scalar_one_or_none()

        if model:
            return self._to_domain_entity(model)
        return None

    def get_by_profile(self, profile_id: UUID) -> List[ProfileFolderPermission]:
        """Get all permissions for a profile."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(ProfileFolderPermissionModel.profile_id == profile_id)
            .order_by(ProfileFolderPermissionModel.folder_path)
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_active_by_profile(self, profile_id: UUID) -> List[ProfileFolderPermission]:
        """Get active permissions for a profile."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.profile_id == profile_id,
                    ProfileFolderPermissionModel.is_active == True
                )
            )
            .order_by(ProfileFolderPermissionModel.folder_path)
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_by_organization(self, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get all permissions for an organization."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(ProfileFolderPermissionModel.organization_id == organization_id)
            .order_by(ProfileFolderPermissionModel.folder_path)
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_active_by_organization(self, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get active permissions for an organization."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.organization_id == organization_id,
                    ProfileFolderPermissionModel.is_active == True
                )
            )
            .order_by(ProfileFolderPermissionModel.folder_path)
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_by_folder_path(self, folder_path: str, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get permissions by folder path."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.folder_path == folder_path,
                    ProfileFolderPermissionModel.organization_id == organization_id
                )
            )
            .order_by(ProfileFolderPermissionModel.created_at)
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_by_folder_path_prefix(self, folder_path_prefix: str, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get permissions by folder path prefix."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.folder_path.startswith(folder_path_prefix),
                    ProfileFolderPermissionModel.organization_id == organization_id
                )
            )
            .order_by(ProfileFolderPermissionModel.folder_path)
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_by_permission_level(self, permission_level: FolderPermissionLevel, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get permissions by permission level."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.permission_level == FolderPermissionLevelEnum(permission_level.value),
                    ProfileFolderPermissionModel.organization_id == organization_id
                )
            )
            .order_by(ProfileFolderPermissionModel.folder_path)
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_by_profile_and_folder(self, profile_id: UUID, folder_path: str) -> Optional[ProfileFolderPermission]:
        """Get permission by profile and folder."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.profile_id == profile_id,
                    ProfileFolderPermissionModel.folder_path == folder_path
                )
            )
        )
        model = result.scalar_one_or_none()

        if model:
            return self._to_domain_entity(model)
        return None

    def get_by_created_by(self, created_by: UUID, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get permissions created by a specific user."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.created_by == created_by,
                    ProfileFolderPermissionModel.organization_id == organization_id
                )
            )
            .order_by(ProfileFolderPermissionModel.created_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_conflicting_permissions(self, profile_id: UUID, folder_path: str) -> List[ProfileFolderPermission]:
        """Get conflicting permissions for a profile and folder path."""
        # This is a simplified implementation - in a real system, you'd check for
        # hierarchical conflicts (parent/child folder permissions)
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.profile_id == profile_id,
                    ProfileFolderPermissionModel.is_active == True,
                    or_(
                        ProfileFolderPermissionModel.folder_path.startswith(folder_path),
                        folder_path.startswith(ProfileFolderPermissionModel.folder_path)
                    )
                )
            )
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def get_recently_created(self, organization_id: UUID, days: int = 30) -> List[ProfileFolderPermission]:
        """Get permissions created within the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = self.session.execute(
            select(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.organization_id == organization_id,
                    ProfileFolderPermissionModel.created_at >= cutoff_date
                )
            )
            .order_by(ProfileFolderPermissionModel.created_at.desc())
        )
        models = result.scalars().all()

        return [self._to_domain_entity(model) for model in models]

    def count_by_profile(self, profile_id: UUID) -> int:
        """Count permissions for a profile."""
        result = self.session.execute(
            select(func.count(ProfileFolderPermissionModel.id))
            .where(ProfileFolderPermissionModel.profile_id == profile_id)
        )
        return result.scalar()

    def count_active_by_profile(self, profile_id: UUID) -> int:
        """Count active permissions for a profile."""
        result = self.session.execute(
            select(func.count(ProfileFolderPermissionModel.id))
            .where(
                and_(
                    ProfileFolderPermissionModel.profile_id == profile_id,
                    ProfileFolderPermissionModel.is_active == True
                )
            )
        )
        return result.scalar()

    def count_by_organization(self, organization_id: UUID) -> int:
        """Count permissions for an organization."""
        result = self.session.execute(
            select(func.count(ProfileFolderPermissionModel.id))
            .where(ProfileFolderPermissionModel.organization_id == organization_id)
        )
        return result.scalar()

    def count_active_by_organization(self, organization_id: UUID) -> int:
        """Count active permissions for an organization."""
        result = self.session.execute(
            select(func.count(ProfileFolderPermissionModel.id))
            .where(
                and_(
                    ProfileFolderPermissionModel.organization_id == organization_id,
                    ProfileFolderPermissionModel.is_active == True
                )
            )
        )
        return result.scalar()

    def count_by_folder_path(self, folder_path: str, organization_id: UUID) -> int:
        """Count permissions for a specific folder path."""
        result = self.session.execute(
            select(func.count(ProfileFolderPermissionModel.id))
            .where(
                and_(
                    ProfileFolderPermissionModel.folder_path == folder_path,
                    ProfileFolderPermissionModel.organization_id == organization_id
                )
            )
        )
        return result.scalar()

    def exists_by_profile_and_folder(self, profile_id: UUID, folder_path: str) -> bool:
        """Check if permission exists for profile and folder."""
        result = self.session.execute(
            select(ProfileFolderPermissionModel.id)
            .where(
                and_(
                    ProfileFolderPermissionModel.profile_id == profile_id,
                    ProfileFolderPermissionModel.folder_path == folder_path
                )
            )
        )
        return result.scalar_one_or_none() is not None

    def delete(self, permission_id: UUID) -> bool:
        """Delete a permission."""
        result = self.session.execute(
            delete(ProfileFolderPermissionModel)
            .where(ProfileFolderPermissionModel.id == permission_id)
        )
        return result.rowcount > 0

    def delete_by_profile(self, profile_id: UUID) -> int:
        """Delete all permissions for a profile."""
        result = self.session.execute(
            delete(ProfileFolderPermissionModel)
            .where(ProfileFolderPermissionModel.profile_id == profile_id)
        )
        return result.rowcount

    def delete_by_folder_path(self, folder_path: str, organization_id: UUID) -> int:
        """Delete all permissions for a folder path."""
        result = self.session.execute(
            delete(ProfileFolderPermissionModel)
            .where(
                and_(
                    ProfileFolderPermissionModel.folder_path == folder_path,
                    ProfileFolderPermissionModel.organization_id == organization_id
                )
            )
        )
        return result.rowcount

    def delete_by_organization(self, organization_id: UUID) -> int:
        """Delete all permissions for an organization."""
        result = self.session.execute(
            delete(ProfileFolderPermissionModel)
            .where(ProfileFolderPermissionModel.organization_id == organization_id)
        )
        return result.rowcount

    def _to_domain_entity(self, model: ProfileFolderPermissionModel) -> ProfileFolderPermission:
        """Convert SQLAlchemy model to domain entity."""
        return ProfileFolderPermission(
            id=model.id,
            profile_id=model.profile_id,
            folder_path=model.folder_path,
            permission_level=FolderPermissionLevel(model.permission_level.value),
            organization_id=model.organization_id,
            created_by=model.created_by,
            is_active=model.is_active,
            notes=model.notes,
            extra_data=model.extra_data,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )