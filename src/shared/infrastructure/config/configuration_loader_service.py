"""Service for loading default configurations from JSON files."""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from uuid import uuid4


class ConfigurationLoaderService:
    """Service for loading and caching default configurations from JSON files."""

    def __init__(self, config_base_path: Optional[str] = None):
        """
        Initialize the configuration loader service.
        
        Args:
            config_base_path: Base path for configuration files. 
                            Defaults to shared/config/defaults relative to project root.
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if config_base_path:
            self.config_base_path = Path(config_base_path)
        else:
            # Default to project's shared config directory
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            self.config_base_path = project_root / "shared" / "config" / "defaults"
        
        # Cache for loaded configurations
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_enabled = True

    def load_default_roles(self) -> Dict[str, Dict[str, Any]]:
        """Load default role configurations."""
        return self._load_json_config("roles/default_roles.json", "default_roles")

    def load_application_types(self) -> Dict[str, Dict[str, Any]]:
        """Load application type configurations."""
        return self._load_json_config("applications/application_types.json", "application_types")

    def load_plan_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Load plan configurations."""
        config = self._load_json_config("applications/plan_configurations.json", "plan_configurations")
        return config.get("plans", {})

    def load_app_config(self, app_type: str) -> Dict[str, Any]:
        """
        Load specific application configuration.
        
        Args:
            app_type: Type of application (e.g., 'web_chat_app', 'whatsapp_app')
            
        Returns:
            Configuration dictionary for the application type
        """
        cache_key = f"app_config_{app_type}"
        file_path = f"applications/app_configs/{app_type}.json"
        
        return self._load_json_config(file_path, cache_key)

    def load_trial_settings(self) -> Dict[str, Any]:
        """Load trial subscription settings."""
        return self._load_json_config("subscription/trial_settings.json", "trial_settings")

    def get_default_app_configuration(self, app_type: str, organization_id: str) -> Dict[str, Any]:
        """
        Get default configuration for a specific application type with organization-specific values.
        
        Args:
            app_type: Type of application
            organization_id: ID of the organization (for organization-specific config)
            
        Returns:
            Processed configuration with organization-specific values
        """
        base_config = self.load_app_config(app_type)
        
        # Process template values
        processed_config = self._process_config_templates(base_config, organization_id)
        
        return processed_config

    def _load_json_config(self, relative_path: str, cache_key: str) -> Dict[str, Any]:
        """
        Load JSON configuration with caching.
        
        Args:
            relative_path: Path relative to config_base_path
            cache_key: Key for caching the configuration
            
        Returns:
            Loaded configuration dictionary
        """
        # Check cache first
        if self._cache_enabled and cache_key in self._cache:
            return self._cache[cache_key].copy()

        file_path = self.config_base_path / relative_path
        
        try:
            if not file_path.exists():
                self.logger.warning(f"Configuration file not found: {file_path}")
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Cache the configuration
            if self._cache_enabled:
                self._cache[cache_key] = config.copy()
            
            self.logger.debug(f"Loaded configuration from {file_path}")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file {file_path}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading configuration from {file_path}: {e}")
            return {}

    def _process_config_templates(self, config: Dict[str, Any], organization_id: str) -> Dict[str, Any]:
        """
        Process template values in configuration.
        
        Args:
            config: Configuration dictionary that may contain templates
            organization_id: Organization ID for template processing
            
        Returns:
            Configuration with processed template values
        """
        processed_config = {}
        
        for key, value in config.items():
            if isinstance(value, dict):
                processed_config[key] = self._process_config_templates(value, organization_id)
            elif isinstance(value, list):
                processed_config[key] = [
                    self._process_config_templates(item, organization_id) if isinstance(item, dict) 
                    else self._process_template_string(item, organization_id) if isinstance(item, str)
                    else item
                    for item in value
                ]
            elif isinstance(value, str):
                processed_config[key] = self._process_template_string(value, organization_id)
            else:
                processed_config[key] = value
        
        return processed_config

    def _process_template_string(self, template: str, organization_id: str) -> str:
        """
        Process template strings with placeholders.
        
        Args:
            template: Template string that may contain placeholders
            organization_id: Organization ID for template processing
            
        Returns:
            Processed string with placeholders replaced
        """
        if template == "generated_uuid":
            return str(uuid4())
        elif "{organization_id}" in template:
            return template.replace("{organization_id}", organization_id)
        
        return template

    def reload_cache(self) -> None:
        """Clear cache to force reload of configurations."""
        self._cache.clear()
        self.logger.info("Configuration cache cleared")

    def disable_cache(self) -> None:
        """Disable configuration caching (useful for testing)."""
        self._cache_enabled = False
        self._cache.clear()

    def enable_cache(self) -> None:
        """Enable configuration caching."""
        self._cache_enabled = True

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        return {
            "cache_enabled": self._cache_enabled,
            "cached_configs": list(self._cache.keys()),
            "cache_size": len(self._cache),
            "config_base_path": str(self.config_base_path)
        }


# Global instance for easy access
_config_loader_instance: Optional[ConfigurationLoaderService] = None


def get_configuration_loader() -> ConfigurationLoaderService:
    """Get the global configuration loader instance."""
    global _config_loader_instance
    
    if _config_loader_instance is None:
        _config_loader_instance = ConfigurationLoaderService()
    
    return _config_loader_instance


def set_configuration_loader(loader: ConfigurationLoaderService) -> None:
    """Set a custom configuration loader instance (useful for testing)."""
    global _config_loader_instance
    _config_loader_instance = loader