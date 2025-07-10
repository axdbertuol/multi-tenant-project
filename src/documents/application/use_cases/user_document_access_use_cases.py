from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from ...domain.entities.user_document_access import UserDocumentAccess
from ...domain.repositories.user_document_access_repository import UserDocumentAccessRepository
from ...domain.repositories.document_area_repository import DocumentAreaRepository
from ...domain.services.document_area_service import DocumentAreaService
from ...application.contracts.iam_contract import IAMContract
from ..dtos.user_document_access_dto import (
    UserDocumentAccessCreateDTO,
    UserDocumentAccessUpdateDTO,
    UserDocumentAccessResponseDTO,
    UserDocumentAccessDetailResponseDTO,
    UserDocumentAccessListResponseDTO,
    UserDocumentAccessBatchCreateDTO,
    UserDocumentAccessBatchUpdateDTO,
    UserDocumentAccessTransferDTO,
    UserDocumentAccessStatsDTO,
    UserDocumentAccessFilterDTO,
    UserDocumentAccessSearchDTO,
    UserDocumentAccessBulkActionDTO,
    UserDocumentAccessBulkActionResponseDTO,
    UserDocumentAccessRevokeDTO,
    UserDocumentAccessExtendDTO,
    UserDocumentAccessAuditDTO,
    UserInfoDTO,
)


