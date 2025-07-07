from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LimitType(str, Enum):
    COUNT = "count"
    SIZE = "size"
    RATE = "rate"
    DURATION = "duration"
    CONCURRENT = "concurrent"
    STORAGE = "storage"


class LimitUnit(str, Enum):
    # Count units
    PER_MONTH = "per_month"
    PER_DAY = "per_day"
    PER_HOUR = "per_hour"
    PER_MINUTE = "per_minute"
    TOTAL = "total"
    
    # Size units
    BYTES = "bytes"
    KB = "KB"
    MB = "MB"
    GB = "GB"
    TB = "TB"
    
    # Rate units
    REQUESTS_PER_SECOND = "requests_per_second"
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    
    # Duration units
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class PlanResourceLimit(BaseModel):
    id: UUID
    resource_id: UUID
    limit_key: str = Field(..., min_length=1, max_length=100)
    limit_name: str = Field(..., min_length=1, max_length=200)
    limit_type: LimitType
    default_value: Optional[int] = None
    unit: Optional[LimitUnit] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        resource_id: UUID,
        limit_key: str,
        limit_name: str,
        limit_type: LimitType,
        default_value: Optional[int] = None,
        unit: Optional[LimitUnit] = None,
        description: Optional[str] = None,
    ) -> "PlanResourceLimit":
        """Create a new plan resource limit."""
        now = datetime.utcnow()
        
        return cls(
            id=uuid4(),
            resource_id=resource_id,
            limit_key=limit_key,
            limit_name=limit_name,
            limit_type=limit_type,
            default_value=default_value,
            unit=unit,
            description=description,
            created_at=now,
        )

    def update_name(self, limit_name: str) -> "PlanResourceLimit":
        """Update the limit name."""
        if not limit_name or len(limit_name) < 1 or len(limit_name) > 200:
            raise ValueError("Limit name must be between 1 and 200 characters")
        
        return self.model_copy(
            update={
                "limit_name": limit_name,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_description(self, description: str) -> "PlanResourceLimit":
        """Update the limit description."""
        return self.model_copy(
            update={
                "description": description,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_default_value(self, default_value: Optional[int]) -> "PlanResourceLimit":
        """Update the default limit value."""
        if default_value is not None and default_value < 0:
            raise ValueError("Default value cannot be negative. Use None for unlimited.")
        
        return self.model_copy(
            update={
                "default_value": default_value,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_unit(self, unit: Optional[LimitUnit]) -> "PlanResourceLimit":
        """Update the limit unit."""
        return self.model_copy(
            update={
                "unit": unit,
                "updated_at": datetime.utcnow(),
            }
        )

    def validate_limit_key(self) -> tuple[bool, str]:
        """Validate the limit key format."""
        if not self.limit_key:
            return False, "Limit key cannot be empty"
        
        if len(self.limit_key) < 1 or len(self.limit_key) > 100:
            return False, "Limit key must be between 1 and 100 characters"
        
        # Basic alphanumeric and underscore validation
        if not self.limit_key.replace("_", "").replace("-", "").isalnum():
            return False, "Limit key can only contain letters, numbers, underscores, and hyphens"
        
        return True, "Limit key is valid"

    def is_unlimited(self) -> bool:
        """Check if this limit represents unlimited usage."""
        return self.default_value is None or self.default_value == -1

    def is_count_based(self) -> bool:
        """Check if this is a count-based limit."""
        return self.limit_type == LimitType.COUNT

    def is_size_based(self) -> bool:
        """Check if this is a size-based limit."""
        return self.limit_type == LimitType.SIZE

    def is_rate_based(self) -> bool:
        """Check if this is a rate-based limit."""
        return self.limit_type == LimitType.RATE

    def is_duration_based(self) -> bool:
        """Check if this is a duration-based limit."""
        return self.limit_type == LimitType.DURATION

    def get_limit_identifier(self) -> str:
        """Get a unique identifier for this limit."""
        return f"{self.resource_id}:{self.limit_key}"

    def get_display_value(self) -> str:
        """Get formatted display value with unit."""
        if self.is_unlimited():
            return "Unlimited"
        
        value_str = str(self.default_value)
        if self.unit:
            return f"{value_str} {self.unit.value}"
        
        return value_str

    def get_display_name(self) -> str:
        """Get formatted display name with value."""
        return f"{self.limit_name}: {self.get_display_value()}"

    def validate_value(self, value: int) -> tuple[bool, str]:
        """Validate a proposed limit value."""
        if value < 0:
            return False, "Limit value cannot be negative"
        
        # Type-specific validations
        if self.limit_type == LimitType.RATE and value > 10000:
            return False, "Rate limits should not exceed 10,000 requests per unit"
        
        if self.limit_type == LimitType.SIZE and value > 1000000000:  # 1GB in MB
            return False, "Size limits should not exceed 1TB"
        
        return True, "Limit value is valid"

    def create_limit_config(self, limit_value: int, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a limit configuration dict."""
        return {
            "limit_id": str(self.id),
            "limit_key": self.limit_key,
            "limit_name": self.limit_name,
            "limit_type": self.limit_type.value,
            "limit_value": limit_value,
            "unit": self.unit.value if self.unit else None,
            "is_unlimited": limit_value == -1,
            "custom_config": custom_config or {},
        }

    def get_limit_summary(self) -> Dict[str, Any]:
        """Get a summary of the limit."""
        return {
            "id": str(self.id),
            "resource_id": str(self.resource_id),
            "limit_key": self.limit_key,
            "limit_name": self.limit_name,
            "limit_type": self.limit_type.value,
            "default_value": self.default_value,
            "unit": self.unit.value if self.unit else None,
            "description": self.description,
            "is_unlimited": self.is_unlimited(),
            "limit_identifier": self.get_limit_identifier(),
            "display_name": self.get_display_name(),
            "display_value": self.get_display_value(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }