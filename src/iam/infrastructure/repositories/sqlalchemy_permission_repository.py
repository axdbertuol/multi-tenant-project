from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete, and_, text, join
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ...domain.entities.permission import Permission, PermissionAction
from ...domain.repositories.permission_repository import PermissionRepository
from ...infrastructure.database.models import (
    PermissionModel,
    PermissionActionEnum,
    role_permission_association,
    user_role_assignment,
)


class SqlAlchemyPermissionRepository(PermissionRepository):
    """SQLAlchemy implementation of PermissionRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, permission: Permission) -> Permission:
        """Save a permission entity."""
        # Check if permission exists
        existing = self.session.get(PermissionModel, permission.id)

        if existing:
            # Update existing permission
            existing.name = permission.name
            existing.description = permission.description
            existing.action = PermissionActionEnum(permission.action)
            existing.resource_type = permission.resource_type
            existing.is_active = permission.is_active
            existing.is_system_permission = permission.is_system_permission
            existing.updated_at = datetime.now(timezone.utc)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new permission
            permission_model = PermissionModel(
                id=permission.id,
                name=permission.name,
                description=permission.description,
                action=PermissionActionEnum(permission.action),
                resource_type=permission.resource_type,
                is_active=permission.is_active,
                is_system_permission=permission.is_system_permission,
                created_at=permission.created_at,
                updated_at=permission.updated_at,
            )

            self.session.add(permission_model)
            self.session.flush()
            return self._to_domain_entity(permission_model)

    def find_by_id(self, permission_id: UUID) -> Optional[Permission]:
        """Find a permission by ID."""
        result = self.session.execute(
            select(PermissionModel).where(PermissionModel.id == permission_id)
        )
        permission_model = result.scalar_one_or_none()

        if permission_model:
            return self._to_domain_entity(permission_model)
        return None

    def find_by_name_and_resource(
        self, name: str, resource_type: str
    ) -> Optional[Permission]:
        """Find a permission by name and resource type."""
        result = self.session.execute(
            select(PermissionModel).where(
                and_(
                    PermissionModel.name == name,
                    PermissionModel.resource_type == resource_type,
                )
            )
        )
        permission_model = result.scalar_one_or_none()

        if permission_model:
            return self._to_domain_entity(permission_model)
        return None

    def find_by_resource_type(self, resource_type: str) -> List[Permission]:
        """Find permissions for a specific resource type."""
        result = self.session.execute(
            select(PermissionModel).where(
                and_(
                    PermissionModel.resource_type == resource_type,
                    PermissionModel.is_active,
                )
            )
        )
        permission_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in permission_models]

    def find_by_action(self, action: str) -> List[Permission]:
        """Find permissions by action."""
        result = self.session.execute(
            select(PermissionModel).where(
                and_(
                    PermissionModel.action == PermissionActionEnum(action),
                    PermissionModel.is_active,
                )
            )
        )
        permission_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in permission_models]

    def find_system_permissions(self) -> List[Permission]:
        """Find all system permissions."""
        result = self.session.execute(
            select(PermissionModel).where(
                and_(
                    PermissionModel.is_system_permission,
                    PermissionModel.is_active,
                )
            )
        )
        permission_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in permission_models]

    def find_by_ids(self, permission_ids: List[UUID]) -> List[Permission]:
        """Find permissions by list of IDs."""
        result = self.session.execute(
            select(PermissionModel).where(PermissionModel.id.in_(permission_ids))
        )
        permission_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in permission_models]

    def find_paginated(
        self,
        include_system: bool = True,
        is_active: Optional[bool] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Permission], int]:
        """Find permissions with pagination and filters."""
        query = select(PermissionModel)
        count_query = select(PermissionModel)

        # Apply filters
        if not include_system:
            query = query.where(not PermissionModel.is_system_permission)
            count_query = count_query.where(not PermissionModel.is_system_permission)

        if is_active is not None:
            query = query.where(PermissionModel.is_active == is_active)
            count_query = count_query.where(PermissionModel.is_active == is_active)

        if resource_type:
            query = query.where(PermissionModel.resource_type == resource_type)
            count_query = count_query.where(
                PermissionModel.resource_type == resource_type
            )

        if action:
            query = query.where(PermissionModel.action == PermissionActionEnum(action))
            count_query = count_query.where(
                PermissionModel.action == PermissionActionEnum(action)
            )

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = (
            query.offset(offset)
            .limit(limit)
            .order_by(PermissionModel.created_at.desc())
        )
        result = self.session.execute(query)
        permission_models = result.scalars().all()

        permissions = [self._to_domain_entity(model) for model in permission_models]
        return permissions, total

    def search(
        self,
        query: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Permission], int]:
        """Search permissions with text query and filters."""
        db_query = select(PermissionModel)
        count_query = select(PermissionModel)

        # Apply text search
        if query:
            search_filter = PermissionModel.name.ilike(
                f"%{query}%"
            ) | PermissionModel.description.ilike(f"%{query}%")
            db_query = db_query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Apply filters
        if resource_type:
            db_query = db_query.where(PermissionModel.resource_type == resource_type)
            count_query = count_query.where(
                PermissionModel.resource_type == resource_type
            )

        if action:
            db_query = db_query.where(
                PermissionModel.action == PermissionActionEnum(action)
            )
            count_query = count_query.where(
                PermissionModel.action == PermissionActionEnum(action)
            )

        if is_active is not None:
            db_query = db_query.where(PermissionModel.is_active == is_active)
            count_query = count_query.where(PermissionModel.is_active == is_active)

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        db_query = (
            db_query.offset(offset)
            .limit(limit)
            .order_by(PermissionModel.created_at.desc())
        )
        result = self.session.execute(db_query)
        permission_models = result.scalars().all()

        permissions = [self._to_domain_entity(model) for model in permission_models]
        return permissions, total

    def delete(self, permission_id: UUID) -> bool:
        """Delete a permission (hard delete)."""
        result = self.session.execute(
            delete(PermissionModel).where(PermissionModel.id == permission_id)
        )
        return result.rowcount > 0

    def bulk_save(self, permissions: List[Permission]) -> List[Permission]:
        """Save multiple permissions in bulk."""
        saved_permissions = []

        for permission in permissions:
            # Check if permission exists
            existing = self.find_by_name_and_resource(
                permission.name, permission.resource_type
            )
            if existing:
                continue  # Skip existing permissions

            permission_model = PermissionModel(
                id=permission.id,
                name=permission.name,
                description=permission.description,
                action=PermissionActionEnum(permission.action),
                resource_type=permission.resource_type,
                is_active=permission.is_active,
                is_system_permission=permission.is_system_permission,
                created_at=permission.created_at,
                updated_at=permission.updated_at,
            )

            self.session.add(permission_model)
            saved_permissions.append(permission)

        self.session.flush()
        return saved_permissions

    def get_role_count(self, permission_id: UUID) -> int:
        """Get the number of roles that have this permission."""
        result = self.session.execute(
            text(
                "SELECT COUNT(*) FROM role_permissions WHERE permission_id = :permission_id"
            ).bindparam(permission_id=permission_id)
        )
        return result.scalar() or 0

    def get_resource_types(self) -> List[str]:
        """Get all unique resource types."""
        result = self.session.execute(select(PermissionModel.resource_type).distinct())
        return [row[0] for row in result.fetchall()]

    def get_actions(self) -> List[str]:
        """Get all permission actions."""
        return [pt.value for pt in PermissionActionEnum]

    def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions assigned to a role."""
        result = self.session.execute(
            select(PermissionModel)
            .join(
                role_permission_association,
                PermissionModel.id == role_permission_association.c.permission_id,
            )
            .where(
                and_(
                    role_permission_association.c.role_id == role_id,
                    PermissionModel.is_active,
                )
            )
            .order_by(PermissionModel.created_at.desc())
        )
        permission_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in permission_models]

    def get_by_resource_and_type(
        self, resource_type: str, action: PermissionAction
    ) -> List[Permission]:
        """Get permissions by resource type and action."""
        result = self.session.execute(
            select(PermissionModel)
            .where(
                and_(
                    PermissionModel.resource_type == resource_type,
                    PermissionModel.action == PermissionActionEnum(action),
                    PermissionModel.is_active,
                )
            )
            .order_by(PermissionModel.created_at.desc())
        )
        permission_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in permission_models]

    def get_user_permissions(
        self, user_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[Permission]:
        """Get all permissions for a user (through roles)."""
        query = (
            select(PermissionModel)
            .join(
                role_permission_association,
                PermissionModel.id == role_permission_association.c.permission_id,
            )
            .join(
                user_role_assignment,
                role_permission_association.c.role_id == user_role_assignment.c.role_id,
            )
            .where(
                and_(
                    user_role_assignment.c.user_id == user_id,
                    user_role_assignment.c.is_active,
                    PermissionModel.is_active,
                )
            )
        )

        # Add organization filter if provided
        if organization_id is not None:
            query = query.where(
                user_role_assignment.c.organization_id == organization_id
            )

        query = query.distinct().order_by(PermissionModel.created_at.desc())

        result = self.session.execute(query)
        permission_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in permission_models]

    def exists_by_name(self, name) -> bool:
        """Check if permission exists by name."""
        # Handle both string and PermissionName value object
        name_value = name.value if hasattr(name, "value") else str(name)

        result = self.session.execute(
            select(PermissionModel.id)
            .where(PermissionModel.name == name_value)
            .limit(1)
        )
        return result.scalar() is not None

    def _to_domain_entity(self, permission_model: PermissionModel) -> Permission:
        """Convert SQLAlchemy model to domain entity."""
        return Permission(
            id=permission_model.id,
            name=permission_model.name,
            description=permission_model.description,
            action=permission_model.action.value,
            resource_type=permission_model.resource_type,
            is_active=permission_model.is_active,
            is_system_permission=permission_model.is_system_permission,
            created_at=permission_model.created_at,
            updated_at=permission_model.updated_at,
        )
