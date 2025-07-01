from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_
from sqlalchemy.exc import IntegrityError

from ...domain.entities.user_organization_role import UserOrganizationRole
from ...domain.repositories.user_organization_role_repository import (
    UserOrganizationRoleRepository,
)
from ..database.models import UserOrganizationRoleModel


class SqlAlchemyUserOrganizationRoleRepository(UserOrganizationRoleRepository):
    """SQLAlchemy implementation of UserOrganizationRoleRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, role_assignment: UserOrganizationRole) -> UserOrganizationRole:
        """Save a user organization role entity."""
        try:
            # Check if role assignment exists
            existing = self.session.get(UserOrganizationRoleModel, role_assignment.id)

            if existing:
                # Update existing role assignment
                existing.user_id = role_assignment.user_id
                existing.organization_id = role_assignment.organization_id
                existing.role_id = role_assignment.role_id
                existing.assigned_by = role_assignment.assigned_by
                existing.assigned_at = role_assignment.assigned_at
                existing.expires_at = role_assignment.expires_at
                existing.is_active = role_assignment.is_active
                existing.revoked_at = role_assignment.revoked_at
                existing.revoked_by = role_assignment.revoked_by
                existing.updated_at = datetime.now(timezone.utc)

                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                # Create new role assignment
                role_model = UserOrganizationRoleModel(
                    id=role_assignment.id,
                    user_id=role_assignment.user_id,
                    organization_id=role_assignment.organization_id,
                    role_id=role_assignment.role_id,
                    assigned_by=role_assignment.assigned_by,
                    assigned_at=role_assignment.assigned_at,
                    expires_at=role_assignment.expires_at,
                    is_active=role_assignment.is_active,
                    revoked_at=role_assignment.revoked_at,
                    revoked_by=role_assignment.revoked_by,
                    created_at=role_assignment.created_at,
                    updated_at=role_assignment.updated_at,
                )

                self.session.add(role_model)
                self.session.flush()
                return self._to_domain_entity(role_model)

        except IntegrityError as e:
            self.session.rollback()
            raise e

    def get_by_id(self, role_id: UUID) -> Optional[UserOrganizationRole]:
        """Get role assignment by ID."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                UserOrganizationRoleModel.id == role_id
            )
        )
        role_model = result.scalar_one_or_none()

        if role_model:
            return self._to_domain_entity(role_model)
        return None

    def get_by_user_and_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> Optional[UserOrganizationRole]:
        """Get active role assignment for user in organization."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.user_id == user_id,
                    UserOrganizationRoleModel.organization_id == organization_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        role_model = result.scalar_one_or_none()

        if role_model:
            return self._to_domain_entity(role_model)
        return None

    def get_user_roles_in_organization(
        self, organization_id: UUID
    ) -> List[UserOrganizationRole]:
        """Get all user role assignments in an organization."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.organization_id == organization_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        role_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in role_models]

    def get_user_organizations(self, user_id: UUID) -> List[UserOrganizationRole]:
        """Get all organizations where user has a role."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.user_id == user_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        role_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in role_models]

    def user_has_role_in_organization(
        self, user_id: UUID, organization_id: UUID, role_id: UUID
    ) -> bool:
        """Check if user has specific role in organization."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.user_id == user_id,
                    UserOrganizationRoleModel.organization_id == organization_id,
                    UserOrganizationRoleModel.role_id == role_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        return result.scalar_one_or_none() is not None


    def count_organization_users(self, organization_id: UUID) -> int:
        """Count active users in organization."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.organization_id == organization_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        return len(result.scalars().all())

    def remove_user_from_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> bool:
        """Remove user from organization."""
        result = self.session.execute(
            update(UserOrganizationRoleModel)
            .where(
                and_(
                    UserOrganizationRoleModel.user_id == user_id,
                    UserOrganizationRoleModel.organization_id == organization_id,
                )
            )
            .values(is_active=False, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def delete(self, role_id: UUID) -> bool:
        """Delete role by ID."""
        result = self.session.execute(
            delete(UserOrganizationRoleModel).where(
                UserOrganizationRoleModel.id == role_id
            )
        )
        return result.rowcount > 0

    def cleanup_expired_roles(self) -> int:
        """Cleanup expired roles. Returns count of cleaned roles."""
        current_time = datetime.now(timezone.utc)
        result = self.session.execute(
            update(UserOrganizationRoleModel)
            .where(
                and_(
                    UserOrganizationRoleModel.expires_at <= current_time,
                    UserOrganizationRoleModel.is_active,
                )
            )
            .values(is_active=False, updated_at=current_time)
        )
        return result.rowcount

    def _to_domain_entity(
        self, role_model: UserOrganizationRoleModel
    ) -> UserOrganizationRole:
        """Convert SQLAlchemy model to domain entity."""
        return UserOrganizationRole(
            id=role_model.id,
            user_id=role_model.user_id,
            organization_id=role_model.organization_id,
            role_id=role_model.role_id,
            assigned_by=role_model.assigned_by,
            assigned_at=role_model.assigned_at,
            expires_at=role_model.expires_at,
            is_active=role_model.is_active,
            revoked_at=role_model.revoked_at,
            revoked_by=role_model.revoked_by,
            created_at=role_model.created_at,
            updated_at=role_model.updated_at,
        )
