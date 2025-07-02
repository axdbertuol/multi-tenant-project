from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class UsagePeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class FeatureUsage(BaseModel):
    id: UUID
    organization_id: UUID
    feature_name: str
    usage_period: UsagePeriod
    period_start: datetime
    period_end: datetime
    current_usage: int
    limit_value: int  # -1 for unlimited
    metadata: Dict[str, Any]  # Additional usage data
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        feature_name: str,
        usage_period: UsagePeriod,
        limit_value: int,
        current_usage: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "FeatureUsage":
        now = datetime.utcnow()
        period_start, period_end = cls._calculate_period_boundaries(now, usage_period)

        return cls(
            id=uuid4(),
            organization_id=organization_id,
            feature_name=feature_name,
            usage_period=usage_period,
            period_start=period_start,
            period_end=period_end,
            current_usage=current_usage,
            limit_value=limit_value,
            metadata=metadata or {},
            created_at=now,
        )

    @staticmethod
    def _calculate_period_boundaries(
        date: datetime, period: UsagePeriod
    ) -> tuple[datetime, datetime]:
        """Calculate period start and end dates."""
        if period == UsagePeriod.DAILY:
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1) - timedelta(microseconds=1)

        elif period == UsagePeriod.WEEKLY:
            # Start on Monday
            days_since_monday = date.weekday()
            start = (date - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end = start + timedelta(days=7) - timedelta(microseconds=1)

        elif period == UsagePeriod.MONTHLY:
            start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1) - timedelta(
                    microseconds=1
                )
            else:
                end = start.replace(month=start.month + 1) - timedelta(microseconds=1)

        elif period == UsagePeriod.YEARLY:
            start = date.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end = start.replace(year=start.year + 1) - timedelta(microseconds=1)

        else:
            raise ValueError(f"Unsupported usage period: {period}")

        return start, end

    def increment_usage(
        self, amount: int = 1, metadata_update: Optional[Dict[str, Any]] = None
    ) -> "FeatureUsage":
        """Increment usage counter."""
        new_metadata = self.metadata.copy()
        if metadata_update:
            new_metadata.update(metadata_update)

        return self.model_copy(
            update={
                "current_usage": self.current_usage + amount,
                "metadata": new_metadata,
                "updated_at": datetime.utcnow(),
            }
        )

    def reset_usage(self) -> "FeatureUsage":
        """Reset usage counter for new period."""
        now = datetime.utcnow()
        period_start, period_end = self._calculate_period_boundaries(
            now, self.usage_period
        )

        return self.model_copy(
            update={
                "current_usage": 0,
                "period_start": period_start,
                "period_end": period_end,
                "metadata": {},
                "updated_at": now,
            }
        )

    def update_limit(self, new_limit: int) -> "FeatureUsage":
        """Update usage limit."""
        return self.model_copy(
            update={"limit_value": new_limit, "updated_at": datetime.utcnow()}
        )

    def is_unlimited(self) -> bool:
        """Check if feature has unlimited usage."""
        return self.limit_value == -1

    def is_limit_exceeded(self) -> bool:
        """Check if usage limit is exceeded."""
        if self.is_unlimited():
            return False

        return self.current_usage >= self.limit_value

    def is_limit_near(self, threshold_percent: float = 0.8) -> bool:
        """Check if usage is near the limit."""
        if self.is_unlimited():
            return False

        threshold = int(self.limit_value * threshold_percent)
        return self.current_usage >= threshold

    def get_usage_percentage(self) -> float:
        """Get usage as percentage of limit."""
        if self.is_unlimited():
            return 0.0

        if self.limit_value == 0:
            return 100.0 if self.current_usage > 0 else 0.0

        return (self.current_usage / self.limit_value) * 100

    def get_remaining_usage(self) -> int:
        """Get remaining usage before hitting limit."""
        if self.is_unlimited():
            return -1  # Unlimited

        return max(0, self.limit_value - self.current_usage)

    def is_current_period(self) -> bool:
        """Check if this record is for the current period."""
        now = datetime.utcnow()
        return self.period_start <= now <= self.period_end

    def is_period_expired(self) -> bool:
        """Check if the usage period has expired."""
        return datetime.utcnow() > self.period_end

    def days_until_reset(self) -> int:
        """Get days until usage resets."""
        if self.is_period_expired():
            return 0

        delta = self.period_end - datetime.utcnow()
        return max(0, delta.days + 1)  # +1 to include current day

    def can_use_feature(self, amount: int = 1) -> tuple[bool, str]:
        """Check if feature can be used given the amount."""
        if self.is_period_expired():
            return False, "Usage period has expired"

        if self.is_unlimited():
            return True, "Feature has unlimited usage"

        if self.current_usage + amount > self.limit_value:
            remaining = self.get_remaining_usage()
            return (
                False,
                f"Would exceed limit. Remaining: {remaining}, Requested: {amount}",
            )

        return True, "Usage within limits"

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive usage summary."""
        return {
            "feature_name": self.feature_name,
            "current_usage": self.current_usage,
            "limit_value": self.limit_value,
            "is_unlimited": self.is_unlimited(),
            "usage_percentage": self.get_usage_percentage(),
            "remaining_usage": self.get_remaining_usage(),
            "is_limit_exceeded": self.is_limit_exceeded(),
            "is_limit_near": self.is_limit_near(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "days_until_reset": self.days_until_reset(),
            "is_current_period": self.is_current_period(),
        }
