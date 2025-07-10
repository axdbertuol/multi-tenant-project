from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import delete, select, func, and_, or_
from sqlalchemy.orm import Session
from ...domain.entities.document_folder import DocumentFolder
from ...domain.repositories.document_folder_repository import DocumentFolderRepository
from ..database.models import DocumentFolderModel, document_folder_allowed_areas


class SqlAlchemyDocumentFolderRepository(DocumentFolderRepository):
    """SQLAlchemy implementation of DocumentFolderRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, folder: DocumentFolder) -> DocumentFolder:
        """Save a document folder entity."""
        # Check if folder exists
        existing = self.session.get(DocumentFolderModel, folder.id)

        if existing:
            # Update existing folder
            existing.name = folder.name
            existing.path = folder.path
            existing.area_id = folder.area_id
            existing.organization_id = folder.organization_id
            existing.parent_folder_id = folder.parent_folder_id
            existing.created_by = folder.created_by
            existing.is_active = folder.is_active
            existing.is_virtual = folder.is_virtual
            existing.extra_data = folder.extra_data
            existing.updated_at = datetime.now(timezone.utc)

            # Update allowed areas
            self._update_allowed_areas(existing, folder.allowed_areas)

            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # Create new folder
            folder_model = DocumentFolderModel(
                id=folder.id,
                name=folder.name,
                path=folder.path,
                area_id=folder.area_id,
                organization_id=folder.organization_id,
                parent_folder_id=folder.parent_folder_id,
                created_by=folder.created_by,
                is_active=folder.is_active,
                is_virtual=folder.is_virtual,
                extra_data=folder.extra_data,
                created_at=folder.created_at,
                updated_at=folder.updated_at,
            )

            self.session.add(folder_model)
            self.session.flush()

            # Add allowed areas
            self._update_allowed_areas(folder_model, folder.allowed_areas)

            return self._to_domain_entity(folder_model)

    def _update_allowed_areas(self, folder_model: DocumentFolderModel, allowed_areas: List[UUID]):
        """Update allowed areas for a folder."""
        # Remove existing associations
        self.session.execute(
            delete(document_folder_allowed_areas).where(
                document_folder_allowed_areas.c.folder_id == folder_model.id
            )
        )

        # Add new associations
        for area_id in allowed_areas:
            self.session.execute(
                document_folder_allowed_areas.insert().values(
                    folder_id=folder_model.id,
                    area_id=area_id
                )
            )

    def get_by_id(self, folder_id: UUID) -> Optional[DocumentFolder]:
        """Get folder by ID."""
        result = self.session.execute(
            select(DocumentFolderModel).where(DocumentFolderModel.id == folder_id)
        )
        folder_model = result.scalar_one_or_none()

        if folder_model:
            return self._to_domain_entity(folder_model)
        return None

    def get_by_path(self, path: str, organization_id: UUID) -> Optional[DocumentFolder]:
        """Get folder by path within organization."""
        result = self.session.execute(
            select(DocumentFolderModel).where(
                and_(
                    DocumentFolderModel.path == path,
                    DocumentFolderModel.organization_id == organization_id,
                )
            )
        )
        folder_model = result.scalar_one_or_none()

        if folder_model:
            return self._to_domain_entity(folder_model)
        return None

    def get_by_area(self, area_id: UUID) -> List[DocumentFolder]:
        """Get all folders for an area."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .where(DocumentFolderModel.area_id == area_id)
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def get_by_organization(self, organization_id: UUID) -> List[DocumentFolder]:
        """Get all folders for an organization."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .where(DocumentFolderModel.organization_id == organization_id)
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def get_active_by_organization(self, organization_id: UUID) -> List[DocumentFolder]:
        """Get active folders for an organization."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .where(
                and_(
                    DocumentFolderModel.organization_id == organization_id,
                    DocumentFolderModel.is_active == True,
                )
            )
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def get_root_folders(self, organization_id: UUID) -> List[DocumentFolder]:
        """Get root folders (without parent) for an organization."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .where(
                and_(
                    DocumentFolderModel.organization_id == organization_id,
                    DocumentFolderModel.parent_folder_id.is_(None),
                    DocumentFolderModel.is_active == True,
                )
            )
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def get_child_folders(self, parent_folder_id: UUID) -> List[DocumentFolder]:
        """Get child folders of a parent folder."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .where(
                and_(
                    DocumentFolderModel.parent_folder_id == parent_folder_id,
                    DocumentFolderModel.is_active == True,
                )
            )
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def get_folders_by_path_prefix(self, path_prefix: str, organization_id: UUID) -> List[DocumentFolder]:
        """Get folders by path prefix."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .where(
                and_(
                    DocumentFolderModel.path.startswith(path_prefix),
                    DocumentFolderModel.organization_id == organization_id,
                    DocumentFolderModel.is_active == True,
                )
            )
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def get_folders_accessible_by_area(self, area_id: UUID, organization_id: UUID) -> List[DocumentFolder]:
        """Get folders accessible by a specific area."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .join(
                document_folder_allowed_areas,
                DocumentFolderModel.id == document_folder_allowed_areas.c.folder_id
            )
            .where(
                and_(
                    document_folder_allowed_areas.c.area_id == area_id,
                    DocumentFolderModel.organization_id == organization_id,
                    DocumentFolderModel.is_active == True,
                )
            )
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def get_virtual_folders(self, organization_id: UUID) -> List[DocumentFolder]:
        """Get virtual folders for an organization."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .where(
                and_(
                    DocumentFolderModel.organization_id == organization_id,
                    DocumentFolderModel.is_virtual == True,
                    DocumentFolderModel.is_active == True,
                )
            )
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def get_physical_folders(self, organization_id: UUID) -> List[DocumentFolder]:
        """Get physical folders for an organization."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .where(
                and_(
                    DocumentFolderModel.organization_id == organization_id,
                    DocumentFolderModel.is_virtual == False,
                    DocumentFolderModel.is_active == True,
                )
            )
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def get_hierarchy_for_folder(self, folder_id: UUID) -> List[DocumentFolder]:
        """Get complete hierarchy for a folder."""
        folder = self.get_by_id(folder_id)
        if not folder:
            return []

        all_folders = self.get_by_organization(folder.organization_id)
        
        hierarchy = []
        folder_map = {f.id: f for f in all_folders}
        
        # Add the folder itself
        hierarchy.append(folder)
        
        # Add all ancestors
        current = folder
        while current.parent_folder_id:
            parent = folder_map.get(current.parent_folder_id)
            if parent:
                hierarchy.append(parent)
                current = parent
            else:
                break
        
        # Add all descendants
        def add_descendants(parent_id: UUID):
            for child_folder in all_folders:
                if child_folder.parent_folder_id == parent_id:
                    if child_folder not in hierarchy:
                        hierarchy.append(child_folder)
                        add_descendants(child_folder.id)
        
        add_descendants(folder.id)
        
        return hierarchy

    def find_by_name_pattern(self, pattern: str, organization_id: UUID) -> List[DocumentFolder]:
        """Find folders by name pattern."""
        result = self.session.execute(
            select(DocumentFolderModel)
            .where(
                and_(
                    DocumentFolderModel.name.ilike(f"%{pattern}%"),
                    DocumentFolderModel.organization_id == organization_id,
                    DocumentFolderModel.is_active == True,
                )
            )
            .order_by(DocumentFolderModel.path)
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def exists_by_path(self, path: str, organization_id: UUID) -> bool:
        """Check if folder with path exists in organization."""
        result = self.session.execute(
            select(DocumentFolderModel.id).where(
                and_(
                    DocumentFolderModel.path == path,
                    DocumentFolderModel.organization_id == organization_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    def count_by_area(self, area_id: UUID) -> int:
        """Count folders for an area."""
        result = self.session.execute(
            select(func.count(DocumentFolderModel.id)).where(
                DocumentFolderModel.area_id == area_id
            )
        )
        return result.scalar()

    def count_by_organization(self, organization_id: UUID) -> int:
        """Count folders in organization."""
        result = self.session.execute(
            select(func.count(DocumentFolderModel.id)).where(
                DocumentFolderModel.organization_id == organization_id
            )
        )
        return result.scalar()

    def get_recently_created(self, organization_id: UUID, days: int = 30) -> List[DocumentFolder]:
        """Get folders created within the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = self.session.execute(
            select(DocumentFolderModel)
            .where(
                and_(
                    DocumentFolderModel.organization_id == organization_id,
                    DocumentFolderModel.created_at >= cutoff_date,
                )
            )
            .order_by(DocumentFolderModel.created_at.desc())
        )
        folder_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in folder_models]

    def delete(self, folder_id: UUID) -> bool:
        """Delete a folder."""
        # First remove allowed areas associations
        self.session.execute(
            delete(document_folder_allowed_areas).where(
                document_folder_allowed_areas.c.folder_id == folder_id
            )
        )
        
        # Then delete the folder
        result = self.session.execute(
            delete(DocumentFolderModel).where(DocumentFolderModel.id == folder_id)
        )
        return result.rowcount > 0

    def _to_domain_entity(self, folder_model: DocumentFolderModel) -> DocumentFolder:
        """Convert SQLAlchemy model to domain entity."""
        # Get allowed areas
        allowed_areas_result = self.session.execute(
            select(document_folder_allowed_areas.c.area_id).where(
                document_folder_allowed_areas.c.folder_id == folder_model.id
            )
        )
        allowed_areas = [row[0] for row in allowed_areas_result.fetchall()]

        return DocumentFolder(
            id=folder_model.id,
            name=folder_model.name,
            path=folder_model.path,
            area_id=folder_model.area_id,
            organization_id=folder_model.organization_id,
            parent_folder_id=folder_model.parent_folder_id,
            allowed_areas=allowed_areas,
            created_at=folder_model.created_at,
            updated_at=folder_model.updated_at,
            created_by=folder_model.created_by,
            is_active=folder_model.is_active,
            is_virtual=folder_model.is_virtual,
            extra_data=folder_model.extra_data,
        )