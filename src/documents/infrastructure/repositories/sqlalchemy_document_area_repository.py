from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import delete, select, func, and_, or_
from sqlalchemy.orm import Session
from ...domain.entities.document_area import DocumentArea
from ...domain.repositories.document_area_repository import DocumentAreaRepository
from ..database.models import DocumentAreaModel


class SqlAlchemyDocumentAreaRepository(DocumentAreaRepository):
    """SQLAlchemy implementation of DocumentAreaRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, area: DocumentArea) -> DocumentArea:
        """Save a document area entity."""
        # Check if area exists
        existing = self.session.get(DocumentAreaModel, area.id)

        if existing:
            # Update existing area
            existing.name = area.name
            existing.description = area.description
            existing.organization_id = area.organization_id
            existing.parent_area_id = area.parent_area_id
            existing.folder_path = area.folder_path
            existing.created_by = area.created_by
            existing.is_active = area.is_active
            existing.is_system_area = area.is_system_area
            existing.updated_at = datetime.now(timezone.utc)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new area
            area_model = DocumentAreaModel(
                id=area.id,
                name=area.name,
                description=area.description,
                organization_id=area.organization_id,
                parent_area_id=area.parent_area_id,
                folder_path=area.folder_path,
                created_by=area.created_by,
                is_active=area.is_active,
                is_system_area=area.is_system_area,
                created_at=area.created_at,
                updated_at=area.updated_at,
            )

            self.session.add(area_model)
            self.session.flush()
            return self._to_domain_entity(area_model)

    def get_by_id(self, area_id: UUID) -> Optional[DocumentArea]:
        """Get area by ID."""
        result = self.session.execute(
            select(DocumentAreaModel).where(DocumentAreaModel.id == area_id)
        )
        area_model = result.scalar_one_or_none()

        if area_model:
            return self._to_domain_entity(area_model)
        return None

    def get_by_name(self, name: str, organization_id: UUID) -> Optional[DocumentArea]:
        """Get area by name within organization."""
        result = self.session.execute(
            select(DocumentAreaModel).where(
                and_(
                    DocumentAreaModel.name == name,
                    DocumentAreaModel.organization_id == organization_id,
                )
            )
        )
        area_model = result.scalar_one_or_none()

        if area_model:
            return self._to_domain_entity(area_model)
        return None

    def get_by_folder_path(self, folder_path: str, organization_id: UUID) -> Optional[DocumentArea]:
        """Get area by folder path within organization."""
        result = self.session.execute(
            select(DocumentAreaModel).where(
                and_(
                    DocumentAreaModel.folder_path == folder_path,
                    DocumentAreaModel.organization_id == organization_id,
                )
            )
        )
        area_model = result.scalar_one_or_none()

        if area_model:
            return self._to_domain_entity(area_model)
        return None

    def get_by_organization(self, organization_id: UUID) -> List[DocumentArea]:
        """Get all areas for an organization."""
        result = self.session.execute(
            select(DocumentAreaModel)
            .where(DocumentAreaModel.organization_id == organization_id)
            .order_by(DocumentAreaModel.name)
        )
        area_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in area_models]

    def get_active_by_organization(self, organization_id: UUID) -> List[DocumentArea]:
        """Get active areas for an organization."""
        result = self.session.execute(
            select(DocumentAreaModel)
            .where(
                and_(
                    DocumentAreaModel.organization_id == organization_id,
                    DocumentAreaModel.is_active == True,
                )
            )
            .order_by(DocumentAreaModel.name)
        )
        area_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in area_models]

    def get_root_areas(self, organization_id: UUID) -> List[DocumentArea]:
        """Get root areas (without parent) for an organization."""
        result = self.session.execute(
            select(DocumentAreaModel)
            .where(
                and_(
                    DocumentAreaModel.organization_id == organization_id,
                    DocumentAreaModel.parent_area_id.is_(None),
                    DocumentAreaModel.is_active == True,
                )
            )
            .order_by(DocumentAreaModel.name)
        )
        area_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in area_models]

    def get_child_areas(self, parent_area_id: UUID) -> List[DocumentArea]:
        """Get child areas of a parent area."""
        result = self.session.execute(
            select(DocumentAreaModel)
            .where(
                and_(
                    DocumentAreaModel.parent_area_id == parent_area_id,
                    DocumentAreaModel.is_active == True,
                )
            )
            .order_by(DocumentAreaModel.name)
        )
        area_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in area_models]

    def get_hierarchy_for_area(self, area_id: UUID) -> List[DocumentArea]:
        """Get complete hierarchy for an area (all ancestors and descendants)."""
        # First get the area itself
        area = self.get_by_id(area_id)
        if not area:
            return []

        # Get all areas in the same organization
        all_areas = self.get_by_organization(area.organization_id)
        
        # Filter to get relevant hierarchy
        hierarchy = []
        area_map = {a.id: a for a in all_areas}
        
        # Add the area itself
        hierarchy.append(area)
        
        # Add all ancestors
        current = area
        while current.parent_area_id:
            parent = area_map.get(current.parent_area_id)
            if parent:
                hierarchy.append(parent)
                current = parent
            else:
                break
        
        # Add all descendants (recursive)
        def add_descendants(parent_id: UUID):
            for child_area in all_areas:
                if child_area.parent_area_id == parent_id:
                    if child_area not in hierarchy:
                        hierarchy.append(child_area)
                        add_descendants(child_area.id)
        
        add_descendants(area.id)
        
        return hierarchy

    def get_areas_by_folder_prefix(self, folder_prefix: str, organization_id: UUID) -> List[DocumentArea]:
        """Get areas by folder path prefix."""
        result = self.session.execute(
            select(DocumentAreaModel)
            .where(
                and_(
                    DocumentAreaModel.folder_path.startswith(folder_prefix),
                    DocumentAreaModel.organization_id == organization_id,
                    DocumentAreaModel.is_active == True,
                )
            )
            .order_by(DocumentAreaModel.folder_path)
        )
        area_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in area_models]

    def get_system_areas(self) -> List[DocumentArea]:
        """Get all system areas."""
        result = self.session.execute(
            select(DocumentAreaModel)
            .where(DocumentAreaModel.is_system_area == True)
            .order_by(DocumentAreaModel.name)
        )
        area_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in area_models]

    def get_areas_created_by(self, created_by: UUID, organization_id: UUID) -> List[DocumentArea]:
        """Get areas created by a specific user."""
        result = self.session.execute(
            select(DocumentAreaModel)
            .where(
                and_(
                    DocumentAreaModel.created_by == created_by,
                    DocumentAreaModel.organization_id == organization_id,
                )
            )
            .order_by(DocumentAreaModel.created_at.desc())
        )
        area_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in area_models]

    def find_by_name_pattern(self, pattern: str, organization_id: UUID) -> List[DocumentArea]:
        """Find areas by name pattern."""
        result = self.session.execute(
            select(DocumentAreaModel)
            .where(
                and_(
                    DocumentAreaModel.name.ilike(f"%{pattern}%"),
                    DocumentAreaModel.organization_id == organization_id,
                    DocumentAreaModel.is_active == True,
                )
            )
            .order_by(DocumentAreaModel.name)
        )
        area_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in area_models]

    def exists_by_name(self, name: str, organization_id: UUID) -> bool:
        """Check if area with name exists in organization."""
        result = self.session.execute(
            select(DocumentAreaModel.id).where(
                and_(
                    DocumentAreaModel.name == name,
                    DocumentAreaModel.organization_id == organization_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    def exists_by_folder_path(self, folder_path: str, organization_id: UUID) -> bool:
        """Check if area with folder path exists in organization."""
        result = self.session.execute(
            select(DocumentAreaModel.id).where(
                and_(
                    DocumentAreaModel.folder_path == folder_path,
                    DocumentAreaModel.organization_id == organization_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    def count_by_organization(self, organization_id: UUID) -> int:
        """Count areas in organization."""
        result = self.session.execute(
            select(func.count(DocumentAreaModel.id)).where(
                DocumentAreaModel.organization_id == organization_id
            )
        )
        return result.scalar()

    def count_active_by_organization(self, organization_id: UUID) -> int:
        """Count active areas in organization."""
        result = self.session.execute(
            select(func.count(DocumentAreaModel.id)).where(
                and_(
                    DocumentAreaModel.organization_id == organization_id,
                    DocumentAreaModel.is_active == True,
                )
            )
        )
        return result.scalar()

    def get_recently_created(self, organization_id: UUID, days: int = 30) -> List[DocumentArea]:
        """Get areas created within the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = self.session.execute(
            select(DocumentAreaModel)
            .where(
                and_(
                    DocumentAreaModel.organization_id == organization_id,
                    DocumentAreaModel.created_at >= cutoff_date,
                )
            )
            .order_by(DocumentAreaModel.created_at.desc())
        )
        area_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in area_models]

    def delete(self, area_id: UUID) -> bool:
        """Delete an area."""
        result = self.session.execute(
            delete(DocumentAreaModel).where(DocumentAreaModel.id == area_id)
        )
        return result.rowcount > 0

    def _to_domain_entity(self, area_model: DocumentAreaModel) -> DocumentArea:
        """Convert SQLAlchemy model to domain entity."""
        return DocumentArea(
            id=area_model.id,
            name=area_model.name,
            description=area_model.description,
            organization_id=area_model.organization_id,
            parent_area_id=area_model.parent_area_id,
            folder_path=area_model.folder_path,
            created_at=area_model.created_at,
            updated_at=area_model.updated_at,
            created_by=area_model.created_by,
            is_active=area_model.is_active,
            is_system_area=area_model.is_system_area,
        )