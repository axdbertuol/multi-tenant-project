from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from ...domain.entities.management_function import ManagementFunction
from ...domain.repositories.management_function_repository import ManagementFunctionRepository
from ...domain.repositories.user_function_area_repository import UserFunctionAreaRepository
from ...domain.services.management_function_service import ManagementFunctionService
from ..dtos.management_function_dto import (
    ManagementFunctionCreateDTO,
    ManagementFunctionUpdateDTO,
    ManagementFunctionResponseDTO,
    ManagementFunctionDetailResponseDTO,
    ManagementFunctionListResponseDTO,
    ManagementFunctionPermissionAssignDTO,
    ManagementFunctionPermissionRemoveDTO,
    ManagementFunctionAssignmentDTO,
    ManagementFunctionStatsDTO,
)


class ManagementFunctionUseCase:
    """Use case for management function operations."""

    def __init__(
        self,
        management_function_repository: ManagementFunctionRepository,
        user_function_area_repository: UserFunctionAreaRepository,
        management_function_service: ManagementFunctionService,
    ):
        self.management_function_repository = management_function_repository
        self.user_function_area_repository = user_function_area_repository
        self.management_function_service = management_function_service

    def create_function(
        self, dto: ManagementFunctionCreateDTO
    ) -> ManagementFunctionResponseDTO:
        """Create a new management function."""
        # Validate function name is unique in organization
        existing_function = self.management_function_repository.get_by_name_and_organization(
            dto.name, dto.organization_id
        )
        if existing_function:
            raise ValueError(f"Function with name '{dto.name}' already exists")

        # Create function entity
        function = ManagementFunction.create(
            name=dto.name,
            description=dto.description,
            organization_id=dto.organization_id,
            permissions=dto.permissions,
        )

        # Save function
        saved_function = self.management_function_repository.save(function)

        return self._build_function_response(saved_function)

    def get_function_by_id(self, function_id: UUID) -> Optional[ManagementFunctionDetailResponseDTO]:
        """Get function by ID with assignments."""
        function = self.management_function_repository.get_by_id(function_id)
        if not function:
            return None

        return self._build_function_detail_response(function)

    def update_function(
        self, function_id: UUID, dto: ManagementFunctionUpdateDTO
    ) -> Optional[ManagementFunctionResponseDTO]:
        """Update an existing management function."""
        function = self.management_function_repository.get_by_id(function_id)
        if not function:
            return None

        # Check if function is system function
        if function.is_system_function:
            raise ValueError("Cannot update system function")

        # Update fields
        if dto.description is not None:
            function.description = dto.description

        if dto.permissions is not None:
            function.permissions = dto.permissions

        # Save function
        updated_function = self.management_function_repository.save(function)

        return self._build_function_response(updated_function)

    def delete_function(self, function_id: UUID) -> bool:
        """Delete a management function (soft delete)."""
        function = self.management_function_repository.get_by_id(function_id)
        if not function:
            return False

        # Check if function is system function
        if function.is_system_function:
            raise ValueError("Cannot delete system function")

        # Check if function has assignments
        assignments = self.user_function_area_repository.get_by_function(function_id)
        if assignments:
            raise ValueError("Cannot delete function with active assignments")

        function.is_active = False
        self.management_function_repository.save(function)

        return True

    def list_functions(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_system: bool = True,
    ) -> ManagementFunctionListResponseDTO:
        """List management functions with pagination."""
        offset = (page - 1) * page_size

        if include_system:
            functions = self.management_function_repository.get_by_organization(organization_id)
        else:
            functions = self.management_function_repository.get_active_by_organization(organization_id)
            functions = [f for f in functions if not f.is_system_function]

        # Apply pagination
        total = len(functions)
        paginated_functions = functions[offset:offset + page_size]

        function_responses = []
        for function in paginated_functions:
            function_responses.append(self._build_function_response(function))

        total_pages = (total + page_size - 1) // page_size

        return ManagementFunctionListResponseDTO(
            functions=function_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def assign_permissions(
        self, function_id: UUID, dto: ManagementFunctionPermissionAssignDTO
    ) -> Optional[ManagementFunctionDetailResponseDTO]:
        """Assign permissions to a management function."""
        function = self.management_function_repository.get_by_id(function_id)
        if not function:
            return None

        # Check if function is system function
        if function.is_system_function:
            raise ValueError("Cannot modify system function permissions")

        # Validate permissions using service
        if not self.management_function_service.validate_permissions(dto.permissions):
            raise ValueError("Invalid permissions provided")

        # Add permissions
        current_permissions = set(function.permissions)
        new_permissions = current_permissions.union(set(dto.permissions))
        function.permissions = list(new_permissions)

        # Save function
        updated_function = self.management_function_repository.save(function)

        return self._build_function_detail_response(updated_function)

    def remove_permissions(
        self, function_id: UUID, dto: ManagementFunctionPermissionRemoveDTO
    ) -> Optional[ManagementFunctionDetailResponseDTO]:
        """Remove permissions from a management function."""
        function = self.management_function_repository.get_by_id(function_id)
        if not function:
            return None

        # Check if function is system function
        if function.is_system_function:
            raise ValueError("Cannot modify system function permissions")

        # Remove permissions
        current_permissions = set(function.permissions)
        remaining_permissions = current_permissions - set(dto.permissions)
        function.permissions = list(remaining_permissions)

        # Save function
        updated_function = self.management_function_repository.save(function)

        return self._build_function_detail_response(updated_function)

    def assign_function_to_user(
        self, function_id: UUID, dto: ManagementFunctionAssignmentDTO
    ) -> bool:
        """Assign a management function to a user."""
        # This will be handled by UserFunctionAreaUseCase
        # but we provide a convenience method here
        from .user_function_area_use_cases import UserFunctionAreaUseCase
        
        function = self.management_function_repository.get_by_id(function_id)
        if not function:
            raise ValueError("Function not found")

        # This would need to be injected or created properly
        # For now, we'll just validate the function exists
        return True

    def get_functions_by_organization(
        self, organization_id: UUID
    ) -> List[ManagementFunctionResponseDTO]:
        """Get all functions for an organization."""
        functions = self.management_function_repository.get_active_by_organization(organization_id)

        function_responses = []
        for function in functions:
            function_responses.append(self._build_function_response(function))

        return function_responses

    def get_system_functions(
        self, organization_id: UUID
    ) -> List[ManagementFunctionResponseDTO]:
        """Get all system functions for an organization."""
        functions = self.management_function_repository.get_system_functions(organization_id)

        function_responses = []
        for function in functions:
            function_responses.append(self._build_function_response(function))

        return function_responses

    def get_functions_with_permission(
        self, permission: str, organization_id: UUID
    ) -> List[ManagementFunctionResponseDTO]:
        """Get all functions that have a specific permission."""
        functions = self.management_function_repository.get_functions_with_permission(
            permission, organization_id
        )

        function_responses = []
        for function in functions:
            function_responses.append(self._build_function_response(function))

        return function_responses

    def get_function_stats(self, organization_id: UUID) -> ManagementFunctionStatsDTO:
        """Get management function statistics."""
        all_functions = self.management_function_repository.get_by_organization(organization_id)
        
        active_functions = [f for f in all_functions if f.is_active]
        system_functions = [f for f in all_functions if f.is_system_function]
        custom_functions = [f for f in all_functions if not f.is_system_function]

        # Count assignments
        total_assignments = 0
        for function in all_functions:
            assignments = self.user_function_area_repository.get_by_function(function.id)
            total_assignments += len(assignments)

        # Count functions by permission
        functions_by_permission = {}
        for function in all_functions:
            for permission in function.permissions:
                if permission not in functions_by_permission:
                    functions_by_permission[permission] = 0
                functions_by_permission[permission] += 1

        return ManagementFunctionStatsDTO(
            total_functions=len(all_functions),
            active_functions=len(active_functions),
            system_functions=len(system_functions),
            custom_functions=len(custom_functions),
            total_assignments=total_assignments,
            functions_by_permission=functions_by_permission,
        )

    def create_default_functions(self, organization_id: UUID) -> List[ManagementFunctionResponseDTO]:
        """Create default management functions for an organization."""
        default_functions = self.management_function_service.create_default_functions(organization_id)
        
        created_functions = []
        for function in default_functions:
            saved_function = self.management_function_repository.save(function)
            created_functions.append(self._build_function_response(saved_function))

        return created_functions

    def _build_function_response(self, function: ManagementFunction) -> ManagementFunctionResponseDTO:
        """Build function response DTO."""
        # Count assignments
        assignments = self.user_function_area_repository.get_by_function(function.id)
        assignment_count = len(assignments)

        return ManagementFunctionResponseDTO(
            id=function.id,
            name=function.name,
            description=function.description,
            organization_id=function.organization_id,
            permissions=function.permissions,
            created_at=function.created_at,
            is_active=function.is_active,
            is_system_function=function.is_system_function,
            assignment_count=assignment_count,
        )

    def _build_function_detail_response(
        self, function: ManagementFunction
    ) -> ManagementFunctionDetailResponseDTO:
        """Build detailed function response DTO with assignments."""
        function_response = self._build_function_response(function)

        # Get assignments
        assignments = self.user_function_area_repository.get_by_function(function.id)
        
        # Note: This would need proper DTO conversion
        # For now, we'll create a basic response
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

        return ManagementFunctionDetailResponseDTO(
            **function_response.model_dump(),
            assignments=assignment_responses,
        )