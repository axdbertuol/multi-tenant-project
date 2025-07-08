from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from ...domain.entities.document_area import DocumentArea
from ...domain.repositories.document_area_repository import DocumentAreaRepository
from ...domain.repositories.document_folder_repository import DocumentFolderRepository
from ...domain.repositories.user_function_area_repository import UserFunctionAreaRepository
from ...domain.services.document_area_service import DocumentAreaService
from ..dtos.document_area_dto import (
    DocumentAreaCreateDTO,
    DocumentAreaUpdateDTO,
    DocumentAreaResponseDTO,
    DocumentAreaDetailResponseDTO,
    DocumentAreaListResponseDTO,
    DocumentAreaMoveDTO,
    DocumentAreaAssignmentDTO,
    DocumentAreaStatsDTO,
    DocumentAreaAccessDTO,
    DocumentAreaAccessResponseDTO,
    DocumentAreaTreeResponseDTO,
    DocumentAreaHierarchyResponseDTO,
)


class DocumentAreaUseCase:
    """Use case for document area operations."""

    def __init__(
        self,
        document_area_repository: DocumentAreaRepository,
        document_folder_repository: DocumentFolderRepository,
        user_function_area_repository: UserFunctionAreaRepository,
        document_area_service: DocumentAreaService,
    ):
        self.document_area_repository = document_area_repository
        self.document_folder_repository = document_folder_repository
        self.user_function_area_repository = user_function_area_repository
        self.document_area_service = document_area_service

    def create_area(self, dto: DocumentAreaCreateDTO) -> DocumentAreaResponseDTO:
        """Create a new document area."""
        # Validate area name is unique in organization
        existing_area = self.document_area_repository.get_by_name_and_organization(
            dto.name, dto.organization_id
        )
        if existing_area:
            raise ValueError(f"Area with name '{dto.name}' already exists")

        # Validate folder path is unique in organization
        existing_folder_area = self.document_area_repository.get_by_folder_path_and_organization(
            dto.folder_path, dto.organization_id
        )
        if existing_folder_area:
            raise ValueError(f"Area with folder path '{dto.folder_path}' already exists")

        # Validate parent area if provided
        if dto.parent_area_id:
            parent_area = self.document_area_repository.get_by_id(dto.parent_area_id)
            if not parent_area:
                raise ValueError("Parent area not found")
            if parent_area.organization_id != dto.organization_id:
                raise ValueError("Parent area must be in the same organization")

        # Create area entity
        area = DocumentArea.create(
            name=dto.name,
            organization_id=dto.organization_id,
            parent_area_id=dto.parent_area_id,
            folder_path=dto.folder_path,
        )

        # Save area
        saved_area = self.document_area_repository.save(area)

        return self._build_area_response(saved_area)

    def get_area_by_id(self, area_id: UUID) -> Optional[DocumentAreaDetailResponseDTO]:
        """Get area by ID with assignments and hierarchy."""
        area = self.document_area_repository.get_by_id(area_id)
        if not area:
            return None

        return self._build_area_detail_response(area)

    def update_area(
        self, area_id: UUID, dto: DocumentAreaUpdateDTO
    ) -> Optional[DocumentAreaResponseDTO]:
        """Update an existing document area."""
        area = self.document_area_repository.get_by_id(area_id)
        if not area:
            return None

        # Check if area is system area
        if area.is_system_area:
            raise ValueError("Cannot update system area")

        # Update fields
        if dto.name is not None:
            # Validate name uniqueness
            existing_area = self.document_area_repository.get_by_name_and_organization(
                dto.name, area.organization_id
            )
            if existing_area and existing_area.id != area.id:
                raise ValueError(f"Area with name '{dto.name}' already exists")
            area.name = dto.name

        if dto.folder_path is not None:
            # Validate folder path uniqueness
            existing_folder_area = self.document_area_repository.get_by_folder_path_and_organization(
                dto.folder_path, area.organization_id
            )
            if existing_folder_area and existing_folder_area.id != area.id:
                raise ValueError(f"Area with folder path '{dto.folder_path}' already exists")
            area.folder_path = dto.folder_path

        if dto.parent_area_id is not None:
            if dto.parent_area_id != area.parent_area_id:
                # Validate parent area
                if dto.parent_area_id:
                    parent_area = self.document_area_repository.get_by_id(dto.parent_area_id)
                    if not parent_area:
                        raise ValueError("Parent area not found")
                    if parent_area.organization_id != area.organization_id:
                        raise ValueError("Parent area must be in the same organization")
                    # Prevent circular reference
                    if self._would_create_circular_reference(area.id, dto.parent_area_id):
                        raise ValueError("Cannot create circular reference in area hierarchy")
                
                area.parent_area_id = dto.parent_area_id

        # Save area
        updated_area = self.document_area_repository.save(area)

        return self._build_area_response(updated_area)

    def delete_area(self, area_id: UUID) -> bool:
        """Delete a document area (soft delete)."""
        area = self.document_area_repository.get_by_id(area_id)
        if not area:
            return False

        # Check if area is system area
        if area.is_system_area:
            raise ValueError("Cannot delete system area")

        # Check if area has assignments
        assignments = self.user_function_area_repository.get_by_area(area_id)
        if assignments:
            raise ValueError("Cannot delete area with active assignments")

        # Check if area has children
        children = self.document_area_repository.get_by_parent_area(area_id)
        if children:
            raise ValueError("Cannot delete area with child areas")

        area.is_active = False
        self.document_area_repository.save(area)

        return True

    def move_area(
        self, area_id: UUID, dto: DocumentAreaMoveDTO
    ) -> Optional[DocumentAreaResponseDTO]:
        """Move an area to a new parent."""
        area = self.document_area_repository.get_by_id(area_id)
        if not area:
            return None

        # Check if area is system area
        if area.is_system_area:
            raise ValueError("Cannot move system area")

        # Validate new parent if provided
        if dto.new_parent_id:
            parent_area = self.document_area_repository.get_by_id(dto.new_parent_id)
            if not parent_area:
                raise ValueError("New parent area not found")
            if parent_area.organization_id != area.organization_id:
                raise ValueError("New parent area must be in the same organization")
            # Prevent circular reference
            if self._would_create_circular_reference(area_id, dto.new_parent_id):
                raise ValueError("Cannot create circular reference in area hierarchy")

        # Update parent
        area.parent_area_id = dto.new_parent_id
        updated_area = self.document_area_repository.save(area)

        return self._build_area_response(updated_area)

    def list_areas(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_system: bool = True,
    ) -> DocumentAreaListResponseDTO:
        """List document areas with pagination."""
        offset = (page - 1) * page_size

        if include_system:
            areas = self.document_area_repository.get_by_organization(organization_id)
        else:
            areas = self.document_area_repository.get_active_by_organization(organization_id)
            areas = [a for a in areas if not a.is_system_area]

        # Apply pagination
        total = len(areas)
        paginated_areas = areas[offset:offset + page_size]

        area_responses = []
        for area in paginated_areas:
            area_responses.append(self._build_area_response(area))

        total_pages = (total + page_size - 1) // page_size

        return DocumentAreaListResponseDTO(
            areas=area_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_area_hierarchy(
        self, organization_id: UUID
    ) -> DocumentAreaHierarchyResponseDTO:
        """Get area hierarchy for an organization."""
        areas = self.document_area_repository.get_active_by_organization(organization_id)
        
        # Build hierarchy tree
        hierarchy_tree = self._build_hierarchy_tree(areas)
        
        # Validate hierarchy
        validation_errors = self._validate_area_hierarchy(areas)

        area_responses = []
        for area in areas:
            area_responses.append(self._build_area_response(area))

        return DocumentAreaHierarchyResponseDTO(
            areas=area_responses,
            hierarchy_tree=hierarchy_tree,
            validation_errors=validation_errors,
        )

    def get_area_tree(self, organization_id: UUID) -> List[DocumentAreaTreeResponseDTO]:
        """Get area hierarchy as tree structure."""
        areas = self.document_area_repository.get_active_by_organization(organization_id)
        
        # Get root areas
        root_areas = [area for area in areas if area.parent_area_id is None]
        
        tree_responses = []
        for root_area in root_areas:
            tree_responses.append(self._build_area_tree_response(root_area, areas))

        return tree_responses

    def check_area_access(
        self, dto: DocumentAreaAccessDTO
    ) -> DocumentAreaAccessResponseDTO:
        """Check if a user has access to a specific folder through areas."""
        # Get user's areas
        user_assignments = self.user_function_area_repository.get_active_by_user(dto.user_id)
        user_area_ids = [assignment.area_id for assignment in user_assignments 
                        if assignment.organization_id == dto.organization_id]

        if not user_area_ids:
            return DocumentAreaAccessResponseDTO(
                has_access=False,
                accessible_areas=[],
                access_reason="User has no area assignments",
                accessible_paths=[],
            )

        # Get user's areas
        user_areas = []
        for area_id in user_area_ids:
            area = self.document_area_repository.get_by_id(area_id)
            if area and area.is_active:
                user_areas.append(area)

        # Check access using service
        has_access = self.document_area_service.can_access_folder(
            dto.folder_path, user_areas
        )

        # Get accessible paths
        accessible_paths = []
        for area in user_areas:
            paths = self.document_area_service.get_accessible_folders(area)
            accessible_paths.extend(paths)

        # Remove duplicates and sort
        accessible_paths = sorted(list(set(accessible_paths)))

        area_responses = []
        for area in user_areas:
            area_responses.append(self._build_area_response(area))

        access_reason = "Access granted through area permissions" if has_access else "No matching area permissions"

        return DocumentAreaAccessResponseDTO(
            has_access=has_access,
            accessible_areas=area_responses,
            access_reason=access_reason,
            accessible_paths=accessible_paths,
        )

    def get_area_stats(self, organization_id: UUID) -> DocumentAreaStatsDTO:
        """Get document area statistics."""
        all_areas = self.document_area_repository.get_by_organization(organization_id)
        
        active_areas = [a for a in all_areas if a.is_active]
        root_areas = [a for a in all_areas if a.parent_area_id is None]
        system_areas = [a for a in all_areas if a.is_system_area]
        custom_areas = [a for a in all_areas if not a.is_system_area]

        # Count assignments
        total_assignments = 0
        for area in all_areas:
            assignments = self.user_function_area_repository.get_by_area(area.id)
            total_assignments += len(assignments)

        # Count areas by level
        areas_by_level = {}
        for area in all_areas:
            level = self._calculate_area_level(area, all_areas)
            if level not in areas_by_level:
                areas_by_level[level] = 0
            areas_by_level[level] += 1

        # Count folder coverage
        folder_coverage = {}
        for area in all_areas:
            folder_path = area.folder_path
            if folder_path not in folder_coverage:
                folder_coverage[folder_path] = 0
            folder_coverage[folder_path] += 1

        return DocumentAreaStatsDTO(
            total_areas=len(all_areas),
            active_areas=len(active_areas),
            root_areas=len(root_areas),
            system_areas=len(system_areas),
            custom_areas=len(custom_areas),
            total_assignments=total_assignments,
            areas_by_level=areas_by_level,
            folder_coverage=folder_coverage,
        )

    def create_default_areas(self, organization_id: UUID) -> List[DocumentAreaResponseDTO]:
        """Create default document areas for an organization."""
        default_areas = self.document_area_service.create_default_areas(organization_id)
        
        created_areas = []
        for area in default_areas:
            saved_area = self.document_area_repository.save(area)
            created_areas.append(self._build_area_response(saved_area))

        return created_areas

    def _build_area_response(self, area: DocumentArea) -> DocumentAreaResponseDTO:
        """Build area response DTO."""
        # Count assignments
        assignments = self.user_function_area_repository.get_by_area(area.id)
        assignment_count = len(assignments)

        # Count subfolders
        folders = self.document_folder_repository.get_by_area(area.id)
        subfolder_count = len(folders)

        # Check if has children
        children = self.document_area_repository.get_by_parent_area(area.id)
        has_children = len(children) > 0

        # Calculate hierarchy level
        all_areas = self.document_area_repository.get_by_organization(area.organization_id)
        hierarchy_level = self._calculate_area_level(area, all_areas)

        return DocumentAreaResponseDTO(
            id=area.id,
            name=area.name,
            organization_id=area.organization_id,
            parent_area_id=area.parent_area_id,
            folder_path=area.folder_path,
            created_at=area.created_at,
            is_active=area.is_active,
            is_system_area=area.is_system_area,
            assignment_count=assignment_count,
            subfolder_count=subfolder_count,
            has_children=has_children,
            hierarchy_level=hierarchy_level,
        )

    def _build_area_detail_response(self, area: DocumentArea) -> DocumentAreaDetailResponseDTO:
        """Build detailed area response DTO."""
        area_response = self._build_area_response(area)

        # Get assignments
        assignments = self.user_function_area_repository.get_by_area(area.id)
        
        # Get children
        children = self.document_area_repository.get_by_parent_area(area.id)
        children_responses = []
        for child in children:
            children_responses.append(self._build_area_response(child))

        # Get accessible folders
        accessible_folders = self.document_area_service.get_accessible_folders(area)

        # Get parent area
        parent_area = None
        if area.parent_area_id:
            parent = self.document_area_repository.get_by_id(area.parent_area_id)
            if parent:
                parent_area = self._build_area_response(parent)

        from ..dtos.user_function_area_dto import UserFunctionAreaResponseDTO
        
        assignment_responses = []
        for assignment in assignments:
            assignment_responses.append(
                UserFunctionAreaResponseDTO(
                    id=assignment.id,
                    user_id=assignment.user_id,
                    organization_id=assignment.organization_id,
                    function_id=assignment.function_id,
                    area_id=assignment.area_id,
                    assigned_by=assignment.assigned_by,
                    assigned_at=assignment.assigned_at,
                    is_active=assignment.is_active,
                )
            )

        return DocumentAreaDetailResponseDTO(
            **area_response.model_dump(),
            assignments=assignment_responses,
            children=children_responses,
            accessible_folders=accessible_folders,
            parent_area=parent_area,
        )

    def _build_area_tree_response(
        self, area: DocumentArea, all_areas: List[DocumentArea]
    ) -> DocumentAreaTreeResponseDTO:
        """Build area tree response DTO."""
        area_response = self._build_area_response(area)
        
        # Get children
        children = [a for a in all_areas if a.parent_area_id == area.id]
        children_responses = []
        for child in children:
            children_responses.append(self._build_area_tree_response(child, all_areas))

        # Get accessible paths
        accessible_paths = self.document_area_service.get_accessible_folders(area)

        return DocumentAreaTreeResponseDTO(
            area=area_response,
            children=children_responses,
            accessible_paths=accessible_paths,
        )

    def _would_create_circular_reference(self, area_id: UUID, new_parent_id: UUID) -> bool:
        """Check if setting a new parent would create a circular reference."""
        current_id = new_parent_id
        visited = set()
        
        while current_id and current_id not in visited:
            if current_id == area_id:
                return True
            visited.add(current_id)
            
            parent_area = self.document_area_repository.get_by_id(current_id)
            if not parent_area:
                break
            current_id = parent_area.parent_area_id
        
        return False

    def _calculate_area_level(self, area: DocumentArea, all_areas: List[DocumentArea]) -> int:
        """Calculate the hierarchy level of an area."""
        if not area.parent_area_id:
            return 0
        
        level = 0
        current_id = area.parent_area_id
        visited = set()
        
        while current_id and current_id not in visited:
            level += 1
            visited.add(current_id)
            
            parent_area = next((a for a in all_areas if a.id == current_id), None)
            if not parent_area:
                break
            current_id = parent_area.parent_area_id
        
        return level

    def _build_hierarchy_tree(self, areas: List[DocumentArea]) -> dict:
        """Build hierarchy tree structure."""
        tree = {}
        
        # Group areas by parent
        areas_by_parent = {}
        for area in areas:
            parent_id = area.parent_area_id or "root"
            if parent_id not in areas_by_parent:
                areas_by_parent[parent_id] = []
            areas_by_parent[parent_id].append(area)
        
        # Build tree structure
        def build_subtree(parent_id):
            if parent_id not in areas_by_parent:
                return []
            
            subtree = []
            for area in areas_by_parent[parent_id]:
                area_data = {
                    "id": str(area.id),
                    "name": area.name,
                    "folder_path": area.folder_path,
                    "children": build_subtree(area.id)
                }
                subtree.append(area_data)
            return subtree
        
        tree["root"] = build_subtree("root")
        return tree

    def _validate_area_hierarchy(self, areas: List[DocumentArea]) -> List[str]:
        """Validate area hierarchy for issues."""
        errors = []
        
        # Check for circular references
        for area in areas:
            if self._has_circular_reference(area, areas):
                errors.append(f"Circular reference detected for area: {area.name}")
        
        # Check for orphaned areas
        area_ids = {area.id for area in areas}
        for area in areas:
            if area.parent_area_id and area.parent_area_id not in area_ids:
                errors.append(f"Orphaned area detected: {area.name} references non-existent parent")
        
        return errors

    def _has_circular_reference(self, area: DocumentArea, all_areas: List[DocumentArea]) -> bool:
        """Check if an area has a circular reference."""
        if not area.parent_area_id:
            return False
        
        visited = set()
        current_id = area.parent_area_id
        
        while current_id and current_id not in visited:
            if current_id == area.id:
                return True
            visited.add(current_id)
            
            parent_area = next((a for a in all_areas if a.id == current_id), None)
            if not parent_area:
                break
            current_id = parent_area.parent_area_id
        
        return False