from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..entities.plan_configuration import PlanConfiguration


class PlanConfigurationRepository(ABC):
    """Plan configuration repository interface for the Plans bounded context."""

    @abstractmethod
    def save(self, plan_configuration: PlanConfiguration) -> PlanConfiguration:
        """Save or update a plan configuration."""
        pass

    @abstractmethod
    def get_by_id(self, configuration_id: UUID) -> Optional[PlanConfiguration]:
        """Get plan configuration by ID."""
        pass

    @abstractmethod
    def get_by_plan_id(self, plan_id: UUID) -> Optional[PlanConfiguration]:
        """Get configuration for a plan."""
        pass

    @abstractmethod
    def get_active_configurations(self) -> List[PlanConfiguration]:
        """Get all active plan configurations."""
        pass

    @abstractmethod
    def delete(self, configuration_id: UUID) -> bool:
        """Delete plan configuration by ID."""
        pass

    @abstractmethod
    def delete_by_plan_id(self, plan_id: UUID) -> bool:
        """Delete configuration for a plan."""
        pass

    @abstractmethod
    def exists_by_plan_id(self, plan_id: UUID) -> bool:
        """Check if plan has configuration."""
        pass

    @abstractmethod
    def update_api_keys(
        self, configuration_id: UUID, api_keys: Dict[str, str]
    ) -> Optional[PlanConfiguration]:
        """Update API keys in configuration."""
        pass

    @abstractmethod
    def update_limits(
        self, configuration_id: UUID, limits: Dict[str, int]
    ) -> Optional[PlanConfiguration]:
        """Update limits in configuration."""
        pass

    @abstractmethod
    def update_enabled_features(
        self, configuration_id: UUID, enabled_features: List[str]
    ) -> Optional[PlanConfiguration]:
        """Update enabled features in configuration."""
        pass

    @abstractmethod
    def activate_configuration(self, configuration_id: UUID) -> bool:
        """Activate a configuration."""
        pass

    @abstractmethod
    def deactivate_configuration(self, configuration_id: UUID) -> bool:
        """Deactivate a configuration."""
        pass

    @abstractmethod
    def list_configurations(
        self, is_active: Optional[bool] = None, limit: int = 100, offset: int = 0
    ) -> List[PlanConfiguration]:
        """List plan configurations with filtering and pagination."""
        pass

    @abstractmethod
    def count_configurations(self, is_active: Optional[bool] = None) -> int:
        """Count plan configurations with optional filtering."""
        pass

    @abstractmethod
    def get_configurations_with_feature(
        self, feature_name: str
    ) -> List[PlanConfiguration]:
        """Get configurations that have a specific feature enabled."""
        pass

    @abstractmethod
    def get_configurations_with_api_key(
        self, api_key_name: str
    ) -> List[PlanConfiguration]:
        """Get configurations that have a specific API key."""
        pass

    @abstractmethod
    def validate_api_key_uniqueness(
        self,
        api_key_name: str,
        api_key_value: str,
        excluding_configuration_id: Optional[UUID] = None,
    ) -> bool:
        """Check if API key value is unique across configurations."""
        pass

    @abstractmethod
    def bulk_update_configurations(
        self, updates: List[Dict[str, Any]]
    ) -> List[PlanConfiguration]:
        """Bulk update multiple configurations."""
        pass
