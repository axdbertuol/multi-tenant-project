from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from ...domain.entities.user_function_area import UserFunctionArea
from ...domain.repositories.user_function_area_repository import UserFunctionAreaRepository
from ...domain.repositories.management_function_repository import ManagementFunctionRepository
from ...domain.repositories.document_area_repository import DocumentAreaRepository
from ...domain.repositories.user_repository import UserRepository
from ...domain.services.document_access_service import DocumentAccessService
from ..dtos.user_function_area_dto import (
    UserFunctionAreaCreateDTO,
    UserFunctionAreaUpdateDTO,
    UserFunctionAreaResponseDTO,
    UserFunctionAreaDetailResponseDTO,
    UserFunctionAreaListResponseDTO,
    UserFunctionAreaBatchCreateDTO,
    UserFunctionAreaBatchUpdateDTO,
    UserFunctionAreaTransferDTO,
    UserFunctionAreaStatsDTO,
    UserFunctionAreaFilterDTO,
    UserFunctionAreaSearchDTO,
    UserFunctionAreaBulkActionDTO,
    UserFunctionAreaBulkActionResponseDTO,
    UserContextDTO,
)


class UserFunctionAreaUseCase:
    """Use case for user function area assignment operations."""

    def __init__(
        self,
        user_function_area_repository: UserFunctionAreaRepository,
        management_function_repository: ManagementFunctionRepository,
        document_area_repository: DocumentAreaRepository,
        user_repository: UserRepository,
        document_access_service: DocumentAccessService,
    ):
        self.user_function_area_repository = user_function_area_repository
        self.management_function_repository = management_function_repository
        self.document_area_repository = document_area_repository
        self.user_repository = user_repository
        self.document_access_service = document_access_service

    def create_assignment(
        self, dto: UserFunctionAreaCreateDTO
    ) -> UserFunctionAreaResponseDTO:
        """Create a new user function area assignment."""
        # Validate user exists
        user = self.user_repository.get_by_id(dto.user_id)
        if not user:
            raise ValueError("User not found")

        # Validate function exists
        function = self.management_function_repository.get_by_id(dto.function_id)
        if not function:
            raise ValueError("Management function not found")

        # Validate area exists
        area = self.document_area_repository.get_by_id(dto.area_id)
        if not area:
            raise ValueError("Document area not found")

        # Validate all belong to same organization
        if function.organization_id != dto.organization_id:
            raise ValueError("Function must belong to the same organization")
        if area.organization_id != dto.organization_id:
            raise ValueError("Area must belong to the same organization")

        # Check if user already has an assignment in this organization
        existing_assignment = self.user_function_area_repository.get_by_user_and_organization(
            dto.user_id, dto.organization_id
        )
        if existing_assignment and existing_assignment.is_active:
            raise ValueError("User already has an active assignment in this organization")

        # Create assignment entity
        assignment = UserFunctionArea.create(
            user_id=dto.user_id,
            organization_id=dto.organization_id,
            function_id=dto.function_id,
            area_id=dto.area_id,
            assigned_by=dto.assigned_by,
        )

        # Save assignment
        saved_assignment = self.user_function_area_repository.save(assignment)

        return self._build_assignment_response(saved_assignment)

    def get_assignment_by_id(
        self, assignment_id: UUID
    ) -> Optional[UserFunctionAreaDetailResponseDTO]:
        """Get assignment by ID with full details."""
        assignment = self.user_function_area_repository.get_by_id(assignment_id)
        if not assignment:
            return None

        return self._build_assignment_detail_response(assignment)

    def update_assignment(
        self, assignment_id: UUID, dto: UserFunctionAreaUpdateDTO
    ) -> Optional[UserFunctionAreaResponseDTO]:
        """Update an existing user function area assignment."""
        assignment = self.user_function_area_repository.get_by_id(assignment_id)
        if not assignment:
            return None

        # Update fields
        if dto.function_id is not None:
            # Validate function exists and belongs to same organization
            function = self.management_function_repository.get_by_id(dto.function_id)
            if not function:
                raise ValueError("Management function not found")
            if function.organization_id != assignment.organization_id:
                raise ValueError("Function must belong to the same organization")
            assignment.function_id = dto.function_id

        if dto.area_id is not None:
            # Validate area exists and belongs to same organization
            area = self.document_area_repository.get_by_id(dto.area_id)
            if not area:
                raise ValueError("Document area not found")
            if area.organization_id != assignment.organization_id:
                raise ValueError("Area must belong to the same organization")
            assignment.area_id = dto.area_id

        if dto.is_active is not None:
            assignment.is_active = dto.is_active

        # Save assignment
        updated_assignment = self.user_function_area_repository.save(assignment)

        return self._build_assignment_response(updated_assignment)

    def delete_assignment(self, assignment_id: UUID) -> bool:
        """Delete a user function area assignment."""
        assignment = self.user_function_area_repository.get_by_id(assignment_id)
        if not assignment:
            return False

        return self.user_function_area_repository.delete(assignment_id)

    def deactivate_assignment(self, assignment_id: UUID) -> Optional[UserFunctionAreaResponseDTO]:
        """Deactivate a user function area assignment."""
        assignment = self.user_function_area_repository.get_by_id(assignment_id)
        if not assignment:
            return None

        assignment.is_active = False
        updated_assignment = self.user_function_area_repository.save(assignment)

        return self._build_assignment_response(updated_assignment)

    def batch_create_assignments(
        self, dto: UserFunctionAreaBatchCreateDTO
    ) -> List[UserFunctionAreaResponseDTO]:
        """Create multiple user function area assignments."""
        created_assignments = []
        
        for assignment_dto in dto.assignments:
            try:
                assignment = self.create_assignment(assignment_dto)
                created_assignments.append(assignment)
            except ValueError as e:
                # Log error but continue with other assignments
                continue

        return created_assignments

    def batch_update_assignments(
        self, dto: UserFunctionAreaBatchUpdateDTO
    ) -> List[UserFunctionAreaResponseDTO]:
        """Update multiple user function area assignments."""
        updated_assignments = []
        
        for assignment_id in dto.assignment_ids:
            try:
                update_dto = UserFunctionAreaUpdateDTO(
                    function_id=dto.function_id,
                    area_id=dto.area_id,
                    is_active=dto.is_active,
                )
                assignment = self.update_assignment(assignment_id, update_dto)
                if assignment:
                    updated_assignments.append(assignment)
            except ValueError as e:
                # Log error but continue with other assignments
                continue

        return updated_assignments

    def transfer_assignments(
        self, dto: UserFunctionAreaTransferDTO
    ) -> List[UserFunctionAreaResponseDTO]:
        """Transfer user assignments from one function/area to another."""
        transferred_assignments = []
        
        for user_id in dto.user_ids:
            # Get current assignment
            current_assignment = self.user_function_area_repository.get_by_user_and_organization(
                user_id, dto.organization_id
            )
            
            if not current_assignment:
                continue
                
            # Check if matches source criteria
            if current_assignment.function_id != dto.source_function_id:
                continue
                
            if dto.source_area_id and current_assignment.area_id != dto.source_area_id:
                continue
            
            # Update assignment
            update_dto = UserFunctionAreaUpdateDTO(
                function_id=dto.target_function_id,
                area_id=dto.target_area_id or current_assignment.area_id,
            )
            
            try:
                updated_assignment = self.update_assignment(current_assignment.id, update_dto)
                if updated_assignment:
                    transferred_assignments.append(updated_assignment)
            except ValueError as e:
                # Log error but continue
                continue

        return transferred_assignments

    def list_assignments(
        self,
        filters: Optional[UserFunctionAreaFilterDTO] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UserFunctionAreaListResponseDTO:
        """List user function area assignments with filtering and pagination."""
        # Apply filters
        if filters:
            if filters.user_id:
                if filters.organization_id:
                    assignment = self.user_function_area_repository.get_by_user_and_organization(
                        filters.user_id, filters.organization_id
                    )
                    assignments = [assignment] if assignment else []
                else:
                    assignments = self.user_function_area_repository.get_by_user(filters.user_id)
            elif filters.organization_id:
                assignments = self.user_function_area_repository.get_by_organization(filters.organization_id)
            elif filters.function_id:
                assignments = self.user_function_area_repository.get_by_function(filters.function_id)
            elif filters.area_id:
                assignments = self.user_function_area_repository.get_by_area(filters.area_id)
            else:
                # Get all assignments (this might be too broad in production)
                assignments = []
        else:
            assignments = []

        # Apply additional filters
        if filters and assignments:
            if filters.is_active is not None:
                assignments = [a for a in assignments if a.is_active == filters.is_active]
            if filters.assigned_by:
                assignments = [a for a in assignments if a.assigned_by == filters.assigned_by]
            if filters.assigned_after:
                assignments = [a for a in assignments if a.assigned_at >= filters.assigned_after]
            if filters.assigned_before:
                assignments = [a for a in assignments if a.assigned_at <= filters.assigned_before]

        # Apply pagination
        total = len(assignments)
        offset = (page - 1) * page_size
        paginated_assignments = assignments[offset:offset + page_size]

        assignment_responses = []
        for assignment in paginated_assignments:
            assignment_responses.append(self._build_assignment_response(assignment))

        total_pages = (total + page_size - 1) // page_size

        return UserFunctionAreaListResponseDTO(
            assignments=assignment_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def search_assignments(
        self, dto: UserFunctionAreaSearchDTO
    ) -> List[UserFunctionAreaResponseDTO]:
        """Search user function area assignments."""
        # This would need to be implemented with proper search functionality
        # For now, we'll do a simple filter-based search
        assignments = []
        
        if dto.filters:
            assignments = self.list_assignments(dto.filters, page=1, page_size=1000).assignments
        
        # Apply text search (simplified)
        if dto.query:
            # This would need proper search implementation
            # For now, just return filtered results
            pass

        return assignments

    def bulk_action(
        self, dto: UserFunctionAreaBulkActionDTO
    ) -> UserFunctionAreaBulkActionResponseDTO:
        """Perform bulk action on user function area assignments."""
        success_count = 0
        failure_count = 0
        errors = []
        affected_assignments = []

        for assignment_id in dto.assignment_ids:
            try:
                if dto.action == "activate":
                    update_dto = UserFunctionAreaUpdateDTO(is_active=True)
                    result = self.update_assignment(assignment_id, update_dto)
                    if result:
                        success_count += 1
                        affected_assignments.append(assignment_id)
                    else:
                        failure_count += 1
                        errors.append(f"Assignment {assignment_id} not found")
                        
                elif dto.action == "deactivate":
                    result = self.deactivate_assignment(assignment_id)
                    if result:
                        success_count += 1
                        affected_assignments.append(assignment_id)
                    else:
                        failure_count += 1
                        errors.append(f"Assignment {assignment_id} not found")
                        
                elif dto.action == "delete":
                    result = self.delete_assignment(assignment_id)
                    if result:
                        success_count += 1
                        affected_assignments.append(assignment_id)
                    else:
                        failure_count += 1
                        errors.append(f"Assignment {assignment_id} not found")
                        
                else:
                    failure_count += 1
                    errors.append(f"Unknown action: {dto.action}")
                    
            except Exception as e:
                failure_count += 1
                errors.append(f"Error processing assignment {assignment_id}: {str(e)}")

        return UserFunctionAreaBulkActionResponseDTO(
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
            affected_assignments=affected_assignments,
        )

    def get_user_context(
        self, user_id: UUID, organization_id: UUID
    ) -> Optional[UserContextDTO]:
        """Get user context with function and area information."""
        assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not assignment or not assignment.is_active:
            return None

        # Get function details
        function = self.management_function_repository.get_by_id(assignment.function_id)
        if not function:
            return None

        # Get area details
        area = self.document_area_repository.get_by_id(assignment.area_id)
        if not area:
            return None

        # Get accessible folders
        accessible_folders = self.document_access_service.get_accessible_folders(
            assignment.area_id
        )

        return UserContextDTO(
            user_id=user_id,
            organization_id=organization_id,
            function_id=function.id,
            function_name=function.name,
            area_id=area.id,
            area_name=area.name,
            area_folder_path=area.folder_path,
            effective_permissions=function.permissions,
            accessible_folders=accessible_folders,
            is_active=assignment.is_active,
        )

    def get_assignment_stats(
        self, organization_id: Optional[UUID] = None
    ) -> UserFunctionAreaStatsDTO:
        """Get user function area assignment statistics."""
        if organization_id:
            assignments = self.user_function_area_repository.get_by_organization(organization_id)
        else:
            # This might be too broad - consider limiting scope
            assignments = []

        active_assignments = [a for a in assignments if a.is_active]
        inactive_assignments = [a for a in assignments if not a.is_active]

        # Count by function
        assignments_by_function = {}
        for assignment in assignments:
            function = self.management_function_repository.get_by_id(assignment.function_id)
            if function:
                function_name = function.name
                if function_name not in assignments_by_function:
                    assignments_by_function[function_name] = 0
                assignments_by_function[function_name] += 1

        # Count by area
        assignments_by_area = {}
        for assignment in assignments:
            area = self.document_area_repository.get_by_id(assignment.area_id)
            if area:
                area_name = area.name
                if area_name not in assignments_by_area:
                    assignments_by_area[area_name] = 0
                assignments_by_area[area_name] += 1

        # Count by user
        assignments_by_user = {}
        for assignment in assignments:
            user = self.user_repository.get_by_id(assignment.user_id)
            if user:
                user_email = user.email
                if user_email not in assignments_by_user:
                    assignments_by_user[user_email] = 0
                assignments_by_user[user_email] += 1

        # Get recent assignments
        recent_assignments = sorted(assignments, key=lambda x: x.assigned_at, reverse=True)[:10]
        recent_assignment_responses = []
        for assignment in recent_assignments:
            recent_assignment_responses.append(self._build_assignment_response(assignment))

        return UserFunctionAreaStatsDTO(
            total_assignments=len(assignments),
            active_assignments=len(active_assignments),
            inactive_assignments=len(inactive_assignments),
            assignments_by_function=assignments_by_function,
            assignments_by_area=assignments_by_area,
            assignments_by_user=assignments_by_user,
            recent_assignments=recent_assignment_responses,
        )

    def _build_assignment_response(
        self, assignment: UserFunctionArea
    ) -> UserFunctionAreaResponseDTO:
        """Build assignment response DTO."""
        # Get related data
        user = self.user_repository.get_by_id(assignment.user_id)
        function = self.management_function_repository.get_by_id(assignment.function_id)
        area = self.document_area_repository.get_by_id(assignment.area_id)
        assigned_by_user = self.user_repository.get_by_id(assignment.assigned_by)

        return UserFunctionAreaResponseDTO(
            id=assignment.id,
            user_id=assignment.user_id,
            organization_id=assignment.organization_id,
            function_id=assignment.function_id,
            area_id=assignment.area_id,
            assigned_by=assignment.assigned_by,
            assigned_at=assignment.assigned_at,
            is_active=assignment.is_active,
            user_email=user.email if user else None,
            user_name=user.name if user else None,
            function_name=function.name if function else None,
            area_name=area.name if area else None,
            area_folder_path=area.folder_path if area else None,
            assigned_by_name=assigned_by_user.name if assigned_by_user else None,
        )

    def _build_assignment_detail_response(
        self, assignment: UserFunctionArea
    ) -> UserFunctionAreaDetailResponseDTO:
        """Build detailed assignment response DTO."""
        assignment_response = self._build_assignment_response(assignment)

        # Get full related entities
        user = self.user_repository.get_by_id(assignment.user_id)
        function = self.management_function_repository.get_by_id(assignment.function_id)
        area = self.document_area_repository.get_by_id(assignment.area_id)
        assigned_by_user = self.user_repository.get_by_id(assignment.assigned_by)

        # Get accessible folders
        accessible_folders = []
        if area:
            accessible_folders = self.document_access_service.get_accessible_folders(area.id)

        # Get effective permissions
        effective_permissions = function.permissions if function else []

        # Convert to DTOs (simplified - would need proper conversion)
        from ..dtos.management_function_dto import ManagementFunctionResponseDTO
        from ..dtos.document_area_dto import DocumentAreaResponseDTO
        from ..dtos.user_dto import UserResponseDTO

        function_dto = None
        if function:
            function_dto = ManagementFunctionResponseDTO(
                id=function.id,
                name=function.name,
                description=function.description,
                organization_id=function.organization_id,
                permissions=function.permissions,
                created_at=function.created_at,
                is_active=function.is_active,
                is_system_function=function.is_system_function,
                assignment_count=0,
            )

        area_dto = None
        if area:
            area_dto = DocumentAreaResponseDTO(
                id=area.id,
                name=area.name,
                organization_id=area.organization_id,
                parent_area_id=area.parent_area_id,
                folder_path=area.folder_path,
                created_at=area.created_at,
                is_active=area.is_active,
                is_system_area=area.is_system_area,
            )

        user_dto = None
        if user:
            user_dto = UserResponseDTO(
                id=user.id,
                name=user.name,
                email=user.email,
                created_at=user.created_at,
                is_active=user.is_active,
                is_verified=user.is_verified,
                last_login=user.last_login,
                organization_count=0,
            )

        assigned_by_dto = None
        if assigned_by_user:
            assigned_by_dto = UserResponseDTO(
                id=assigned_by_user.id,
                name=assigned_by_user.name,
                email=assigned_by_user.email,
                created_at=assigned_by_user.created_at,
                is_active=assigned_by_user.is_active,
                is_verified=assigned_by_user.is_verified,
                last_login=assigned_by_user.last_login,
                organization_count=0,
            )

        return UserFunctionAreaDetailResponseDTO(
            **assignment_response.model_dump(),
            function=function_dto,
            area=area_dto,
            user=user_dto,
            assigned_by_user=assigned_by_dto,
            accessible_folders=accessible_folders,
            effective_permissions=effective_permissions,
        )