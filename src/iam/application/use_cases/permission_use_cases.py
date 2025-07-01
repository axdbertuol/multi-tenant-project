from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from ...domain.entities.permission import Permission
from ...domain.repositories.permission_repository import PermissionRepository
from ..dtos.permission_dto import (
    PermissionCreateDTO,
    PermissionResponseDTO,
    PermissionListResponseDTO,
    PermissionSearchDTO,
)


class PermissionUseCase:
    """Use case for permission management operations."""

    def __init__(self, permission_repository: PermissionRepository):
        self.permission_repository = permission_repository

    def create_permission(self, dto: PermissionCreateDTO) -> PermissionResponseDTO:
        """Create a new permission."""
        # Check if permission already exists
        existing = self.permission_repository.find_by_name_and_resource(
            dto.name, dto.resource_type
        )
        if existing:
            raise ValueError(
                f"Permission {dto.name}:{dto.resource_type} already exists"
            )

        # Create permission entity
        permission = Permission(
            name=dto.name,
            description=dto.description,
            action=dto.action,
            resource_type=dto.resource_type,
            created_at=datetime.now(timezone.utc),
        )

        # Save permission
        saved_permission = self.permission_repository.save(permission)

        return self._build_permission_response(saved_permission)

    def get_permission_by_id(
        self, permission_id: UUID
    ) -> Optional[PermissionResponseDTO]:
        """Get permission by ID."""
        permission = self.permission_repository.find_by_id(permission_id)
        if not permission:
            return None

        return self._build_permission_response(permission)

    def list_permissions(
        self, page: int = 1, page_size: int = 20, include_system: bool = True
    ) -> PermissionListResponseDTO:
        """List permissions with pagination."""
        offset = (page - 1) * page_size

        permissions, total = self.permission_repository.find_paginated(
            include_system=include_system, offset=offset, limit=page_size
        )

        permission_responses = []
        for permission in permissions:
            permission_responses.append(self._build_permission_response(permission))

        total_pages = (total + page_size - 1) // page_size

        return PermissionListResponseDTO(
            permissions=permission_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def search_permissions(
        self, search_dto: PermissionSearchDTO, page: int = 1, page_size: int = 20
    ) -> PermissionListResponseDTO:
        """Search permissions with filters."""
        offset = (page - 1) * page_size

        permissions, total = self.permission_repository.search(
            query=search_dto.query,
            resource_type=search_dto.resource_type,
            action=search_dto.action,
            is_active=search_dto.is_active,
            offset=offset,
            limit=page_size,
        )

        permission_responses = []
        for permission in permissions:
            permission_responses.append(self._build_permission_response(permission))

        total_pages = (total + page_size - 1) // page_size

        return PermissionListResponseDTO(
            permissions=permission_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_permissions_by_resource_type(
        self, resource_type: str
    ) -> List[PermissionResponseDTO]:
        """Get all permissions for a specific resource type."""
        permissions = self.permission_repository.find_by_resource_type(resource_type)

        permission_responses = []
        for permission in permissions:
            permission_responses.append(self._build_permission_response(permission))

        return permission_responses

    def delete_permission(self, permission_id: UUID) -> bool:
        """Delete a permission (soft delete)."""
        permission = self.permission_repository.find_by_id(permission_id)
        if not permission:
            return False

        # Check if permission is system permission
        if permission.is_system_permission:
            raise ValueError("Cannot delete system permission")

        # Check if permission is assigned to any roles
        role_count = self.permission_repository.get_role_count(permission_id)
        if role_count > 0:
            raise ValueError("Cannot delete permission assigned to roles")

        permission.is_active = False
        permission.updated_at = datetime.now(timezone.utc)
        self.permission_repository.save(permission)

        return True

    def get_system_permissions(self) -> List[PermissionResponseDTO]:
        """Get all system permissions."""
        permissions = self.permission_repository.find_system_permissions()

        permission_responses = []
        for permission in permissions:
            permission_responses.append(self._build_permission_response(permission))

        return permission_responses

    def bulk_create_permissions(
        self, dtos: List[PermissionCreateDTO]
    ) -> List[PermissionResponseDTO]:
        """Create multiple permissions in bulk."""
        permissions = []

        for dto in dtos:
            # Check if permission already exists
            existing = self.permission_repository.find_by_name_and_resource(
                dto.name, dto.resource_type
            )
            if existing:
                continue  # Skip existing permissions

            # Create permission entity
            permission = Permission(
                name=dto.name,
                description=dto.description,
                action=dto.action,
                resource_type=dto.resource_type,
                created_at=datetime.now(timezone.utc),
            )
            permissions.append(permission)

        # Bulk save
        if permissions:
            saved_permissions = self.permission_repository.bulk_save(permissions)

            permission_responses = []
            for permission in saved_permissions:
                permission_responses.append(self._build_permission_response(permission))

            return permission_responses

        return []

    def _build_permission_response(
        self, permission: Permission
    ) -> PermissionResponseDTO:
        """Build permission response DTO."""
        role_count = self.permission_repository.get_role_count(permission.id)

        return PermissionResponseDTO(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            action=permission.action,
            resource_type=permission.resource_type,
            full_name=permission.get_full_name(),
            created_at=permission.created_at,
            updated_at=permission.updated_at,
            is_active=permission.is_active,
            is_system_permission=permission.is_system_permission,
            role_count=role_count,
        )
