from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, and_, text
from sqlalchemy.exc import IntegrityError

from ...domain.entities.role import Role
from ...domain.entities.permission import Permission
from ...domain.repositories.role_repository import RoleRepository
from ...infrastructure.database.models import (
    RoleModel,
    PermissionModel,
    UserModel,
    role_permission_association,
    user_role_assignment,
)


class SqlAlchemyRoleRepository(RoleRepository):
    """SQLAlchemy implementation of RoleRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, role: Role) -> Role:
        """Save a role entity."""
        # Check if role exists
        existing = self.session.get(RoleModel, role.id)

        if existing:
            # Update existing role
            existing.name = role.name
            existing.description = role.description
            existing.organization_id = role.organization_id
            existing.parent_role_id = role.parent_role_id
            existing.created_by = role.created_by
            existing.is_active = role.is_active
            existing.is_system_role = role.is_system_role
            existing.updated_at = datetime.now(timezone.utc)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new role
            role_model = RoleModel(
                id=role.id,
                name=role.name,
                description=role.description,
                organization_id=role.organization_id,
                parent_role_id=role.parent_role_id,
                created_by=role.created_by,
                is_active=role.is_active,
                is_system_role=role.is_system_role,
                created_at=role.created_at,
                updated_at=role.updated_at,
            )

            self.session.add(role_model)
            self.session.flush()
            return self._to_domain_entity(role_model)

    def get_by_id(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID."""
        result = self.session.execute(select(RoleModel).where(RoleModel.id == role_id))
        role_model = result.scalar_one_or_none()

        if role_model:
            return self._to_domain_entity(role_model)
        return None

    def get_by_name(
        self, name, organization_id: Optional[UUID] = None
    ) -> Optional[Role]:
        """Get role by name within organization scope."""
        result = self.session.execute(
            select(RoleModel).where(
                and_(
                    RoleModel.name == name.value,
                    RoleModel.organization_id == organization_id,
                )
            )
        )
        role_model = result.scalar_one_or_none()

        if role_model:
            return self._to_domain_entity(role_model)
        return None

    def get_organization_roles(self, organization_id: UUID) -> List[Role]:
        """Get all roles for an organization."""
        result = self.session.execute(
            select(RoleModel).where(
                and_(
                    RoleModel.organization_id == organization_id,
                    RoleModel.is_active,
                )
            )
        )
        role_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in role_models]

    def get_system_roles(self) -> List[Role]:
        """Get all system roles."""
        result = self.session.execute(
            select(RoleModel).where(and_(RoleModel.is_system_role, RoleModel.is_active))
        )
        role_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in role_models]

    def get_user_roles(
        self, user_id: UUID, organization_id: Optional[UUID] = None
    ) -> List[Role]:
        """Get roles assigned to a user."""
        query = (
            select(RoleModel)
            .select_from(RoleModel.join(user_role_assignment))
            .where(
                and_(
                    user_role_assignment.c.user_id == user_id,
                    user_role_assignment.c.is_active,
                    RoleModel.is_active,
                )
            )
        )

        # If organization_id is specified, filter by role's organization_id
        if organization_id:
            query = query.where(RoleModel.organization_id == organization_id)

        result = self.session.execute(query)
        role_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in role_models]

    def exists_by_name(self, name, organization_id: Optional[UUID] = None) -> bool:
        """Check if role exists by name within organization scope."""
        result = self.session.execute(
            select(RoleModel.id)
            .where(
                and_(
                    RoleModel.name == name.value,
                    RoleModel.organization_id == organization_id,
                )
            )
            .limit(1)
        )
        return result.first() is not None

    def list_active_roles(
        self, organization_id: Optional[UUID] = None, limit: int = 100, offset: int = 0
    ) -> List[Role]:
        """List active roles with pagination."""
        query = select(RoleModel).where(RoleModel.is_active)

        if organization_id is not None:
            query = query.where(RoleModel.organization_id == organization_id)

        query = query.offset(offset).limit(limit).order_by(RoleModel.name.asc())
        result = self.session.execute(query)
        role_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in role_models]

    def count_role_assignments(self, role_id: UUID) -> int:
        """Count how many users have this role assigned."""
        return self.get_assignment_count(role_id)

    def find_paginated(
        self,
        organization_id: Optional[UUID] = None,
        include_system: bool = True,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Role], int]:
        """Find roles with pagination and filters."""
        query = select(RoleModel)
        count_query = select(RoleModel)

        # Apply filters
        if organization_id is not None:
            query = query.where(RoleModel.organization_id == organization_id)
            count_query = count_query.where(
                RoleModel.organization_id == organization_id
            )

        if not include_system:
            query = query.where(not RoleModel.is_system_role)
            count_query = count_query.where(not RoleModel.is_system_role)

        if is_active is not None:
            query = query.where(RoleModel.is_active == is_active)
            count_query = count_query.where(RoleModel.is_active == is_active)

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = query.offset(offset).limit(limit).order_by(RoleModel.created_at.desc())
        result = self.session.execute(query)
        role_models = result.scalars().all()

        roles = [self._to_domain_entity(model) for model in role_models]
        return roles, total

    def delete(self, role_id: UUID) -> bool:
        """Delete a role (hard delete)."""
        result = self.session.execute(delete(RoleModel).where(RoleModel.id == role_id))
        return result.rowcount > 0

    def assign_permissions(self, role_id: UUID, permission_ids: List[UUID]) -> bool:
        """Assign permissions to a role."""
        # Remove existing permissions first
        self.session.execute(
            text("DELETE FROM role_permissions WHERE role_id = :role_id").bindparam(
                role_id=role_id
            )
        )

        # Add new permissions
        for permission_id in permission_ids:
            self.session.execute(
                text(
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)"
                ).bindparam(role_id=role_id, permission_id=permission_id)
            )

        return True

    def remove_permissions(self, role_id: UUID, permission_ids: List[UUID]) -> bool:
        """Remove specific permissions from a role."""
        for permission_id in permission_ids:
            self.session.execute(
                text(
                    "DELETE FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"
                ).bindparam(role_id=role_id, permission_id=permission_id)
            )

        return True

    def replace_permissions(self, role_id: UUID, permission_ids: List[UUID]) -> bool:
        """Replace all role permissions with new ones."""
        return self.assign_permissions(role_id, permission_ids)

    def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all permissions for a role."""
        result = self.session.execute(
            select(PermissionModel)
            .select_from(PermissionModel.join(role_permission_association))
            .where(role_permission_association.c.role_id == role_id)
        )
        permission_models = result.scalars().all()

        return [self._permission_to_domain_entity(model) for model in permission_models]

    def assign_role_to_user(
        self,
        user_id: UUID,
        role_id: UUID,
        assigned_by: UUID,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Assign a role to a user."""
        self.session.execute(
            text("""
                INSERT INTO user_role_assignments 
                (user_id, role_id, assigned_by, expires_at) 
                VALUES (:user_id, :role_id, :assigned_by, :expires_at)
            """).bindparam(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by,
                expires_at=expires_at,
            )
        )
        return True

    def remove_role_from_user(
        self, user_id: UUID, role_id: UUID
    ) -> bool:
        """Remove a role from a user."""
        query = """
            UPDATE user_role_assignments 
            SET is_active = false 
            WHERE user_id = :user_id AND role_id = :role_id
        """
        params = {"user_id": user_id, "role_id": role_id}

        result = self.session.execute(text(query).bindparam(**params))
        return result.rowcount > 0

    def get_permission_count(self, role_id: UUID) -> int:
        """Get the number of permissions assigned to a role."""
        result = self.session.execute(
            text(
                "SELECT COUNT(*) FROM role_permissions WHERE role_id = :role_id"
            ).bindparam(role_id=role_id)
        )
        return result.scalar() or 0

    def get_assignment_count(self, role_id: UUID) -> int:
        """Get the number of users assigned to a role."""
        result = self.session.execute(
            text(
                "SELECT COUNT(*) FROM user_role_assignments WHERE role_id = :role_id AND is_active = true"
            ).bindparam(role_id=role_id)
        )
        return result.scalar() or 0

    def get_child_roles(self, parent_role_id: UUID) -> List[Role]:
        """Get all direct child roles of a parent role."""
        result = self.session.execute(
            select(RoleModel).where(
                and_(RoleModel.parent_role_id == parent_role_id, RoleModel.is_active)
            )
        )
        role_models = result.scalars().all()
        return [self._to_domain_entity(model) for model in role_models]

    def get_roles_by_parent(self, parent_role_id: Optional[UUID]) -> List[Role]:
        """Get all roles with the specified parent (None for root roles)."""
        if parent_role_id is None:
            # Get root roles (roles with no parent)
            result = self.session.execute(
                select(RoleModel).where(
                    and_(RoleModel.parent_role_id.is_(None), RoleModel.is_active)
                )
            )
        else:
            # Get roles with specific parent
            result = self.session.execute(
                select(RoleModel).where(
                    and_(
                        RoleModel.parent_role_id == parent_role_id, RoleModel.is_active
                    )
                )
            )

        role_models = result.scalars().all()
        return [self._to_domain_entity(model) for model in role_models]

    def get_role_hierarchy(self, organization_id: Optional[UUID] = None) -> List[Role]:
        """Get all roles in hierarchical order for an organization."""
        query = select(RoleModel).where(RoleModel.is_active)

        if organization_id is not None:
            query = query.where(RoleModel.organization_id == organization_id)

        # Order by parent_role_id nulls first (root roles first), then by name
        query = query.order_by(
            RoleModel.parent_role_id.asc().nulls_first(), RoleModel.name.asc()
        )

        result = self.session.execute(query)
        role_models = result.scalars().all()
        return [self._to_domain_entity(model) for model in role_models]

    def has_child_roles(self, role_id: UUID) -> bool:
        """Check if role has any child roles."""
        result = self.session.execute(
            select(RoleModel.id)
            .where(and_(RoleModel.parent_role_id == role_id, RoleModel.is_active))
            .limit(1)
        )
        return result.first() is not None

    def get_root_roles(self, organization_id: Optional[UUID] = None) -> List[Role]:
        """Get all root roles (roles with no parent) for an organization."""
        query = select(RoleModel).where(
            and_(RoleModel.parent_role_id.is_(None), RoleModel.is_active)
        )

        if organization_id is not None:
            query = query.where(RoleModel.organization_id == organization_id)

        result = self.session.execute(query)
        role_models = result.scalars().all()
        return [self._to_domain_entity(model) for model in role_models]

    def get_user_roles_in_organization(self, user_id: UUID, organization_id: UUID) -> List[Role]:
        """Get roles assigned to a user that belong to a specific organization."""
        # First verify user is member of the organization
        user_query = select(UserModel).where(
            and_(
                UserModel.id == user_id,
                UserModel.organization_id == organization_id
            )
        )
        user_result = self.session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return []  # User is not a member of this organization
        
        # Get user's roles that belong to this organization
        query = (
            select(RoleModel)
            .select_from(RoleModel.join(user_role_assignment))
            .where(
                and_(
                    user_role_assignment.c.user_id == user_id,
                    user_role_assignment.c.is_active,
                    RoleModel.is_active,
                    RoleModel.organization_id == organization_id,
                )
            )
        )
        
        result = self.session.execute(query)
        role_models = result.scalars().all()
        
        return [self._to_domain_entity(model) for model in role_models]

    def get_users_with_role_in_organization(self, role_id: UUID, organization_id: UUID) -> List[UUID]:
        """Get all users that have a specific role and belong to a specific organization."""
        query = (
            select(UserModel.id)
            .select_from(
                UserModel.join(user_role_assignment, UserModel.id == user_role_assignment.c.user_id)
            )
            .where(
                and_(
                    user_role_assignment.c.role_id == role_id,
                    user_role_assignment.c.is_active,
                    UserModel.organization_id == organization_id,
                    UserModel.is_active,
                )
            )
        )
        
        result = self.session.execute(query)
        user_ids = result.scalars().all()
        
        return list(user_ids)

    def remove_all_user_roles(self, user_id: UUID) -> bool:
        """Remove all roles from a user (typically when user leaves organization)."""
        query = """
            UPDATE user_role_assignments 
            SET is_active = false 
            WHERE user_id = :user_id
        """
        
        result = self.session.execute(text(query).bindparam(user_id=user_id))
        return result.rowcount > 0

    def _to_domain_entity(self, role_model: RoleModel) -> Role:
        """Convert SQLAlchemy model to domain entity."""
        return Role(
            id=role_model.id,
            name=role_model.name,
            description=role_model.description,
            organization_id=role_model.organization_id,
            parent_role_id=role_model.parent_role_id,
            created_by=role_model.created_by,
            is_active=role_model.is_active,
            is_system_role=role_model.is_system_role,
            created_at=role_model.created_at,
            updated_at=role_model.updated_at,
        )

    def _permission_to_domain_entity(
        self, permission_model: PermissionModel
    ) -> Permission:
        """Convert SQLAlchemy permission model to domain entity."""
        return Permission(
            id=permission_model.id,
            name=permission_model.name,
            description=permission_model.description,
            permission_type=permission_model.permission_type.value,
            resource_type=permission_model.resource_type,
            is_active=permission_model.is_active,
            is_system_permission=permission_model.is_system_permission,
            created_at=permission_model.created_at,
            updated_at=permission_model.updated_at,
        )
