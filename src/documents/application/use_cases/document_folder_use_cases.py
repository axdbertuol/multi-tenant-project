from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from ...domain.entities.document_folder import DocumentFolder
from ...domain.repositories.document_folder_repository import DocumentFolderRepository
from ...domain.repositories.document_area_repository import DocumentAreaRepository
from ...domain.repositories.user_document_access_repository import UserDocumentAccessRepository
from ...domain.services.document_access_service import DocumentAccessService
from ...application.contracts.iam_contract import IAMContract
from ..dtos.document_folder_dto import (
    DocumentFolderCreateDTO,
    DocumentFolderUpdateDTO,
    DocumentFolderResponseDTO,
    DocumentFolderDetailResponseDTO,
    DocumentFolderListResponseDTO,
    DocumentFolderMoveDTO,
    DocumentFolderStatsDTO,
    DocumentFolderSearchDTO,
    DocumentFolderTreeResponseDTO,
    DocumentFolderAccessCheckDTO,
    DocumentFolderAccessCheckResponseDTO,
    DocumentFolderBulkActionDTO,
    DocumentFolderBulkActionResponseDTO,
)


class DocumentFolderUseCase:
    """Use case for document folder operations."""

    def __init__(
        self,
        document_folder_repository: DocumentFolderRepository,
        document_area_repository: DocumentAreaRepository,
        user_document_access_repository: UserDocumentAccessRepository,
        document_access_service: DocumentAccessService,
        iam_contract: IAMContract,
    ):
        self.document_folder_repository = document_folder_repository
        self.document_area_repository = document_area_repository
        self.user_document_access_repository = user_document_access_repository
        self.document_access_service = document_access_service
        self.iam_contract = iam_contract

    def create_folder(
        self, dto: DocumentFolderCreateDTO, created_by: UUID
    ) -> DocumentFolderResponseDTO:
        """Create a new document folder."""
        # Verify user has permission to create folders
        area = self.document_area_repository.get_by_id(dto.area_id)
        if not area:
            raise ValueError("Document area not found")

        if not self.iam_contract.verify_user_active(created_by, area.organization_id):
            raise ValueError("User is not active in organization")

        # Check if user can create folder in this path
        can_create, reason = self.document_access_service.can_user_create_folder_in_path(
            created_by, dto.parent_path or "/", area.organization_id
        )
        if not can_create:
            raise ValueError(f"Cannot create folder: {reason}")

        # Check if folder already exists
        if self.document_folder_repository.exists_by_path(dto.folder_path, area.organization_id):
            raise ValueError("Folder already exists at this path")

        # Create folder entity
        folder = DocumentFolder.create(
            name=dto.name,
            folder_path=dto.folder_path,
            area_id=dto.area_id,
            organization_id=area.organization_id,
            created_by=created_by,
            parent_path=dto.parent_path,
            description=dto.description,
            extra_data=dto.extra_data,
        )

        # Save folder
        saved_folder = self.document_folder_repository.save(folder)

        return self._build_folder_response(saved_folder)

    def get_folder_by_id(self, folder_id: UUID) -> Optional[DocumentFolderDetailResponseDTO]:
        """Get folder by ID with full details."""
        folder = self.document_folder_repository.get_by_id(folder_id)
        if not folder:
            return None

        return self._build_folder_detail_response(folder)

    def get_folder_by_path(self, folder_path: str, organization_id: UUID) -> Optional[DocumentFolderDetailResponseDTO]:
        """Get folder by path."""
        folder = self.document_folder_repository.get_by_path(folder_path, organization_id)
        if not folder:
            return None

        return self._build_folder_detail_response(folder)

    def update_folder(
        self, folder_id: UUID, dto: DocumentFolderUpdateDTO, updated_by: UUID
    ) -> Optional[DocumentFolderResponseDTO]:
        """Update an existing document folder."""
        folder = self.document_folder_repository.get_by_id(folder_id)
        if not folder:
            return None

        # Verify user has permission to update folders
        if not self.iam_contract.verify_user_active(updated_by, folder.organization_id):
            raise ValueError("User is not active in organization")

        # Check if user can modify this folder
        can_access, reason = self.document_access_service.can_user_access_folder(
            updated_by, folder.folder_path, folder.organization_id, "write"
        )
        if not can_access:
            raise ValueError(f"Cannot update folder: {reason}")

        # Update fields
        updated_folder = folder
        if dto.name is not None:
            updated_folder = updated_folder.update_name(dto.name)

        if dto.description is not None:
            updated_folder = updated_folder.update_description(dto.description)

        if dto.extra_data is not None:
            updated_folder = updated_folder.update_extra_data(dto.extra_data)

        # Save folder
        saved_folder = self.document_folder_repository.save(updated_folder)

        return self._build_folder_response(saved_folder)

    def move_folder(
        self, folder_id: UUID, dto: DocumentFolderMoveDTO, moved_by: UUID
    ) -> Optional[DocumentFolderResponseDTO]:
        """Move a folder to a new path."""
        folder = self.document_folder_repository.get_by_id(folder_id)
        if not folder:
            return None

        # Verify user has permission to move folders
        if not self.iam_contract.verify_user_active(moved_by, folder.organization_id):
            raise ValueError("User is not active in organization")

        # Check if user can move from current location
        can_access_source, reason = self.document_access_service.can_user_access_folder(
            moved_by, folder.folder_path, folder.organization_id, "write"
        )
        if not can_access_source:
            raise ValueError(f"Cannot move folder from current location: {reason}")

        # Check if user can move to new location
        can_access_target, reason = self.document_access_service.can_user_create_folder_in_path(
            moved_by, dto.new_parent_path or "/", folder.organization_id
        )
        if not can_access_target:
            raise ValueError(f"Cannot move folder to new location: {reason}")

        # Check if new path already exists
        if self.document_folder_repository.exists_by_path(dto.new_folder_path, folder.organization_id):
            raise ValueError("Folder already exists at target path")

        # Move folder
        moved_folder = folder.move_to_path(dto.new_folder_path, dto.new_parent_path)
        saved_folder = self.document_folder_repository.save(moved_folder)

        return self._build_folder_response(saved_folder)

    def delete_folder(self, folder_id: UUID, deleted_by: UUID) -> bool:
        """Delete a document folder (soft delete)."""
        folder = self.document_folder_repository.get_by_id(folder_id)
        if not folder:
            return False

        # Verify user has permission to delete folders
        if not self.iam_contract.verify_user_active(deleted_by, folder.organization_id):
            raise ValueError("User is not active in organization")

        # Check if user can delete this folder
        can_access, reason = self.document_access_service.can_user_delete_folder(
            deleted_by, folder.folder_path, folder.organization_id
        )
        if not can_access:
            raise ValueError(f"Cannot delete folder: {reason}")

        # Check if folder has subfolders
        subfolders = self.document_folder_repository.get_by_parent_path(
            folder.folder_path, folder.organization_id
        )
        if subfolders:
            raise ValueError("Cannot delete folder with subfolders")

        # Deactivate folder
        deactivated_folder = folder.deactivate()
        self.document_folder_repository.save(deactivated_folder)

        return True

    def list_folders(
        self,
        organization_id: UUID,
        area_id: Optional[UUID] = None,
        parent_path: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        include_inactive: bool = False,
    ) -> DocumentFolderListResponseDTO:
        """List document folders with pagination."""
        offset = (page - 1) * page_size

        if area_id:
            folders = self.document_folder_repository.get_by_area(area_id)
        elif parent_path:
            folders = self.document_folder_repository.get_by_parent_path(parent_path, organization_id)
        else:
            folders = self.document_folder_repository.get_by_organization(organization_id)

        # Filter by active status
        if not include_inactive:
            folders = [f for f in folders if f.is_active]

        # Apply pagination
        total = len(folders)
        paginated_folders = folders[offset:offset + page_size]

        folder_responses = []
        for folder in paginated_folders:
            folder_responses.append(self._build_folder_response(folder))

        total_pages = (total + page_size - 1) // page_size

        return DocumentFolderListResponseDTO(
            folders=folder_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def search_folders(
        self, dto: DocumentFolderSearchDTO
    ) -> DocumentFolderListResponseDTO:
        """Search document folders."""
        folders = []

        if dto.name_pattern:
            folders.extend(
                self.document_folder_repository.search_by_name(
                    dto.name_pattern, dto.organization_id
                )
            )

        if dto.path_pattern:
            folders.extend(
                self.document_folder_repository.search_by_path(
                    dto.path_pattern, dto.organization_id
                )
            )

        # Remove duplicates
        unique_folders = {folder.id: folder for folder in folders}
        folders = list(unique_folders.values())

        # Filter by area if specified
        if dto.area_id:
            folders = [f for f in folders if f.area_id == dto.area_id]

        # Filter by active status
        if not dto.include_inactive:
            folders = [f for f in folders if f.is_active]

        # Apply pagination
        offset = (dto.page - 1) * dto.page_size
        total = len(folders)
        paginated_folders = folders[offset:offset + dto.page_size]

        folder_responses = []
        for folder in paginated_folders:
            folder_responses.append(self._build_folder_response(folder))

        total_pages = (total + dto.page_size - 1) // dto.page_size

        return DocumentFolderListResponseDTO(
            folders=folder_responses,
            total=total,
            page=dto.page,
            page_size=dto.page_size,
            total_pages=total_pages,
        )

    def get_folder_tree(
        self, organization_id: UUID, area_id: Optional[UUID] = None, root_path: str = "/"
    ) -> List[DocumentFolderTreeResponseDTO]:
        """Get folder hierarchy as tree structure."""
        if area_id:
            folders = self.document_folder_repository.get_by_area(area_id)
        else:
            folders = self.document_folder_repository.get_by_organization(organization_id)

        # Filter active folders only
        folders = [f for f in folders if f.is_active]

        # Get root folders
        root_folders = [f for f in folders if (f.parent_path or "/") == root_path]

        tree_responses = []
        for root_folder in root_folders:
            tree_responses.append(self._build_folder_tree_response(root_folder, folders))

        return tree_responses

    def check_folder_access(
        self, dto: DocumentFolderAccessCheckDTO
    ) -> DocumentFolderAccessCheckResponseDTO:
        """Check if a user has access to a specific folder."""
        can_access, reason = self.document_access_service.can_user_access_folder(
            dto.user_id, dto.folder_path, dto.organization_id, dto.action
        )

        # Get user's accessible folders
        accessible_folders = self.document_access_service.get_user_accessible_folders(
            dto.user_id, dto.organization_id
        )

        # Get highest access level for this folder
        highest_access_level = self.document_access_service.get_highest_access_level_for_folder(
            dto.user_id, dto.folder_path, dto.organization_id
        )

        return DocumentFolderAccessCheckResponseDTO(
            can_access=can_access,
            reason=reason,
            action=dto.action,
            folder_path=dto.folder_path,
            user_id=dto.user_id,
            organization_id=dto.organization_id,
            accessible_folders=accessible_folders,
            highest_access_level=highest_access_level.value if highest_access_level else None,
        )

    def bulk_action(
        self, dto: DocumentFolderBulkActionDTO
    ) -> DocumentFolderBulkActionResponseDTO:
        """Perform bulk action on document folders."""
        success_count = 0
        failure_count = 0
        errors = []
        affected_folders = []

        for folder_id in dto.folder_ids:
            try:
                folder = self.document_folder_repository.get_by_id(folder_id)
                if not folder:
                    failure_count += 1
                    errors.append(f"Folder {folder_id} not found")
                    continue

                # Check user permission
                if dto.action in ["activate", "deactivate", "delete"]:
                    can_access, reason = self.document_access_service.can_user_access_folder(
                        dto.performed_by, folder.folder_path, folder.organization_id, "write"
                    )
                    if not can_access:
                        failure_count += 1
                        errors.append(f"Permission denied for folder {folder_id}: {reason}")
                        continue

                if dto.action == "activate":
                    updated_folder = folder.activate()
                elif dto.action == "deactivate":
                    updated_folder = folder.deactivate()
                elif dto.action == "delete":
                    result = self.document_folder_repository.delete(folder_id)
                    if result:
                        success_count += 1
                        affected_folders.append(folder_id)
                    else:
                        failure_count += 1
                        errors.append(f"Failed to delete folder {folder_id}")
                    continue
                else:
                    failure_count += 1
                    errors.append(f"Unknown action: {dto.action}")
                    continue

                self.document_folder_repository.save(updated_folder)
                success_count += 1
                affected_folders.append(folder_id)

            except Exception as e:
                failure_count += 1
                errors.append(f"Error processing folder {folder_id}: {str(e)}")

        return DocumentFolderBulkActionResponseDTO(
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
            affected_folders=affected_folders,
        )

    def get_folder_stats(self, organization_id: UUID) -> DocumentFolderStatsDTO:
        """Get document folder statistics."""
        all_folders = self.document_folder_repository.get_by_organization(organization_id)

        active_folders = [f for f in all_folders if f.is_active]
        inactive_folders = [f for f in all_folders if not f.is_active]

        # Count by area
        folders_by_area = {}
        for folder in all_folders:
            area = self.document_area_repository.get_by_id(folder.area_id)
            if area:
                area_name = area.name
                if area_name not in folders_by_area:
                    folders_by_area[area_name] = 0
                folders_by_area[area_name] += 1

        # Count by depth level
        folders_by_depth = {}
        for folder in all_folders:
            depth = folder.folder_path.count("/") - 1  # Subtract 1 for root /
            if depth not in folders_by_depth:
                folders_by_depth[depth] = 0
            folders_by_depth[depth] += 1

        # Get recent folders
        recent_folders = sorted(all_folders, key=lambda x: x.created_at, reverse=True)[:10]
        recent_folder_responses = []
        for folder in recent_folders:
            recent_folder_responses.append(self._build_folder_response(folder))

        return DocumentFolderStatsDTO(
            total_folders=len(all_folders),
            active_folders=len(active_folders),
            inactive_folders=len(inactive_folders),
            folders_by_area=folders_by_area,
            folders_by_depth=folders_by_depth,
            recent_folders=recent_folder_responses,
        )

    def _build_folder_response(self, folder: DocumentFolder) -> DocumentFolderResponseDTO:
        """Build folder response DTO."""
        # Get area information
        area = self.document_area_repository.get_by_id(folder.area_id)

        # Count subfolders
        subfolders = self.document_folder_repository.get_by_parent_path(
            folder.folder_path, folder.organization_id
        )
        subfolder_count = len([f for f in subfolders if f.is_active])

        return DocumentFolderResponseDTO(
            id=folder.id,
            name=folder.name,
            folder_path=folder.folder_path,
            parent_path=folder.parent_path,
            area_id=folder.area_id,
            organization_id=folder.organization_id,
            description=folder.description,
            created_at=folder.created_at,
            created_by=folder.created_by,
            is_active=folder.is_active,
            extra_data=folder.extra_data,
            area_name=area.name if area else None,
            subfolder_count=subfolder_count,
        )

    def _build_folder_detail_response(self, folder: DocumentFolder) -> DocumentFolderDetailResponseDTO:
        """Build detailed folder response DTO."""
        folder_response = self._build_folder_response(folder)

        # Get area
        area = self.document_area_repository.get_by_id(folder.area_id)

        # Get subfolders
        subfolders = self.document_folder_repository.get_by_parent_path(
            folder.folder_path, folder.organization_id
        )
        active_subfolders = [f for f in subfolders if f.is_active]
        subfolder_responses = []
        for subfolder in active_subfolders:
            subfolder_responses.append(self._build_folder_response(subfolder))

        # Get parent folder
        parent_folder = None
        if folder.parent_path and folder.parent_path != "/":
            parent = self.document_folder_repository.get_by_path(
                folder.parent_path, folder.organization_id
            )
            if parent:
                parent_folder = self._build_folder_response(parent)

        from ..dtos.document_area_dto import DocumentAreaResponseDTO

        area_dto = None
        if area:
            area_dto = DocumentAreaResponseDTO(
                id=area.id,
                name=area.name,
                description=area.description,
                organization_id=area.organization_id,
                parent_area_id=area.parent_area_id,
                folder_path=area.folder_path,
                created_at=area.created_at,
                created_by=area.created_by,
                is_active=area.is_active,
                is_system_area=area.is_system_area,
            )

        return DocumentFolderDetailResponseDTO(
            **folder_response.model_dump(),
            area=area_dto,
            subfolders=subfolder_responses,
            parent_folder=parent_folder,
        )

    def _build_folder_tree_response(
        self, folder: DocumentFolder, all_folders: List[DocumentFolder]
    ) -> DocumentFolderTreeResponseDTO:
        """Build folder tree response DTO."""
        folder_response = self._build_folder_response(folder)

        # Get children
        children = [f for f in all_folders if f.parent_path == folder.folder_path]
        children_responses = []
        for child in children:
            children_responses.append(self._build_folder_tree_response(child, all_folders))

        return DocumentFolderTreeResponseDTO(
            folder=folder_response,
            children=children_responses,
        )