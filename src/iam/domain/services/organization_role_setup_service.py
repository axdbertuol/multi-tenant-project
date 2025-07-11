"""Service for setting up default roles and permissions for new organizations."""

from typing import List
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ..constants.default_roles import (
    DefaultRoleConfigurations,
    DefaultOrganizationRoles,
)
from ..entities.role import Role
from ..entities.permission import Permission
from ..value_objects.role_name import RoleName
from ..value_objects.permission_name import PermissionName
from ..repositories.role_repository import RoleRepository
from ..repositories.permission_repository import PermissionRepository
from ..repositories.role_permission_repository import RolePermissionRepository


class OrganizationRoleSetupService:
    """Service for setting up default roles and permissions for organizations."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._role_repository: RoleRepository = uow.get_repository("role")
        self._permission_repository: PermissionRepository = uow.get_repository(
            "permission"
        )
        self._role_permission_repository: RolePermissionRepository = uow.get_repository(
            "role_permission"
        )

    def setup_default_roles_for_organization(
        self, organization_id: UUID, owner_user_id: UUID
    ) -> List[Role]:
        """
        Create default roles for a new organization and assign owner role to the creator.

        Args:
            organization_id: ID of the organization
            owner_user_id: ID of the user who created the organization (becomes owner)

        Returns:
            List of created roles
        """
        created_roles = []

        with self._uow:
            # Create all default roles
            for role_name in DefaultRoleConfigurations.get_all_default_roles():
                role_config = DefaultRoleConfigurations.get_role_config(role_name)

                # Create role
                role = Role.create(
                    name=role_name,
                    description=role_config["description"],
                    organization_id=organization_id,
                    created_by=owner_user_id,
                    is_system_role=role_config.get("is_system_role", False),
                )

                saved_role = self._role_repository.save(role)
                created_roles.append(saved_role)

                # Create and assign permissions to role
                self._setup_role_permissions(saved_role, role_config["permissions"])

                # If this is the administrador role, assign it to the creator
                if role_name == DefaultOrganizationRoles.ADMINISTRADOR.value:
                    self._assign_role_to_user(
                        owner_user_id, organization_id, saved_role.id
                    )

        return created_roles

    def _setup_role_permissions(self, role: Role, permission_names: List[str]) -> None:
        """Setup permissions for a role."""
        for permission_name in permission_names:
            # Get or create permission
            permission = self._get_or_create_permission(permission_name)

            # Assign permission to role
            self._role_permission_repository.assign_permission_to_role(
                role_id=role.id, permission_id=permission.id
            )

    def _get_or_create_permission(self, permission_name: str) -> Permission:
        """Get existing permission or create new one."""
        # Try to find existing permission
        existing_permission = self._permission_repository.find_by_name(
            PermissionName(permission_name)
        )

        if existing_permission:
            return existing_permission

        # Create new permission if it doesn't exist
        resource_type, action = self._parse_permission_name(permission_name)

        permission = Permission.create(
            name=PermissionName(permission_name),
            description=f"Permission to {action} {resource_type}",
            resource_type=resource_type,
            action=action,
        )

        return self._permission_repository.save(permission)

    def _parse_permission_name(self, permission_name: str) -> tuple[str, str]:
        """Parse permission name into resource_type and action."""
        if ":" in permission_name:
            resource_type, action = permission_name.split(":", 1)
        else:
            resource_type = "general"
            action = permission_name

        return resource_type, action

    def _assign_role_to_user(
        self, user_id: UUID, organization_id: UUID, role_id: UUID
    ) -> None:
        """Assign a role to a user in an organization."""
        self._role_repository.assign_role_to_user(
            user_id=user_id, role_id=role_id, assigned_by=user_id
        )

    def get_organization_roles(self, organization_id: UUID) -> List[Role]:
        """Get all roles for an organization."""
        return self._role_repository.get_organization_roles(organization_id)

    def assign_default_member_role(self, user_id: UUID, organization_id: UUID) -> bool:
        """Assign default analista role to a user."""
        try:
            # Find analista role for the organization
            roles = self._role_repository.get_organization_roles(organization_id)
            member_role = None

            for role in roles:
                if role.name.value == DefaultOrganizationRoles.ANALISTA.value:
                    member_role = role
                    break

            if not member_role:
                return False

            # Assign analista role to user
            self._assign_role_to_user(user_id, organization_id, member_role.id)
            return True

        except Exception:
            return False
