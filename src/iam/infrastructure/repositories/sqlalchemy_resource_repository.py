from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ...domain.entities.resource import Resource
from ...domain.repositories.resource_repository import ResourceRepository
from ...infrastructure.database.models import ResourceModel


class SqlAlchemyResourceRepository(ResourceRepository):
    """SQLAlchemy implementation of ResourceRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, resource: Resource) -> Resource:
        """Save or update a resource."""
        try:
            # Check if resource exists
            existing = self.session.get(ResourceModel, resource.id)

            if existing:
                # Update existing resource
                existing.resource_type = resource.resource_type
                existing.resource_id = resource.resource_id
                existing.owner_id = resource.owner_id
                existing.organization_id = resource.organization_id
                existing.attributes = resource.attributes
                existing.is_active = resource.is_active
                existing.updated_at = datetime.now(timezone.utc)

                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                # Create new resource
                resource_model = ResourceModel(
                    id=resource.id,
                    resource_type=resource.resource_type,
                    resource_id=resource.resource_id,
                    owner_id=resource.owner_id,
                    organization_id=resource.organization_id,
                    attributes=resource.attributes,
                    is_active=resource.is_active,
                    created_at=resource.created_at,
                    updated_at=resource.updated_at,
                )

                self.session.add(resource_model)
                self.session.flush()
                return self._to_domain_entity(resource_model)

        except IntegrityError as e:
            self.session.rollback()
            if "resource_type" in str(e) and "resource_id" in str(e):
                raise ValueError(
                    f"Resource '{resource.resource_type}:{resource.resource_id}' already exists"
                )
            raise e

    def get_by_id(self, resource_id: UUID) -> Optional[Resource]:
        """Get resource by ID."""
        result = self.session.execute(
            select(ResourceModel).where(ResourceModel.id == resource_id)
        )
        resource_model = result.scalar_one_or_none()

        if resource_model:
            return self._to_domain_entity(resource_model)
        return None

    def get_by_resource_id(
        self, resource_type: str, resource_id: UUID
    ) -> Optional[Resource]:
        """Get resource by type and actual resource ID."""
        result = self.session.execute(
            select(ResourceModel).where(
                and_(
                    ResourceModel.resource_type == resource_type,
                    ResourceModel.resource_id == resource_id,
                    ResourceModel.is_active == True,
                )
            )
        )
        resource_model = result.scalar_one_or_none()

        if resource_model:
            return self._to_domain_entity(resource_model)
        return None

    def get_by_owner_id(self, owner_id: UUID) -> List[Resource]:
        """Get all resources owned by a user."""
        result = self.session.execute(
            select(ResourceModel).where(
                and_(
                    ResourceModel.owner_id == owner_id,
                    ResourceModel.is_active == True,
                )
            ).order_by(ResourceModel.created_at.desc())
        )
        resource_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in resource_models]

    def get_by_organization_id(self, organization_id: UUID) -> List[Resource]:
        """Get all resources belonging to an organization."""
        result = self.session.execute(
            select(ResourceModel).where(
                and_(
                    ResourceModel.organization_id == organization_id,
                    ResourceModel.is_active == True,
                )
            ).order_by(ResourceModel.created_at.desc())
        )
        resource_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in resource_models]

    def get_by_type(self, resource_type: str) -> List[Resource]:
        """Get all resources of a specific type."""
        result = self.session.execute(
            select(ResourceModel).where(
                and_(
                    ResourceModel.resource_type == resource_type,
                    ResourceModel.is_active == True,
                )
            ).order_by(ResourceModel.created_at.desc())
        )
        resource_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in resource_models]

    def find_by_attributes(
        self, resource_type: str, attributes: Dict[str, Any]
    ) -> List[Resource]:
        """Find resources by attributes."""
        query = select(ResourceModel).where(
            and_(
                ResourceModel.resource_type == resource_type,
                ResourceModel.is_active == True,
            )
        )

        # Filter by attributes using JSON contains operations
        for key, value in attributes.items():
            # Use PostgreSQL JSON contains operator
            query = query.where(ResourceModel.attributes[key].astext == str(value))

        result = self.session.execute(query.order_by(ResourceModel.created_at.desc()))
        resource_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in resource_models]

    def delete(self, resource_id: UUID) -> bool:
        """Delete resource by ID."""
        result = self.session.execute(
            delete(ResourceModel).where(ResourceModel.id == resource_id)
        )
        return result.rowcount > 0

    def delete_by_resource_id(self, resource_type: str, resource_id: UUID) -> bool:
        """Delete resource by type and actual resource ID."""
        result = self.session.execute(
            delete(ResourceModel).where(
                and_(
                    ResourceModel.resource_type == resource_type,
                    ResourceModel.resource_id == resource_id,
                )
            )
        )
        return result.rowcount > 0

    def list_active_resources(
        self, resource_type: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Resource]:
        """List active resources with pagination."""
        query = select(ResourceModel).where(ResourceModel.is_active == True)

        if resource_type:
            query = query.where(ResourceModel.resource_type == resource_type)

        query = (
            query.offset(offset)
            .limit(limit)
            .order_by(ResourceModel.created_at.desc())
        )

        result = self.session.execute(query)
        resource_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in resource_models]

    def count_user_resources(
        self, user_id: UUID, resource_type: Optional[str] = None
    ) -> int:
        """Count resources owned by a user."""
        query = select(ResourceModel).where(
            and_(
                ResourceModel.owner_id == user_id,
                ResourceModel.is_active == True,
            )
        )

        if resource_type:
            query = query.where(ResourceModel.resource_type == resource_type)

        result = self.session.execute(query)
        return len(result.scalars().all())

    def transfer_ownership(
        self, resource_type: str, resource_id: UUID, new_owner_id: UUID
    ) -> bool:
        """Transfer resource ownership."""
        resource_model = self.session.execute(
            select(ResourceModel).where(
                and_(
                    ResourceModel.resource_type == resource_type,
                    ResourceModel.resource_id == resource_id,
                    ResourceModel.is_active == True,
                )
            )
        ).scalar_one_or_none()

        if resource_model:
            resource_model.owner_id = new_owner_id
            resource_model.updated_at = datetime.now(timezone.utc)
            self.session.flush()
            return True

        return False

    def _to_domain_entity(self, resource_model: ResourceModel) -> Resource:
        """Convert SQLAlchemy model to domain entity."""
        return Resource(
            id=resource_model.id,
            resource_type=resource_model.resource_type,
            resource_id=resource_model.resource_id,
            owner_id=resource_model.owner_id,
            organization_id=resource_model.organization_id,
            attributes=resource_model.attributes,
            created_at=resource_model.created_at,
            updated_at=resource_model.updated_at,
            is_active=resource_model.is_active,
        )