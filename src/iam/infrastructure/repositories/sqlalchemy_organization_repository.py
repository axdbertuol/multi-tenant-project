from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from ...domain.entities.organization import Organization
from ...domain.repositories.organization_repository import OrganizationRepository
from ...domain.value_objects.organization_name import OrganizationName
from ...domain.value_objects.organization_settings import OrganizationSettings
from ..database.models import OrganizationModel


class SqlAlchemyOrganizationRepository(OrganizationRepository):
    """SQLAlchemy implementation of OrganizationRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, organization: Organization) -> Organization:
        """Save an organization entity."""
        # Check if organization exists
        existing = self.session.get(OrganizationModel, organization.id)

        if existing:
            # Update existing organization
            existing.name = organization.name.value
            existing.description = organization.description
            existing.owner_id = organization.owner_id
            existing.is_active = organization.is_active
            existing.settings = organization.settings.to_dict()
            existing.member_count = organization.member_count
            existing.max_members = organization.max_members
            existing.updated_at = datetime.now(timezone.utc)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new organization
            org_model = OrganizationModel(
                id=organization.id,
                name=organization.name.value,
                description=organization.description,
                owner_id=organization.owner_id,
                is_active=organization.is_active,
                settings=organization.settings.to_dict(),
                member_count=organization.member_count,
                max_members=organization.max_members,
                created_at=organization.created_at,
                updated_at=organization.updated_at,
            )

            self.session.add(org_model)
            self.session.flush()
            return self._to_domain_entity(org_model)

    def find_by_id(self, organization_id: UUID) -> Optional[Organization]:
        """Find an organization by ID."""
        result = self.session.execute(
            select(OrganizationModel).where(OrganizationModel.id == organization_id)
        )
        org_model = result.scalar_one_or_none()

        if org_model:
            return self._to_domain_entity(org_model)
        return None

    def find_by_name(self, name: OrganizationName) -> Optional[Organization]:
        """Find an organization by name."""
        result = self.session.execute(
            select(OrganizationModel).where(OrganizationModel.name == name.value)
        )
        org_model = result.scalar_one_or_none()

        if org_model:
            return self._to_domain_entity(org_model)
        return None

    def find_by_owner(self, owner_id: UUID) -> List[Organization]:
        """Find organizations owned by a user."""
        result = self.session.execute(
            select(OrganizationModel).where(OrganizationModel.owner_id == owner_id)
        )
        org_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in org_models]

    def find_active_organizations(self) -> List[Organization]:
        """Find all active organizations."""
        result = self.session.execute(
            select(OrganizationModel).where(OrganizationModel.is_active)
        )
        org_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in org_models]

    def find_paginated(
        self,
        offset: int = 0,
        limit: int = 20,
        name_filter: Optional[str] = None,
        owner_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[Organization], int]:
        """Find organizations with pagination and filters."""
        query = select(OrganizationModel)
        count_query = select(OrganizationModel)

        # Apply filters
        if name_filter:
            query = query.where(OrganizationModel.name.ilike(f"%{name_filter}%"))
            count_query = count_query.where(
                OrganizationModel.name.ilike(f"%{name_filter}%")
            )

        if owner_id:
            query = query.where(OrganizationModel.owner_id == owner_id)
            count_query = count_query.where(OrganizationModel.owner_id == owner_id)

        if is_active is not None:
            query = query.where(OrganizationModel.is_active == is_active)
            count_query = count_query.where(OrganizationModel.is_active == is_active)

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = (
            query.offset(offset)
            .limit(limit)
            .order_by(OrganizationModel.created_at.desc())
        )
        result = self.session.execute(query)
        org_models = result.scalars().all()

        organizations = [self._to_domain_entity(model) for model in org_models]
        return organizations, total

    def delete(self, organization_id: UUID) -> bool:
        """Delete an organization (hard delete)."""
        result = self.session.execute(
            delete(OrganizationModel).where(OrganizationModel.id == organization_id)
        )
        return result.rowcount > 0

    def exists_by_name(self, name: OrganizationName) -> bool:
        """Check if an organization with the given name exists."""
        result = self.session.execute(
            select(OrganizationModel.id).where(OrganizationModel.name == name.value)
        )
        return result.scalar_one_or_none() is not None

    def update_member_count(self, organization_id: UUID, member_count: int) -> bool:
        """Update organization's member count."""
        result = self.session.execute(
            update(OrganizationModel)
            .where(OrganizationModel.id == organization_id)
            .values(member_count=member_count, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def transfer_ownership(self, organization_id: UUID, new_owner_id: UUID) -> bool:
        """Transfer organization ownership."""
        result = self.session.execute(
            update(OrganizationModel)
            .where(OrganizationModel.id == organization_id)
            .values(owner_id=new_owner_id, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def update_settings(
        self, organization_id: UUID, settings: OrganizationSettings
    ) -> bool:
        """Update organization settings."""
        result = self.session.execute(
            update(OrganizationModel)
            .where(OrganizationModel.id == organization_id)
            .values(settings=settings.to_dict(), updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def count_organizations_by_owner(self, owner_id: UUID) -> int:
        """Count organizations owned by a user."""
        result = self.session.execute(
            select(OrganizationModel).where(OrganizationModel.owner_id == owner_id)
        )
        return len(result.scalars().all())

    # Abstract method implementations (aliases for existing methods)
    def get_by_id(self, organization_id: UUID) -> Optional[Organization]:
        """Get organization by ID (interface method)."""
        return self.find_by_id(organization_id)

    def get_by_name(self, name: OrganizationName) -> Optional[Organization]:
        """Get organization by name (interface method)."""
        return self.find_by_name(name)

    def get_by_owner_id(self, owner_id: UUID) -> List[Organization]:
        """Get organizations owned by a user (interface method)."""
        return self.find_by_owner(owner_id)

    def list_active_organizations(
        self, limit: int = 100, offset: int = 0
    ) -> List[Organization]:
        """List active organizations with pagination (interface method)."""
        organizations, _ = self.find_paginated(
            offset=offset, limit=limit, is_active=True
        )
        return organizations

    def count_active_organizations(self) -> int:
        """Count total active organizations (interface method)."""
        result = self.session.execute(
            select(OrganizationModel).where(OrganizationModel.is_active)
        )
        return len(result.scalars().all())

    def get_user_organizations(self, user_id: UUID) -> List[Organization]:
        """Get organizations where user is a member (interface method)."""
        # For now, this returns organizations owned by the user
        # In a full implementation, this would join with user table
        return self.find_by_owner(user_id)

    def _to_domain_entity(self, org_model: OrganizationModel) -> Organization:
        """Convert SQLAlchemy model to domain entity."""
        return Organization(
            id=org_model.id,
            name=OrganizationName(value=org_model.name),
            description=org_model.description,
            owner_id=org_model.owner_id,
            is_active=org_model.is_active,
            settings=OrganizationSettings.from_dict(org_model.settings),
            member_count=org_model.member_count,
            max_members=org_model.max_members,
            created_at=org_model.created_at,
            updated_at=org_model.updated_at,
        )
