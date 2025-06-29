from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ..entities.feature_usage import FeatureUsage, UsagePeriod


class FeatureUsageRepository(ABC):
    """Feature usage repository interface for the Plans bounded context."""

    @abstractmethod
    def save(self, feature_usage: FeatureUsage) -> FeatureUsage:
        """Save or update feature usage."""
        pass

    @abstractmethod
    def get_by_id(self, usage_id: UUID) -> Optional[FeatureUsage]:
        """Get feature usage by ID."""
        pass

    @abstractmethod
    def get_current_usage(
        self, organization_id: UUID, feature_name: str, period: UsagePeriod
    ) -> Optional[FeatureUsage]:
        """Get current usage for organization and feature."""
        pass

    @abstractmethod
    def get_organization_usage(
        self,
        organization_id: UUID,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> List[FeatureUsage]:
        """Get all usage records for an organization."""
        pass

    @abstractmethod
    def get_feature_usage_across_organizations(
        self,
        feature_name: str,
        period: UsagePeriod,
        period_start: Optional[datetime] = None,
    ) -> List[FeatureUsage]:
        """Get usage for a specific feature across all organizations."""
        pass

    @abstractmethod
    def get_organizations_exceeding_limit(
        self, feature_name: str, threshold_percent: float = 0.8
    ) -> List[UUID]:
        """Get organizations exceeding usage threshold for a feature."""
        pass

    @abstractmethod
    def increment_usage(
        self,
        organization_id: UUID,
        feature_name: str,
        amount: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeatureUsage:
        """Increment usage for organization and feature."""
        pass

    @abstractmethod
    def reset_usage_for_period(
        self, organization_id: UUID, feature_name: str, period: UsagePeriod
    ) -> bool:
        """Reset usage for new billing period."""
        pass

    @abstractmethod
    def delete(self, usage_id: UUID) -> bool:
        """Delete usage record by ID."""
        pass

    @abstractmethod
    def delete_old_records(self, older_than_days: int = 365) -> int:
        """Delete usage records older than specified days."""
        pass

    @abstractmethod
    def get_usage_summary(
        self, organization_id: UUID, period_start: datetime, period_end: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """Get usage summary for organization within period."""
        pass

    @abstractmethod
    def get_usage_trends(
        self, organization_id: UUID, feature_name: str, periods: int = 12
    ) -> List[Dict[str, Any]]:
        """Get usage trends for feature over specified periods."""
        pass

    @abstractmethod
    def bulk_reset_monthly_usage(self) -> int:
        """Reset monthly usage for all organizations at month end."""
        pass
