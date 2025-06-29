from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.plan_feature import PlanFeature, FeatureCategory, FeatureType


class PlanFeatureRepository(ABC):
    """Plan feature repository interface for the Plans bounded context."""

    @abstractmethod
    def save(self, feature: PlanFeature) -> PlanFeature:
        """Save or update a plan feature."""
        pass

    @abstractmethod
    def get_by_id(self, feature_id: UUID) -> Optional[PlanFeature]:
        """Get feature by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[PlanFeature]:
        """Get feature by name."""
        pass

    @abstractmethod
    def get_by_category(self, category: FeatureCategory) -> List[PlanFeature]:
        """Get features by category."""
        pass

    @abstractmethod
    def get_by_type(self, feature_type: FeatureType) -> List[PlanFeature]:
        """Get features by type."""
        pass

    @abstractmethod
    def get_active_features(self) -> List[PlanFeature]:
        """Get all active features."""
        pass

    @abstractmethod
    def get_system_features(self) -> List[PlanFeature]:
        """Get all system features."""
        pass

    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """Check if feature exists by name."""
        pass

    @abstractmethod
    def delete(self, feature_id: UUID) -> bool:
        """Delete feature by ID."""
        pass

    @abstractmethod
    def list_features(
        self,
        category: Optional[FeatureCategory] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PlanFeature]:
        """List features with filtering and pagination."""
        pass

    @abstractmethod
    def search_features(self, query: str, limit: int = 100) -> List[PlanFeature]:
        """Search features by name or description."""
        pass

    @abstractmethod
    def count_features(
        self,
        category: Optional[FeatureCategory] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count features with optional filtering."""
        pass