class UserDocumentAccessUseCase:
    """Use case for user document access operations."""

    def __init__(
        self,
        user_document_access_repository: UserDocumentAccessRepository,
        document_area_repository: DocumentAreaRepository,
        document_area_service: DocumentAreaService,
        iam_contract: IAMContract,
    ):
        self.user_document_access_repository = user_document_access_repository
        self.document_area_repository = document_area_repository
        self.document_area_service = document_area_service
        self.iam_contract = iam_contract

    def create_access(
        self, dto: UserDocumentAccessCreateDTO
    ) -> UserDocumentAccessResponseDTO:
        """Create a new user document access."""
        # Verify user exists and is active
        user_info = self.iam_contract.get_user_info(dto.user_id)
        if not user_info:
            raise ValueError("User not found")

        if not self.iam_contract.verify_user_active(dto.user_id, dto.organization_id):
            raise ValueError("User is not active in organization")

        # Verify area exists
        area = self.document_area_repository.get_by_id(dto.area_id)
        if not area:
            raise ValueError("Document area not found")

        if not area.is_active:
            raise ValueError("Cannot assign inactive area")

        # Verify assigned_by user has permission
        if not self.iam_contract.verify_management_permission(
            dto.assigned_by, dto.organization_id, "management:assign_area"
        ):
            raise ValueError("User lacks permission to assign areas")

        # Check if user already has access to this area
        existing_access = self.user_document_access_repository.get_by_user_and_area(
            dto.user_id, dto.area_id
        )
        if existing_access and existing_access.is_active:
            raise ValueError("User already has active access to this area")

        # Create access entity
        access = UserDocumentAccess.create(
            user_id=dto.user_id,
            area_id=dto.area_id,
            organization_id=dto.organization_id,
            access_level=dto.access_level,
            granted_by=dto.granted_by,
            expires_at=dto.expires_at,
            notes=dto.notes,
            extra_data=dto.extra_data,
        )

        # Save access
        saved_access = self.user_document_access_repository.save(access)

        return self._build_access_response(saved_access)

    def get_access_by_id(self, access_id: UUID) -> Optional[UserDocumentAccessDetailResponseDTO]:
        """Get access by ID with full details."""
        access = self.user_document_access_repository.get_by_id(access_id)
        if not access:
            return None

        return self._build_access_detail_response(access)

    def update_access(
        self, access_id: UUID, dto: UserDocumentAccessUpdateDTO
    ) -> Optional[UserDocumentAccessResponseDTO]:
        """Update an existing user document access."""
        access = self.user_document_access_repository.get_by_id(access_id)
        if not access:
            return None

        # Update fields
        updated_access = access
        if dto.area_id is not None:
            # Validate area exists and belongs to same organization
            area = self.document_area_repository.get_by_id(dto.area_id)
            if not area:
                raise ValueError("Document area not found")
            if area.organization_id != access.organization_id:
                raise ValueError("Area must belong to the same organization")
            # Create new access with different area
            updated_access = UserDocumentAccess.create(
                user_id=access.user_id,
                area_id=dto.area_id,
                organization_id=access.organization_id,
                access_level=access.access_level,
                granted_by=access.granted_by,
                expires_at=access.expires_at,
                notes=access.notes,
                extra_data=access.extra_data,
            )

        if dto.expires_at is not None:
            updated_access = updated_access.extend_access(dto.expires_at)

        if dto.is_active is not None:
            if dto.is_active:
                updated_access = updated_access.activate()
            else:
                updated_access = updated_access.deactivate()

        if dto.extra_data is not None:
            updated_access = updated_access.update_extra_data(dto.extra_data)

        # Save access
        saved_access = self.user_document_access_repository.save(updated_access)

        return self._build_access_response(saved_access)

    def delete_access(self, access_id: UUID) -> bool:
        """Delete a user document access."""
        access = self.user_document_access_repository.get_by_id(access_id)
        if not access:
            return False

        return self.user_document_access_repository.delete(access_id)

    def revoke_access(self, dto: UserDocumentAccessRevokeDTO) -> bool:
        """Revoke user document access."""
        # Verify user has permission to revoke
        if not self.iam_contract.verify_management_permission(
            dto.revoked_by, dto.organization_id, "management:revoke_area"
        ):
            raise ValueError("User lacks permission to revoke document access")

        # Get current access
        user_accesses = self.user_document_access_repository.get_active_by_user(dto.user_id)
        access = next(
            (a for a in user_accesses if a.organization_id == dto.organization_id),
            None
        )
        
        if not access:
            return False

        # Revoke access
        revoked_access = access.revoke(dto.revoked_by, dto.reason)

        self.user_document_access_repository.save(revoked_access)
        return True

    def extend_access(
        self, access_id: UUID, dto: UserDocumentAccessExtendDTO
    ) -> Optional[UserDocumentAccessResponseDTO]:
        """Extend user document access expiration."""
        access = self.user_document_access_repository.get_by_id(access_id)
        if not access:
            return None

        # Verify user has permission to extend
        if not self.iam_contract.verify_management_permission(
            dto.extended_by, access.organization_id, "management:extend_area"
        ):
            raise ValueError("User lacks permission to extend document access")

        # Update expiration
        extended_access = access.extend_access(dto.new_expires_at)

        # Add extension reason to extra_data
        if dto.reason:
            extra_data = extended_access.extra_data.copy()
            extra_data["extension_reason"] = dto.reason
            extra_data["extended_at"] = datetime.now(timezone.utc).isoformat()
            extra_data["extended_by"] = str(dto.extended_by)
            extended_access = extended_access.update_extra_data(extra_data)

        saved_access = self.user_document_access_repository.save(extended_access)
        return self._build_access_response(saved_access)

    def batch_create_accesses(
        self, dto: UserDocumentAccessBatchCreateDTO
    ) -> List[UserDocumentAccessResponseDTO]:
        """Create multiple user document accesses."""
        created_accesses = []
        
        for access_dto in dto.accesses:
            try:
                access = self.create_access(access_dto)
                created_accesses.append(access)
            except ValueError as e:
                # Log error but continue with other accesses
                continue

        return created_accesses

    def transfer_accesses(
        self, dto: UserDocumentAccessTransferDTO
    ) -> List[UserDocumentAccessResponseDTO]:
        """Transfer user accesses from one area to another."""
        # Verify user has permission to transfer
        # Get organization from source area
        source_area = self.document_area_repository.get_by_id(dto.source_area_id)
        if not source_area:
            raise ValueError("Source area not found")

        if not self.iam_contract.verify_management_permission(
            dto.transferred_by, source_area.organization_id, "management:transfer_area"
        ):
            raise ValueError("User lacks permission to transfer document access")

        # Verify target area exists
        target_area = self.document_area_repository.get_by_id(dto.target_area_id)
        if not target_area:
            raise ValueError("Target area not found")

        if target_area.organization_id != source_area.organization_id:
            raise ValueError("Target area must be in the same organization")

        transferred_accesses = []
        
        for user_id in dto.user_ids:
            # Get current access for this specific area
            current_access = self.user_document_access_repository.get_by_user_and_area(
                user_id, dto.source_area_id
            )
            
            if not current_access or not current_access.is_active:
                continue
            
            # Create new access for target area and revoke old one
            try:
                # Create new access
                new_access = UserDocumentAccess.create(
                    user_id=user_id,
                    area_id=dto.target_area_id,
                    organization_id=source_area.organization_id,
                    access_level=current_access.access_level,
                    granted_by=dto.transferred_by,
                    expires_at=current_access.expires_at,
                    notes=f"Transferred from area {source_area.name}",
                    extra_data=current_access.extra_data,
                )
                
                # Revoke old access
                revoked_access = current_access.revoke(
                    dto.transferred_by,
                    f"Transferred to area {target_area.name}"
                )
                
                # Save both
                self.user_document_access_repository.save(revoked_access)
                saved_access = self.user_document_access_repository.save(new_access)
                transferred_accesses.append(self._build_access_response(saved_access))
            except ValueError as e:
                # Log error but continue
                continue

        return transferred_accesses

    def list_accesses(
        self,
        filters: Optional[UserDocumentAccessFilterDTO] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UserDocumentAccessListResponseDTO:
        """List user document accesses with filtering and pagination."""
        # Apply filters
        if filters:
            if filters.user_id and filters.organization_id:
                user_accesses = self.user_document_access_repository.get_by_user(filters.user_id)
                accesses = [a for a in user_accesses if a.organization_id == filters.organization_id]
            elif filters.user_id:
                accesses = self.user_document_access_repository.get_by_user(filters.user_id)
            elif filters.organization_id:
                accesses = self.user_document_access_repository.get_by_organization(filters.organization_id)
            elif filters.area_id:
                accesses = self.user_document_access_repository.get_by_area(filters.area_id)
            else:
                accesses = []
        else:
            accesses = []

        # Apply additional filters
        if filters and accesses:
            if filters.is_active is not None:
                accesses = [a for a in accesses if a.is_active == filters.is_active]
            if filters.is_expired is not None:
                if filters.is_expired:
                    accesses = [a for a in accesses if a.is_expired()]
                else:
                    accesses = [a for a in accesses if not a.is_expired()]
            if filters.granted_by:
                accesses = [a for a in accesses if a.granted_by == filters.granted_by]

        # Apply pagination
        total = len(accesses)
        offset = (page - 1) * page_size
        paginated_accesses = accesses[offset:offset + page_size]

        access_responses = []
        for access in paginated_accesses:
            access_responses.append(self._build_access_response(access))

        total_pages = (total + page_size - 1) // page_size

        return UserDocumentAccessListResponseDTO(
            accesses=access_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def bulk_action(
        self, dto: UserDocumentAccessBulkActionDTO
    ) -> UserDocumentAccessBulkActionResponseDTO:
        """Perform bulk action on user document accesses."""
        # Verify user has permission for bulk actions
        success_count = 0
        failure_count = 0
        errors = []
        affected_accesses = []

        for access_id in dto.access_ids:
            try:
                access = self.user_document_access_repository.get_by_id(access_id)
                if not access:
                    failure_count += 1
                    errors.append(f"Access {access_id} not found")
                    continue

                # Verify permission for this organization
                if not self.iam_contract.verify_management_permission(
                    dto.performed_by, access.organization_id, f"management:{dto.action}_area"
                ):
                    failure_count += 1
                    errors.append(f"Permission denied for access {access_id}")
                    continue

                if dto.action == "activate":
                    updated_access = access.activate()
                elif dto.action == "deactivate":
                    updated_access = access.deactivate()
                elif dto.action == "delete":
                    result = self.user_document_access_repository.delete(access_id)
                    if result:
                        success_count += 1
                        affected_accesses.append(access_id)
                    else:
                        failure_count += 1
                        errors.append(f"Failed to delete access {access_id}")
                    continue
                elif dto.action == "extend":
                    if dto.new_expires_at:
                        updated_access = access.extend_access(dto.new_expires_at)
                    else:
                        updated_access = access.extend_access(None)
                else:
                    failure_count += 1
                    errors.append(f"Unknown action: {dto.action}")
                    continue

                self.user_document_access_repository.save(updated_access)
                success_count += 1
                affected_accesses.append(access_id)
                    
            except Exception as e:
                failure_count += 1
                errors.append(f"Error processing access {access_id}: {str(e)}")

        return UserDocumentAccessBulkActionResponseDTO(
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
            affected_accesses=affected_accesses,
        )

    def get_access_stats(
        self, organization_id: Optional[UUID] = None
    ) -> UserDocumentAccessStatsDTO:
        """Get user document access statistics."""
        if organization_id:
            accesses = self.user_document_access_repository.get_by_organization(organization_id)
        else:
            accesses = []

        active_accesses = [a for a in accesses if a.is_active]
        expired_accesses = [a for a in accesses if a.is_expired()]
        expiring_soon_accesses = [a for a in accesses if a.is_expiring_soon()]

        # Count by area
        accesses_by_area = {}
        for access in accesses:
            area = self.document_area_repository.get_by_id(access.area_id)
            if area:
                area_name = area.name
                if area_name not in accesses_by_area:
                    accesses_by_area[area_name] = 0
                accesses_by_area[area_name] += 1

        # Count by user
        accesses_by_user = {}
        for access in accesses:
            user = self.iam_contract.get_user_info(access.user_id)
            if user:
                user_email = user.email
                if user_email not in accesses_by_user:
                    accesses_by_user[user_email] = 0
                accesses_by_user[user_email] += 1

        # Get recent accesses
        recent_accesses = sorted(accesses, key=lambda x: x.granted_at, reverse=True)[:10]
        recent_access_responses = []
        for access in recent_accesses:
            recent_access_responses.append(self._build_access_response(access))

        return UserDocumentAccessStatsDTO(
            total_accesses=len(accesses),
            active_accesses=len(active_accesses),
            expired_accesses=len(expired_accesses),
            expiring_soon_accesses=len(expiring_soon_accesses),
            accesses_by_area=accesses_by_area,
            accesses_by_user=accesses_by_user,
            recent_accesses=recent_access_responses,
        )

    def _build_access_response(
        self, access: UserDocumentAccess
    ) -> UserDocumentAccessResponseDTO:
        """Build access response DTO."""
        # Get related data
        user_info = self.iam_contract.get_user_info(access.user_id)
        area = self.document_area_repository.get_by_id(access.area_id)
        assigned_by_info = self.iam_contract.get_user_info(access.assigned_by)

        return UserDocumentAccessResponseDTO(
            id=access.id,
            user_id=access.user_id,
            organization_id=access.organization_id,
            area_id=access.area_id,
            access_level=access.access_level.value,
            granted_by=access.granted_by,
            granted_at=access.granted_at,
            expires_at=access.expires_at,
            is_active=access.is_active,
            notes=access.notes,
            extra_data=access.extra_data,
            user_email=user_info.email if user_info else None,
            user_name=user_info.name if user_info else None,
            area_name=area.name if area else None,
            area_folder_path=area.folder_path if area else None,
            granted_by_name=assigned_by_info.name if assigned_by_info else None,
        )

    def _build_access_detail_response(
        self, access: UserDocumentAccess
    ) -> UserDocumentAccessDetailResponseDTO:
        """Build detailed access response DTO."""
        access_response = self._build_access_response(access)

        # Get full related entities
        user_info = self.iam_contract.get_user_info(access.user_id)
        area = self.document_area_repository.get_by_id(access.area_id)
        assigned_by_info = self.iam_contract.get_user_info(access.assigned_by)

        # Get accessible folders
        accessible_folders = []
        if area:
            accessible_folders = self.document_area_service.get_accessible_folders(area)

        # Convert to DTOs
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

        user_dto = None
        if user_info:
            user_dto = UserInfoDTO(
                id=user_info.id,
                name=user_info.name,
                email=user_info.email,
                is_active=user_info.is_active,
            )

        assigned_by_dto = None
        if assigned_by_info:
            assigned_by_dto = UserInfoDTO(
                id=assigned_by_info.id,
                name=assigned_by_info.name,
                email=assigned_by_info.email,
                is_active=assigned_by_info.is_active,
            )

        return UserDocumentAccessDetailResponseDTO(
            **access_response.model_dump(),
            area=area_dto,
            user=user_dto,
            assigned_by_user=assigned_by_dto,
            accessible_folders=accessible_folders,
            is_expired=access.is_expired(),
            days_until_expiry=access.days_until_expiry(),
        )