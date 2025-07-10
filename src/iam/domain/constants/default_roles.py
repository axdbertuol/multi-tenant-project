"""Default organization roles and their configurations."""

from enum import Enum
from typing import Dict, List

from shared.infrastructure.config import get_configuration_loader


class DefaultOrganizationRoles(Enum):
    """Default roles created for new organizations."""

    ADMINISTRADOR = "administrador"
    GERENCIADOR = "gerenciador"
    ESPECIALISTA = "especialista"
    ANALISTA = "analista"


class DefaultRoleConfigurations:
    """Default configurations for organization roles."""

    _config_loader = None
    _cached_configs = None

    @classmethod
    def _get_config_loader(cls):
        """Get configuration loader instance."""
        if cls._config_loader is None:
            cls._config_loader = get_configuration_loader()
        return cls._config_loader

    @classmethod
    def _load_role_configs(cls) -> Dict[str, Dict[str, any]]:
        """Load role configurations from JSON files."""
        if cls._cached_configs is None:
            cls._cached_configs = cls._get_config_loader().load_default_roles()
        return cls._cached_configs

    @classmethod
    def _get_role_configs(cls) -> Dict[str, Dict[str, any]]:
        """Get role configurations with fallback to hardcoded values."""
        try:
            return cls._load_role_configs()
        except Exception:
            # Fallback to hardcoded configurations
            return {
                DefaultOrganizationRoles.ADMINISTRADOR.value: {
                    "description": "Administrador com permissão para usar tudo",
                    "permissions": [
                        "organization:*",
                        "user:*",
                        "role:*",
                        "permission:*",
                        "resource:*",
                        "application:*",
                        "document:*",
                        "folder:*",
                        "rag:*",
                        "ai:*",
                        "settings:*",
                    ],
                    "is_system_role": True,
                    "can_be_deleted": False,
                    "hierarchy_level": 1,
                },
                DefaultOrganizationRoles.GERENCIADOR.value: {
                    "description": "Gerenciador com permissões de administração",
                    "permissions": [
                        "organization:read",
                        "organization:update",
                        "user:*",
                        "role:read",
                        "permission:read",
                        "resource:*",
                        "application:*",
                        "document:*",
                        "folder:*",
                        "rag:*",
                        "ai:*",
                        "settings:read",
                        "settings:update",
                    ],
                    "is_system_role": True,
                    "can_be_deleted": False,
                    "hierarchy_level": 2,
                    "parent_role": "administrador",
                },
                DefaultOrganizationRoles.ESPECIALISTA.value: {
                    "description": "Especialista com permissões de edição",
                    "permissions": [
                        "organization:read",
                        "user:read",
                        "role:read",
                        "resource:read",
                        "resource:use",
                        "application:read",
                        "application:use",
                        "document:read",
                        "document:update",
                        "document:share",
                        "document:download",
                        "rag:query_by_profile",
                        "ai:query_by_profile",
                    ],
                    "is_system_role": True,
                    "can_be_deleted": False,
                    "hierarchy_level": 3,
                    "parent_role": "gerenciador",
                },
                DefaultOrganizationRoles.ANALISTA.value: {
                    "description": "Analista com permissões de leitura",
                    "permissions": [
                        "organization:read",
                        "user:read",
                        "role:read",
                        "resource:read",
                        "application:read",
                        "document:read",
                        "document:download",
                        "rag:query_by_profile",
                        "ai:query_by_profile",
                    ],
                    "is_system_role": True,
                    "can_be_deleted": False,
                    "hierarchy_level": 4,
                    "parent_role": "especialista",
                },
            }

    @classmethod
    def get_role_configs(cls) -> Dict[str, Dict[str, any]]:
        """Get all role configurations."""
        return cls._get_role_configs()

    @classmethod
    def get_role_config(cls, role_name: str) -> Dict[str, any]:
        """Get configuration for a specific role."""
        return cls.get_role_configs().get(role_name, {})

    @classmethod
    def get_default_permissions(cls, role_name: str) -> List[str]:
        """Get default permissions for a role."""
        config = cls.get_role_config(role_name)
        return config.get("permissions", [])

    @classmethod
    def get_all_default_roles(cls) -> List[str]:
        """Get all default role names."""
        return list(cls.get_role_configs().keys())

    @classmethod
    def reload_configurations(cls) -> None:
        """Reload configurations from JSON files."""
        cls._cached_configs = None
        if cls._config_loader:
            cls._config_loader.reload_cache()
