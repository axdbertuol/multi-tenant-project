from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from ...domain.entities.role import Role
from ...domain.repositories.role_repository import RoleRepository
from ...domain.repositories.permission_repository import PermissionRepository
from ...domain.services.role_inheritance_service import RoleInheritanceService
from ..dtos.role_dto import (
    RoleCreateDTO,
    RoleUpdateDTO,
    RoleResponseDTO,
    RoleDetailResponseDTO,
    RoleListResponseDTO,
    RolePermissionAssignDTO,
    RolePermissionRemoveDTO,
)
from ..dtos.permission_dto import PermissionResponseDTO


class RoleUseCase:
    """Use case for role management operations."""

    def __init__(
        self,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
    ):
        self.role_repository = role_repository
        self.permission_repository = permission_repository
        self.role_inheritance_service = RoleInheritanceService()

    def create_role(self, dto: RoleCreateDTO, created_by: UUID) -> RoleResponseDTO:
        """Create a new role."""
        # Validate parent role if provided
        if hasattr(dto, "parent_role_id") and dto.parent_role_id:
            parent_role = self.role_repository.get_by_id(dto.parent_role_id)
            if not parent_role:
                raise ValueError("Parent role not found")

            # Validate inheritance rules
            temp_role = Role.create(
                name=dto.name,
                description=dto.description,
                created_by=created_by,
                organization_id=dto.organization_id,
                parent_role_id=dto.parent_role_id,
            )

            all_roles = self.role_repository.get_role_hierarchy(dto.organization_id)
            can_inherit, reason = self.role_inheritance_service.can_role_inherit_from(
                temp_role, parent_role, all_roles
            )

            if not can_inherit:
                raise ValueError(f"Invalid inheritance: {reason}")

        # Validate permissions exist
        if hasattr(dto, "permission_ids") and dto.permission_ids:
            permissions = self.permission_repository.find_by_ids(dto.permission_ids)
            if len(permissions) != len(dto.permission_ids):
                raise ValueError("One or more permissions not found")

        # Create role entity
        role = Role.create(
            name=dto.name,
            description=dto.description,
            created_by=created_by,
            organization_id=dto.organization_id,
            parent_role_id=getattr(dto, "parent_role_id", None),
        )

        # Save role
        saved_role = self.role_repository.save(role)

        # Assign permissions if provided
        if hasattr(dto, "permission_ids") and dto.permission_ids:
            self.role_repository.assign_permissions(saved_role.id, dto.permission_ids)

        return self._build_role_response(saved_role)

    def get_role_by_id(self, role_id: UUID) -> Optional[RoleDetailResponseDTO]:
        """Get role by ID with permissions."""
        role = self.role_repository.get_by_id(role_id)
        if not role:
            return None

        return self._build_role_detail_response(role)

    def update_role(
        self, role_id: UUID, dto: RoleUpdateDTO
    ) -> Optional[RoleResponseDTO]:
        """Update an existing role."""
        role = self.role_repository.get_by_id(role_id)
        if not role:
            return None

        # Update fields
        if dto.description is not None:
            role.description = dto.description

        role.updated_at = datetime.now(timezone.utc)

        # Save role
        updated_role = self.role_repository.save(role)

        # Update permissions if provided
        if dto.permission_ids is not None:
            # Validate permissions exist
            if dto.permission_ids:
                permissions = self.permission_repository.find_by_ids(dto.permission_ids)
                if len(permissions) != len(dto.permission_ids):
                    raise ValueError("One or more permissions not found")

            self.role_repository.replace_permissions(role_id, dto.permission_ids)

        return self._build_role_response(updated_role)

    def delete_role(self, role_id: UUID) -> bool:
        """Delete a role (soft delete)."""
        role = self.role_repository.get_by_id(role_id)
        if not role:
            return False

        # Check if role is system role
        if role.is_system_role:
            raise ValueError("Cannot delete system role")

        # Check if role has assignments
        assignment_count = self.role_repository.get_assignment_count(role_id)
        if assignment_count > 0:
            raise ValueError("Cannot delete role with active assignments")

        role.is_active = False
        role.updated_at = datetime.now(timezone.utc)
        self.role_repository.save(role)

        return True

    def list_roles(
        self,
        organization_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
        include_system: bool = True,
    ) -> RoleListResponseDTO:
        """List roles with pagination."""
        offset = (page - 1) * page_size

        roles, total = self.role_repository.find_paginated(
            organization_id=organization_id,
            include_system=include_system,
            offset=offset,
            limit=page_size,
        )

        role_responses = []
        for role in roles:
            role_responses.append(self._build_role_response(role))

        total_pages = (total + page_size - 1) // page_size

        return RoleListResponseDTO(
            roles=role_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def assign_permissions(
        self, role_id: UUID, dto: RolePermissionAssignDTO
    ) -> Optional[RoleDetailResponseDTO]:
        """Assign permissions to a role."""
        role = self.role_repository.get_by_id(role_id)
        if not role:
            return None

        # Validate permissions exist
        permissions = self.permission_repository.find_by_ids(dto.permission_ids)
        if len(permissions) != len(dto.permission_ids):
            raise ValueError("One or more permissions not found")

        self.role_repository.assign_permissions(role_id, dto.permission_ids)

        return self._build_role_detail_response(role)

    def remove_permissions(
        self, role_id: UUID, dto: RolePermissionRemoveDTO
    ) -> Optional[RoleDetailResponseDTO]:
        """Remove permissions from a role."""
        role = self.role_repository.get_by_id(role_id)
        if not role:
            return None

        self.role_repository.remove_permissions(role_id, dto.permission_ids)

        return self._build_role_detail_response(role)

    def get_roles_by_organization(self, organization_id: UUID) -> List[RoleResponseDTO]:
        """Get all roles for an organization."""
        roles = self.role_repository.get_organization_roles(organization_id)

        role_responses = []
        for role in roles:
            role_responses.append(self._build_role_response(role))

        return role_responses

    def set_role_parent(
        self, role_id: UUID, parent_role_id: UUID
    ) -> Optional[RoleResponseDTO]:
        """Set parent role for inheritance."""
        role = self.role_repository.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")

        parent_role = self.role_repository.get_by_id(parent_role_id)
        if not parent_role:
            raise ValueError("Parent role not found")

        # Validate inheritance rules
        all_roles = self.role_repository.get_role_hierarchy(role.organization_id)
        can_inherit, reason = self.role_inheritance_service.can_role_inherit_from(
            role, parent_role, all_roles
        )

        if not can_inherit:
            raise ValueError(f"Invalid inheritance: {reason}")

        # Update role
        updated_role = role.set_parent_role(parent_role_id)
        saved_role = self.role_repository.save(updated_role)

        return self._build_role_response(saved_role)

    def remove_role_parent(self, role_id: UUID) -> Optional[RoleResponseDTO]:
        """Remove parent role inheritance."""
        role = self.role_repository.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")

        # Update role
        updated_role = role.remove_parent_role()
        saved_role = self.role_repository.save(updated_role)

        return self._build_role_response(saved_role)

    def get_role_hierarchy(
        self, organization_id: Optional[UUID] = None
    ) -> List[RoleResponseDTO]:
        """Get role hierarchy for an organization."""
        roles = self.role_repository.get_role_hierarchy(organization_id)

        role_responses = []
        for role in roles:
            role_responses.append(self._build_role_response(role))

        return role_responses

    def get_role_children(self, role_id: UUID) -> List[RoleResponseDTO]:
        """Get direct child roles of a role."""
        child_roles = self.role_repository.get_child_roles(role_id)

        role_responses = []
        for role in child_roles:
            role_responses.append(self._build_role_response(role))

        return role_responses

    def get_effective_permissions(self, role_id: UUID) -> List[PermissionResponseDTO]:
        """Get all effective permissions for a role (including inherited)."""
        role = self.role_repository.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")

        # Get all roles for hierarchy calculation
        all_roles = self.role_repository.get_role_hierarchy(role.organization_id)

        # Get role permissions mapping
        role_permissions = {}
        for r in all_roles:
            permissions = self.role_repository.get_role_permissions(r.id)
            role_permissions[r.id] = permissions

        # Calculate inherited permissions
        effective_permissions = (
            self.role_inheritance_service.calculate_inherited_permissions(
                role, all_roles, role_permissions
            )
        )

        # Convert to DTOs
        permission_responses = []
        for perm in effective_permissions:
            permission_responses.append(
                PermissionResponseDTO(
                    id=perm.id,
                    name=perm.name,
                    description=perm.description,
                    permission_type=perm.permission_type,
                    resource_type=perm.resource_type,
                    full_name=perm.full_name,
                    created_at=perm.created_at,
                    updated_at=perm.updated_at,
                    is_active=perm.is_active,
                    is_system_permission=perm.is_system_permission,
                    role_count=0,
                )
            )

        return permission_responses

    def validate_role_hierarchy(
        self, organization_id: Optional[UUID] = None
    ) -> List[str]:
        """Validate role hierarchy for issues."""
        roles = self.role_repository.get_role_hierarchy(organization_id)
        return self.role_inheritance_service.validate_role_hierarchy(roles)

    def get_role_tree(self, organization_id: Optional[UUID] = None) -> dict:
        """Get role hierarchy as tree structure."""
        roles = self.role_repository.get_role_hierarchy(organization_id)
        tree = self.role_inheritance_service.build_role_tree(roles)

        # Convert to response DTOs
        response_tree = {}
        for parent_id, child_roles in tree.items():
            parent_key = str(parent_id) if parent_id != "root" else "root"
            response_tree[parent_key] = [
                self._build_role_response(role) for role in child_roles
            ]

        return response_tree

    def _build_role_response(self, role: Role) -> RoleResponseDTO:
        """Build role response DTO."""
        permission_count = self.role_repository.get_permission_count(role.id)
        assignment_count = self.role_repository.get_assignment_count(role.id)
        has_children = self.role_repository.has_child_roles(role.id)

        # Calculate inheritance level
        inheritance_level = 0
        if role.has_parent():
            all_roles = self.role_repository.get_role_hierarchy(role.organization_id)
            hierarchy_path = role.get_role_hierarchy_path(all_roles)
            inheritance_level = len(hierarchy_path) - 1

        return RoleResponseDTO(
            id=role.id,
            name=role.name.value,
            description=role.description,
            organization_id=role.organization_id,
            parent_role_id=role.parent_role_id,
            created_by=role.created_by,
            created_at=role.created_at,
            updated_at=role.updated_at,
            is_active=role.is_active,
            is_system_role=role.is_system_role,
            permission_count=permission_count,
            assignment_count=assignment_count,
            has_children=has_children,
            inheritance_level=inheritance_level,
        )

    def _build_role_detail_response(self, role: Role) -> RoleDetailResponseDTO:
        """Build detailed role response DTO with permissions."""
        role_response = self._build_role_response(role)

        # Get permissions
        permissions = self.role_repository.get_role_permissions(role.id)
        permission_responses = [
            PermissionResponseDTO(
                id=perm.id,
                name=perm.name,
                description=perm.description,
                permission_type=perm.permission_type,
                resource_type=perm.resource_type,
                full_name=perm.full_name,
                created_at=perm.created_at,
                updated_at=perm.updated_at,
                is_active=perm.is_active,
                is_system_permission=perm.is_system_permission,
                role_count=0,  # Not needed in this context
            )
            for perm in permissions
        ]

        return RoleDetailResponseDTO(
            **role_response.model_dump(), permissions=permission_responses
        )
