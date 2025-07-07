from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from decimal import Decimal

from ..entities.plan_resource_limit import PlanResourceLimit, LimitType, LimitUnit
from ..entities.plan_resource import ResourceCategory


class PlanResourceLimitService:
    """Domain service for managing plan resource limits and their business logic."""

    def create_limit(
        self,
        resource_id: UUID,
        limit_key: str,
        limit_name: str,
        limit_type: LimitType,
        default_value: Optional[int] = None,
        unit: Optional[LimitUnit] = None,
        description: Optional[str] = None,
    ) -> PlanResourceLimit:
        """Create a new resource limit with validation."""
        
        # Validate limit key format
        if not self._is_valid_limit_key(limit_key):
            raise ValueError(
                "Limit key must be alphanumeric with underscores/hyphens, 3-100 characters"
            )
        
        # Validate limit key uniqueness for the resource
        if self._is_limit_key_taken_for_resource(resource_id, limit_key):
            raise ValueError(f"Limit key '{limit_key}' already exists for this resource")
        
        # Validate business rules
        self._validate_limit_creation_rules(limit_key, limit_type, default_value, unit)
        
        return PlanResourceLimit.create(
            resource_id=resource_id,
            limit_key=limit_key,
            limit_name=limit_name,
            limit_type=limit_type,
            default_value=default_value,
            unit=unit,
            description=description,
        )

    def validate_limit_type_compatibility(
        self, limit_type: LimitType, unit: Optional[LimitUnit], resource_category: ResourceCategory
    ) -> tuple[bool, List[str]]:
        """Validate limit type and unit compatibility."""
        
        issues = []
        
        # Type-Unit compatibility rules
        type_unit_rules = {
            LimitType.COUNT: [
                LimitUnit.TOTAL, LimitUnit.PER_DAY, LimitUnit.PER_MONTH, 
                LimitUnit.PER_HOUR, LimitUnit.PER_MINUTE
            ],
            LimitType.SIZE: [
                LimitUnit.BYTES, LimitUnit.KB, LimitUnit.MB, LimitUnit.GB, LimitUnit.TB
            ],
            LimitType.RATE: [
                LimitUnit.REQUESTS_PER_SECOND, LimitUnit.REQUESTS_PER_MINUTE, 
                LimitUnit.REQUESTS_PER_HOUR
            ],
            LimitType.DURATION: [
                LimitUnit.SECONDS, LimitUnit.MINUTES, LimitUnit.HOURS, LimitUnit.DAYS
            ],
            LimitType.CONCURRENT: [LimitUnit.TOTAL],
            LimitType.STORAGE: [
                LimitUnit.BYTES, LimitUnit.KB, LimitUnit.MB, LimitUnit.GB, LimitUnit.TB
            ],
        }
        
        if unit and limit_type in type_unit_rules:
            if unit not in type_unit_rules[limit_type]:
                issues.append(
                    f"Unit '{unit.value}' is not compatible with limit type '{limit_type.value}'"
                )
        
        # Category-Type compatibility
        category_type_rules = {
            ResourceCategory.MESSAGING: [
                LimitType.COUNT, LimitType.RATE, LimitType.CONCURRENT
            ],
            ResourceCategory.ANALYTICS: [
                LimitType.COUNT, LimitType.STORAGE, LimitType.DURATION
            ],
            ResourceCategory.STORAGE: [
                LimitType.SIZE, LimitType.STORAGE, LimitType.COUNT
            ],
            ResourceCategory.INTEGRATION: [
                LimitType.RATE, LimitType.COUNT, LimitType.CONCURRENT
            ],
        }
        
        if limit_type not in category_type_rules.get(resource_category, []):
            issues.append(
                f"Limit type '{limit_type.value}' is unusual for {resource_category.value} resources"
            )
        
        return len(issues) == 0, issues

    def calculate_effective_limit(
        self,
        base_limit: PlanResourceLimit,
        override_value: Optional[int] = None,
        plan_multiplier: float = 1.0,
    ) -> Dict[str, Any]:
        """Calculate the effective limit considering overrides and multipliers."""
        
        # Start with base limit
        effective_value = base_limit.default_value
        
        # Apply override if provided
        if override_value is not None:
            effective_value = override_value
        
        # Apply plan multiplier
        if effective_value is not None and effective_value != -1:  # -1 = unlimited
            effective_value = int(effective_value * plan_multiplier)
        
        # Validate the final value
        is_valid, validation_message = base_limit.validate_value(effective_value) if effective_value is not None else (True, "")
        
        return {
            "limit_id": str(base_limit.id),
            "limit_key": base_limit.limit_key,
            "limit_name": base_limit.limit_name,
            "base_value": base_limit.default_value,
            "override_value": override_value,
            "plan_multiplier": plan_multiplier,
            "effective_value": effective_value,
            "is_unlimited": effective_value == -1,
            "unit": base_limit.unit.value if base_limit.unit else None,
            "limit_type": base_limit.limit_type.value,
            "is_valid": is_valid,
            "validation_message": validation_message,
            "display_value": self._format_limit_display(effective_value, base_limit.unit),
        }

    def get_recommended_limits_for_resource(
        self, resource_type: str, resource_category: ResourceCategory, plan_tier: str
    ) -> List[Dict[str, Any]]:
        """Get recommended limits for a specific resource type and plan tier."""
        
        recommendations = []
        
        # Category-based recommendations
        if resource_category == ResourceCategory.MESSAGING:
            recommendations.extend([
                {
                    "limit_key": "messages_per_month",
                    "limit_name": "Monthly Message Limit",
                    "limit_type": LimitType.COUNT,
                    "unit": LimitUnit.PER_MONTH,
                    "default_values": {
                        "basic": 1000,
                        "premium": 10000,
                        "enterprise": -1  # unlimited
                    },
                    "priority": "high",
                    "description": "Maximum messages that can be sent per month"
                },
                {
                    "limit_key": "concurrent_sessions",
                    "limit_name": "Concurrent Sessions",
                    "limit_type": LimitType.CONCURRENT,
                    "unit": LimitUnit.TOTAL,
                    "default_values": {
                        "basic": 25,
                        "premium": 100,
                        "enterprise": 500
                    },
                    "priority": "medium",
                    "description": "Maximum simultaneous active conversations"
                }
            ])
        
        elif resource_category == ResourceCategory.ANALYTICS:
            recommendations.extend([
                {
                    "limit_key": "report_generation_per_day",
                    "limit_name": "Daily Report Generation",
                    "limit_type": LimitType.COUNT,
                    "unit": LimitUnit.PER_DAY,
                    "default_values": {
                        "basic": 5,
                        "premium": 50,
                        "enterprise": 200
                    },
                    "priority": "medium",
                    "description": "Number of reports that can be generated daily"
                },
                {
                    "limit_key": "data_retention_days",
                    "limit_name": "Data Retention Period",
                    "limit_type": LimitType.DURATION,
                    "unit": LimitUnit.DAYS,
                    "default_values": {
                        "basic": 30,
                        "premium": 365,
                        "enterprise": -1  # unlimited
                    },
                    "priority": "high",
                    "description": "How long analytics data is retained"
                }
            ])
        
        elif resource_category == ResourceCategory.STORAGE:
            recommendations.extend([
                {
                    "limit_key": "storage_quota",
                    "limit_name": "Storage Quota",
                    "limit_type": LimitType.STORAGE,
                    "unit": LimitUnit.GB,
                    "default_values": {
                        "basic": 5,
                        "premium": 100,
                        "enterprise": 1000
                    },
                    "priority": "high",
                    "description": "Total storage space available"
                },
                {
                    "limit_key": "file_upload_size",
                    "limit_name": "Maximum File Upload Size",
                    "limit_type": LimitType.SIZE,
                    "unit": LimitUnit.MB,
                    "default_values": {
                        "basic": 10,
                        "premium": 100,
                        "enterprise": 500
                    },
                    "priority": "medium",
                    "description": "Maximum size for individual file uploads"
                }
            ])
        
        elif resource_category == ResourceCategory.INTEGRATION:
            recommendations.extend([
                {
                    "limit_key": "api_requests_per_minute",
                    "limit_name": "API Request Rate Limit",
                    "limit_type": LimitType.RATE,
                    "unit": LimitUnit.REQUESTS_PER_MINUTE,
                    "default_values": {
                        "basic": 60,
                        "premium": 600,
                        "enterprise": 6000
                    },
                    "priority": "high",
                    "description": "Maximum API requests per minute"
                },
                {
                    "limit_key": "webhook_endpoints",
                    "limit_name": "Webhook Endpoints",
                    "limit_type": LimitType.COUNT,
                    "unit": LimitUnit.TOTAL,
                    "default_values": {
                        "basic": 2,
                        "premium": 10,
                        "enterprise": 50
                    },
                    "priority": "medium",
                    "description": "Number of webhook endpoints allowed"
                }
            ])
        
        # Apply plan tier values
        for recommendation in recommendations:
            recommendation["default_value"] = recommendation["default_values"].get(plan_tier, 0)
        
        return recommendations

    def analyze_limit_utilization(
        self, current_usage: int, limit_value: int, limit_type: LimitType
    ) -> Dict[str, Any]:
        """Analyze limit utilization and provide insights."""
        
        if limit_value == -1:  # unlimited
            utilization_percent = 0.0
            status = "unlimited"
        elif limit_value == 0:
            utilization_percent = 100.0 if current_usage > 0 else 0.0
            status = "no_limit"
        else:
            utilization_percent = (current_usage / limit_value) * 100
            
            if utilization_percent >= 100:
                status = "exceeded"
            elif utilization_percent >= 90:
                status = "critical"
            elif utilization_percent >= 75:
                status = "warning"
            elif utilization_percent >= 50:
                status = "moderate"
            else:
                status = "healthy"
        
        remaining = max(0, limit_value - current_usage) if limit_value != -1 else -1
        
        return {
            "current_usage": current_usage,
            "limit_value": limit_value,
            "utilization_percent": round(utilization_percent, 2),
            "remaining": remaining,
            "status": status,
            "is_unlimited": limit_value == -1,
            "recommendations": self._get_utilization_recommendations(status, utilization_percent)
        }

    def suggest_limit_optimizations(
        self, limits: List[PlanResourceLimit], usage_data: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Suggest optimizations for resource limits based on usage data."""
        
        suggestions = []
        
        for limit in limits:
            current_usage = usage_data.get(limit.limit_key, 0)
            utilization = self.analyze_limit_utilization(
                current_usage, limit.default_value or 0, limit.limit_type
            )
            
            # Suggest increases for high utilization
            if utilization["status"] in ["critical", "exceeded"]:
                suggestions.append({
                    "type": "increase_limit",
                    "priority": "high",
                    "limit_key": limit.limit_key,
                    "current_value": limit.default_value,
                    "suggested_value": self._calculate_suggested_increase(
                        limit.default_value, current_usage, limit.limit_type
                    ),
                    "reason": f"Current utilization is {utilization['utilization_percent']:.1f}%",
                    "impact": "Prevents limit-related service interruptions"
                })
            
            # Suggest decreases for consistently low utilization
            elif utilization["status"] == "healthy" and utilization["utilization_percent"] < 10:
                if current_usage > 0:  # Only if there's some usage
                    suggestions.append({
                        "type": "decrease_limit",
                        "priority": "low",
                        "limit_key": limit.limit_key,
                        "current_value": limit.default_value,
                        "suggested_value": self._calculate_suggested_decrease(
                            limit.default_value, current_usage, limit.limit_type
                        ),
                        "reason": f"Low utilization at {utilization['utilization_percent']:.1f}%",
                        "impact": "Cost optimization without affecting functionality"
                    })
        
        return suggestions

    def convert_limit_units(
        self, value: int, from_unit: LimitUnit, to_unit: LimitUnit
    ) -> Optional[int]:
        """Convert limit values between different units."""
        
        # Size conversions
        size_conversions = {
            LimitUnit.BYTES: 1,
            LimitUnit.KB: 1024,
            LimitUnit.MB: 1024 * 1024,
            LimitUnit.GB: 1024 * 1024 * 1024,
            LimitUnit.TB: 1024 * 1024 * 1024 * 1024,
        }
        
        # Time conversions (to seconds)
        time_conversions = {
            LimitUnit.SECONDS: 1,
            LimitUnit.MINUTES: 60,
            LimitUnit.HOURS: 3600,
            LimitUnit.DAYS: 86400,
        }
        
        # Rate conversions (to requests per second)
        rate_conversions = {
            LimitUnit.REQUESTS_PER_SECOND: 1,
            LimitUnit.REQUESTS_PER_MINUTE: 1/60,
            LimitUnit.REQUESTS_PER_HOUR: 1/3600,
        }
        
        # Choose appropriate conversion table
        if from_unit in size_conversions and to_unit in size_conversions:
            base_value = value * size_conversions[from_unit]
            return int(base_value / size_conversions[to_unit])
        
        elif from_unit in time_conversions and to_unit in time_conversions:
            base_value = value * time_conversions[from_unit]
            return int(base_value / time_conversions[to_unit])
        
        elif from_unit in rate_conversions and to_unit in rate_conversions:
            base_value = value * rate_conversions[from_unit]
            return int(base_value / rate_conversions[to_unit])
        
        # No conversion possible
        return None

    def _is_valid_limit_key(self, limit_key: str) -> bool:
        """Validate limit key format."""
        if not limit_key or len(limit_key) < 3 or len(limit_key) > 100:
            return False
        
        # Only alphanumeric, underscores, and hyphens
        return limit_key.replace("_", "").replace("-", "").isalnum()

    def _is_limit_key_taken_for_resource(self, resource_id: UUID, limit_key: str) -> bool:
        """Check if limit key is already used for the resource."""
        # This would typically check against a limit repository
        # For now, return False to allow creation
        return False

    def _validate_limit_creation_rules(
        self,
        limit_key: str,
        limit_type: LimitType,
        default_value: Optional[int],
        unit: Optional[LimitUnit],
    ) -> None:
        """Validate limit creation business rules."""
        
        # Value validation
        if default_value is not None and default_value < -1:
            raise ValueError("Limit value must be -1 (unlimited) or non-negative")
        
        # Type-specific validation
        if limit_type == LimitType.RATE and (default_value is None or default_value <= 0):
            raise ValueError("Rate limits must have positive values")
        
        if limit_type == LimitType.SIZE and unit is None:
            raise ValueError("Size limits must specify a unit")
        
        if limit_type == LimitType.DURATION and unit is None:
            raise ValueError("Duration limits must specify a unit")

    def _format_limit_display(self, value: Optional[int], unit: Optional[LimitUnit]) -> str:
        """Format limit value for display."""
        if value is None:
            return "Not set"
        
        if value == -1:
            return "Unlimited"
        
        if unit:
            return f"{value:,} {unit.value}"
        
        return f"{value:,}"

    def _get_utilization_recommendations(self, status: str, utilization_percent: float) -> List[str]:
        """Get recommendations based on utilization status."""
        
        recommendations = []
        
        if status == "exceeded":
            recommendations.extend([
                "Immediate action required - limit has been exceeded",
                "Consider upgrading plan or requesting limit increase",
                "Review usage patterns to optimize consumption"
            ])
        
        elif status == "critical":
            recommendations.extend([
                "Approaching limit - monitor usage closely",
                "Plan for limit increase or usage optimization",
                "Set up alerts for usage monitoring"
            ])
        
        elif status == "warning":
            recommendations.extend([
                "Usage is moderately high - consider future planning",
                "Monitor trends to predict when limit might be reached"
            ])
        
        elif status == "healthy" and utilization_percent < 10:
            recommendations.extend([
                "Usage is very low - consider if limit can be reduced",
                "Limit may be over-provisioned for current needs"
            ])
        
        return recommendations

    def _calculate_suggested_increase(
        self, current_limit: Optional[int], current_usage: int, limit_type: LimitType
    ) -> int:
        """Calculate suggested limit increase."""
        
        if current_limit is None or current_limit <= 0:
            return current_usage * 2
        
        # Increase by 50-100% depending on type
        if limit_type in [LimitType.RATE, LimitType.CONCURRENT]:
            # For rate and concurrency, be more conservative
            multiplier = 1.5
        else:
            # For storage and count, can be more generous
            multiplier = 2.0
        
        return max(int(current_usage * multiplier), current_limit * 2)

    def _calculate_suggested_decrease(
        self, current_limit: Optional[int], current_usage: int, limit_type: LimitType
    ) -> int:
        """Calculate suggested limit decrease."""
        
        if current_limit is None or current_limit <= 0:
            return current_usage * 2  # Provide some buffer
        
        # Set to 2-3x current usage to provide buffer
        buffer_multiplier = 3 if limit_type in [LimitType.RATE, LimitType.CONCURRENT] else 2
        suggested = current_usage * buffer_multiplier
        
        # Don't decrease below a reasonable minimum
        minimum_value = 1 if limit_type == LimitType.COUNT else 10
        
        return max(suggested, minimum_value)