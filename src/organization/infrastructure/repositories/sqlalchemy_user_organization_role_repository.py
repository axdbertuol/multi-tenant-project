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
from ..database.models import (
    UserOrganizationRoleModel,
    OrganizationRoleEnum,
)


class SqlAlchemyUserOrganizationRoleRepository(UserOrganizationRoleRepository):
    """SQLAlchemy implementation of UserOrganizationRoleRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, membership: UserOrganizationRole) -> UserOrganizationRole:
        """Save a user organization role entity."""
        try:
            # Check if membership exists
            existing = self.session.get(UserOrganizationRoleModel, membership.id)

            if existing:
                # Update existing membership
                existing.user_id = membership.user_id
                existing.organization_id = membership.organization_id
                existing.role = OrganizationRoleEnum(membership.role)
                existing.assigned_by = membership.assigned_by
                existing.expires_at = membership.expires_at
                existing.is_active = membership.is_active
                existing.updated_at = datetime.now(timezone.utc)

                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                # Create new membership
                membership_model = UserOrganizationRoleModel(
                    id=membership.id,
                    user_id=membership.user_id,
                    organization_id=membership.organization_id,
                    role=OrganizationRoleEnum(membership.role),
                    assigned_by=membership.assigned_by,
                    expires_at=membership.expires_at,
                    is_active=membership.is_active,
                    created_at=membership.created_at,
                    updated_at=membership.updated_at,
                )

                self.session.add(membership_model)
                self.session.flush()
                return self._to_domain_entity(membership_model)

        except IntegrityError as e:
            self.session.rollback()
            raise e

    def find_by_id(self, membership_id: UUID) -> Optional[UserOrganizationRole]:
        """Find a membership by ID."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                UserOrganizationRoleModel.id == membership_id
            )
        )
        membership_model = result.scalar_one_or_none()

        if membership_model:
            return self._to_domain_entity(membership_model)
        return None

    def find_by_user_and_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> Optional[UserOrganizationRole]:
        """Find active membership for user in organization."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.user_id == user_id,
                    UserOrganizationRoleModel.organization_id == organization_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        membership_model = result.scalar_one_or_none()

        if membership_model:
            return self._to_domain_entity(membership_model)
        return None

    def find_user_memberships(self, user_id: UUID) -> List[UserOrganizationRole]:
        """Find all active memberships for a user."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.user_id == user_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        membership_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in membership_models]

    def find_organization_members(
        self, organization_id: UUID
    ) -> List[UserOrganizationRole]:
        """Find all active members of an organization."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.organization_id == organization_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        membership_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in membership_models]

    def find_organization_members_by_role(
        self, organization_id: UUID, role: str
    ) -> List[UserOrganizationRole]:
        """Find organization members with specific role."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.organization_id == organization_id,
                    UserOrganizationRoleModel.role == OrganizationRoleEnum(role),
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        membership_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in membership_models]

    def find_expired_memberships(self) -> List[UserOrganizationRole]:
        """Find expired memberships that are still active."""
        current_time = datetime.now(timezone.utc)
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.expires_at <= current_time,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        membership_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in membership_models]

    def find_paginated(
        self,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[UserOrganizationRole], int]:
        """Find memberships with pagination and filters."""
        query = select(UserOrganizationRoleModel)
        count_query = select(UserOrganizationRoleModel)

        # Apply filters
        if organization_id:
            query = query.where(
                UserOrganizationRoleModel.organization_id == organization_id
            )
            count_query = count_query.where(
                UserOrganizationRoleModel.organization_id == organization_id
            )

        if user_id:
            query = query.where(UserOrganizationRoleModel.user_id == user_id)
            count_query = count_query.where(
                UserOrganizationRoleModel.user_id == user_id
            )

        if role:
            query = query.where(
                UserOrganizationRoleModel.role == OrganizationRoleEnum(role)
            )
            count_query = count_query.where(
                UserOrganizationRoleModel.role == OrganizationRoleEnum(role)
            )

        if is_active is not None:
            query = query.where(UserOrganizationRoleModel.is_active == is_active)
            count_query = count_query.where(
                UserOrganizationRoleModel.is_active == is_active
            )

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = (
            query.offset(offset)
            .limit(limit)
            .order_by(UserOrganizationRoleModel.created_at.desc())
        )
        result = self.session.execute(query)
        membership_models = result.scalars().all()

        memberships = [self._to_domain_entity(model) for model in membership_models]
        return memberships, total

    def delete(self, membership_id: UUID) -> bool:
        """Delete a membership (hard delete)."""
        result = self.session.execute(
            delete(UserOrganizationRoleModel).where(
                UserOrganizationRoleModel.id == membership_id
            )
        )
        return result.rowcount > 0

    def deactivate_membership(self, membership_id: UUID) -> bool:
        """Deactivate a membership (soft delete)."""
        result = self.session.execute(
            update(UserOrganizationRoleModel)
            .where(UserOrganizationRoleModel.id == membership_id)
            .values(is_active=False, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def update_role(self, membership_id: UUID, new_role: str) -> bool:
        """Update membership role."""
        result = self.session.execute(
            update(UserOrganizationRoleModel)
            .where(UserOrganizationRoleModel.id == membership_id)
            .values(
                role=OrganizationRoleEnum(new_role),
                updated_at=datetime.now(timezone.utc),
            )
        )
        return result.rowcount > 0

    def extend_membership(self, membership_id: UUID, new_expiration: datetime) -> bool:
        """Extend membership expiration."""
        result = self.session.execute(
            update(UserOrganizationRoleModel)
            .where(UserOrganizationRoleModel.id == membership_id)
            .values(expires_at=new_expiration, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def count_organization_members(self, organization_id: UUID) -> int:
        """Count active members in an organization."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.organization_id == organization_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        return len(result.scalars().all())

    def count_user_memberships(self, user_id: UUID) -> int:
        """Count active memberships for a user."""
        result = self.session.execute(
            select(UserOrganizationRoleModel).where(
                and_(
                    UserOrganizationRoleModel.user_id == user_id,
                    UserOrganizationRoleModel.is_active,
                )
            )
        )
        return len(result.scalars().all())

    def expire_memberships(self) -> int:
        """Mark expired memberships as inactive."""
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
        self, membership_model: UserOrganizationRoleModel
    ) -> UserOrganizationRole:
        """Convert SQLAlchemy model to domain entity."""
        return UserOrganizationRole(
            id=membership_model.id,
            user_id=membership_model.user_id,
            organization_id=membership_model.organization_id,
            role=membership_model.role.value,
            assigned_by=membership_model.assigned_by,
            expires_at=membership_model.expires_at,
            is_active=membership_model.is_active,
            created_at=membership_model.created_at,
            updated_at=membership_model.updated_at,
        )
