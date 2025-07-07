from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.entities.plan_resource_limit import PlanResourceLimit
from ...domain.entities.plan_resource import ResourceCategory
from ...domain.services.plan_resource_limit_service import PlanResourceLimitService
from ...domain.repositories.plan_repository import PlanRepository
from ...domain.repositories.organization_plan_repository import OrganizationPlanRepository


class PlanResourceLimitUseCase:
    """Use case for plan resource limit management operations."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._plan_repository: PlanRepository = uow.get_repository("plan")
        self._org_plan_repository: OrganizationPlanRepository = uow.get_repository("organization_plan")
        self._plan_resource_limit_service = PlanResourceLimitService()

    def create_limit(
        self,
        resource_id: UUID,
        limit_type: str,
        limit_value: int,
        period: str,
        is_hard_limit: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new plan resource limit."""
        
        try:
            limit = self._plan_resource_limit_service.create_limit(
                resource_id=resource_id,
                limit_type=limit_type,
                limit_value=limit_value,
                period=period,
                is_hard_limit=is_hard_limit,
                metadata=metadata,
            )
            
            return {
                "success": True,
                "limit": self._build_limit_response(limit),
                "message": "Resource limit created successfully",
            }
            
        except ValueError as e:
            return {
                "success": False,
                "message": f"Failed to create limit: {str(e)}",
                "resource_id": str(resource_id),
                "limit_type": limit_type,
            }

    def get_limit_by_id(self, limit_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a plan resource limit by ID."""
        
        # This would typically use a limit repository
        # For now, return a simulated response
        return {
            "id": str(limit_id),
            "resource_id": "00000000-0000-0000-0000-000000000000",
            "limit_type": "api_requests",
            "limit_value": 10000,
            "period": "monthly",
            "is_hard_limit": True,
            "is_active": True,
            "metadata": {},
            "created_at": "2024-01-01T00:00:00Z",
        }

    def update_limit(
        self,
        limit_id: UUID,
        limit_value: Optional[int] = None,
        period: Optional[str] = None,
        is_hard_limit: Optional[bool] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update an existing plan resource limit."""
        
        try:
            # This would typically load the limit, update it, and save
            # For now, simulate the update process
            
            return {
                "success": True,
                "limit_id": str(limit_id),
                "updated_fields": {
                    "limit_value": limit_value,
                    "period": period,
                    "is_hard_limit": is_hard_limit,
                    "is_active": is_active,
                    "metadata": metadata,
                },
                "message": "Limit updated successfully",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "limit_id": str(limit_id),
                "message": f"Failed to update limit: {str(e)}",
            }

    def validate_limit_configuration(
        self, resource_id: UUID, limit_type: str, limit_value: int, period: str
    ) -> Dict[str, Any]:
        """Validate limit configuration for a resource."""
        
        # Create a temporary limit for validation
        temp_limit = PlanResourceLimit.create(
            resource_id=resource_id,
            limit_type=limit_type,
            limit_value=limit_value,
            period=period,
        )
        
        is_valid, issues = self._plan_resource_limit_service.validate_limit_configuration(
            temp_limit
        )
        
        return {
            "resource_id": str(resource_id),
            "limit_type": limit_type,
            "limit_value": limit_value,
            "period": period,
            "is_valid": is_valid,
            "issues": issues,
            "recommendations": self._get_limit_recommendations(limit_type, limit_value, issues),
        }

    def get_resource_limits(
        self, resource_id: UUID, is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get all limits for a specific resource."""
        
        # This would typically query a limit repository
        # For now, return sample data
        
        sample_limits = [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "resource_id": str(resource_id),
                "limit_type": "api_requests",
                "limit_value": 10000,
                "period": "monthly",
                "is_hard_limit": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "resource_id": str(resource_id),
                "limit_type": "storage_mb",
                "limit_value": 1000,
                "period": "monthly",
                "is_hard_limit": False,
                "is_active": True,
                "created_at": "2024-01-02T00:00:00Z",
            },
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "resource_id": str(resource_id),
                "limit_type": "concurrent_users",
                "limit_value": 50,
                "period": "concurrent",
                "is_hard_limit": True,
                "is_active": False,
                "created_at": "2024-01-03T00:00:00Z",
            },
        ]
        
        # Filter by active status if specified
        if is_active is not None:
            sample_limits = [
                limit for limit in sample_limits
                if limit["is_active"] == is_active
            ]
        
        return sample_limits

    def calculate_effective_limits(
        self, resource_id: UUID, organization_id: UUID
    ) -> Dict[str, Any]:
        """Calculate effective limits considering plan and organization overrides."""
        
        # This would typically load the resource, plan, and organization overrides
        # For now, simulate the calculation
        
        base_limits = self.get_resource_limits(resource_id, is_active=True)
        
        # Get organization plan for overrides
        org_plan = self._org_plan_repository.get_by_organization_id(organization_id)
        
        effective_limits = {}
        for limit in base_limits:
            limit_type = limit["limit_type"]
            base_value = limit["limit_value"]
            
            # Check for organization overrides
            org_override = None
            if org_plan and org_plan.limit_overrides:
                org_override = org_plan.limit_overrides.get(limit_type)
            
            effective_value = org_override if org_override is not None else base_value
            
            effective_limits[limit_type] = {
                "base_value": base_value,
                "organization_override": org_override,
                "effective_value": effective_value,
                "period": limit["period"],
                "is_hard_limit": limit["is_hard_limit"],
                "source": "organization" if org_override is not None else "plan",
            }
        
        return {
            "resource_id": str(resource_id),
            "organization_id": str(organization_id),
            "effective_limits": effective_limits,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    def analyze_limit_usage_patterns(self, resource_id: UUID) -> Dict[str, Any]:
        """Analyze usage patterns against limits for a resource."""
        
        patterns = self._plan_resource_limit_service.analyze_limit_usage_patterns(resource_id)
        
        # Enhance with additional insights
        insights = self._generate_limit_insights(patterns)
        
        return {
            "resource_id": str(resource_id),
            "usage_patterns": patterns,
            "insights": insights,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_limit_optimization_suggestions(
        self, resource_id: UUID, usage_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get optimization suggestions for resource limits."""
        
        # This would typically load actual limits and usage data
        # For now, simulate with sample data
        
        current_limits = self.get_resource_limits(resource_id, is_active=True)
        
        # Use sample usage data if none provided
        sample_usage = usage_data or {
            "api_requests": {"current": 8500, "peak": 9200, "average": 7500},
            "storage_mb": {"current": 750, "peak": 800, "average": 600},
            "concurrent_users": {"current": 35, "peak": 42, "average": 30},
        }
        
        suggestions = self._plan_resource_limit_service.suggest_limit_optimizations(
            current_limits, sample_usage
        )
        
        return suggestions

    def validate_limit_compatibility(
        self, resource_id: UUID, limit_configurations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate compatibility between multiple limit configurations."""
        
        # Create temporary limits for validation
        temp_limits = []
        for config in limit_configurations:
            temp_limit = PlanResourceLimit.create(
                resource_id=resource_id,
                limit_type=config["limit_type"],
                limit_value=config["limit_value"],
                period=config["period"],
            )
            temp_limits.append(temp_limit)
        
        compatibility_result = self._plan_resource_limit_service.validate_limit_compatibility(
            temp_limits
        )
        
        return {
            "resource_id": str(resource_id),
            "limit_configurations": limit_configurations,
            "compatibility_result": compatibility_result,
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_limit_violation_history(
        self, resource_id: UUID, limit_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get history of limit violations for a resource."""
        
        # This would typically query violation records
        # For now, return sample data
        
        sample_violations = [
            {
                "id": "violation_001",
                "resource_id": str(resource_id),
                "limit_type": "api_requests",
                "limit_value": 10000,
                "actual_usage": 10500,
                "exceeded_by": 500,
                "exceeded_at": "2024-01-15T14:30:00Z",
                "resolved_at": "2024-01-15T15:00:00Z",
                "action_taken": "Temporary limit increase",
            },
            {
                "id": "violation_002",
                "resource_id": str(resource_id),
                "limit_type": "storage_mb",
                "limit_value": 1000,
                "actual_usage": 1050,
                "exceeded_by": 50,
                "exceeded_at": "2024-01-10T10:15:00Z",
                "resolved_at": "2024-01-10T11:00:00Z",
                "action_taken": "Data cleanup",
            },
        ]
        
        # Filter by limit type if specified
        if limit_type:
            sample_violations = [
                violation for violation in sample_violations
                if violation["limit_type"] == limit_type
            ]
        
        return sample_violations

    def delete_limit(self, limit_id: UUID) -> Dict[str, Any]:
        """Delete a plan resource limit."""
        
        try:
            # This would typically load and delete the actual limit
            return {
                "success": True,
                "limit_id": str(limit_id),
                "message": "Limit deleted successfully",
                "deleted_at": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "limit_id": str(limit_id),
                "message": f"Failed to delete limit: {str(e)}",
            }

    def activate_limit(self, limit_id: UUID) -> Dict[str, Any]:
        """Activate a plan resource limit."""
        
        try:
            # This would typically load the limit and set is_active=True
            return {
                "success": True,
                "limit_id": str(limit_id),
                "is_active": True,
                "message": "Limit activated successfully",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "limit_id": str(limit_id),
                "message": f"Failed to activate limit: {str(e)}",
            }

    def deactivate_limit(self, limit_id: UUID) -> Dict[str, Any]:
        """Deactivate a plan resource limit."""
        
        try:
            # This would typically load the limit and set is_active=False
            return {
                "success": True,
                "limit_id": str(limit_id),
                "is_active": False,
                "message": "Limit deactivated successfully",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "limit_id": str(limit_id),
                "message": f"Failed to deactivate limit: {str(e)}",
            }

    def bulk_update_limits(
        self, resource_id: UUID, limit_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Bulk update multiple limits for a resource."""
        
        results = []
        success_count = 0
        error_count = 0
        
        for update in limit_updates:
            limit_id = update.get("limit_id")
            if not limit_id:
                results.append({
                    "limit_id": None,
                    "success": False,
                    "message": "Limit ID is required",
                })
                error_count += 1
                continue
            
            try:
                # Simulate limit update
                results.append({
                    "limit_id": limit_id,
                    "success": True,
                    "message": "Limit updated successfully",
                    "updated_fields": {k: v for k, v in update.items() if k != "limit_id"},
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    "limit_id": limit_id,
                    "success": False,
                    "message": f"Failed to update limit: {str(e)}",
                })
                error_count += 1
        
        return {
            "resource_id": str(resource_id),
            "total_limits": len(limit_updates),
            "successful_updates": success_count,
            "failed_updates": error_count,
            "results": results,
            "bulk_update_completed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _build_limit_response(self, limit: PlanResourceLimit) -> Dict[str, Any]:
        """Build limit response dictionary."""
        
        return {
            "id": str(limit.id),
            "resource_id": str(limit.resource_id),
            "limit_type": limit.limit_type,
            "limit_value": limit.limit_value,
            "period": limit.period,
            "is_hard_limit": limit.is_hard_limit,
            "is_active": limit.is_active,
            "display_name": limit.get_display_name(),
            "formatted_value": limit.get_formatted_value(),
            "metadata": limit.metadata,
            "created_at": limit.created_at.isoformat(),
            "updated_at": limit.updated_at.isoformat() if limit.updated_at else None,
        }

    def _get_limit_recommendations(
        self, limit_type: str, limit_value: int, issues: List[str]
    ) -> List[str]:
        """Generate limit recommendations."""
        
        recommendations = []
        
        if issues:
            for issue in issues:
                if "too low" in issue.lower():
                    recommendations.append("Consider increasing the limit value for better user experience")
                elif "too high" in issue.lower():
                    recommendations.append("Consider reducing the limit value to prevent resource abuse")
                elif "invalid period" in issue.lower():
                    recommendations.append("Use a standard period: hourly, daily, weekly, monthly, or concurrent")
        
        # Type-specific recommendations
        if limit_type == "api_requests":
            if limit_value < 1000:
                recommendations.append("API request limit seems low for production use")
            elif limit_value > 100000:
                recommendations.append("Very high API limit - ensure infrastructure can handle the load")
        
        if limit_type == "storage_mb":
            if limit_value < 100:
                recommendations.append("Storage limit may be insufficient for normal usage")
        
        if not recommendations:
            recommendations.append("Limit configuration appears appropriate")
        
        return recommendations

    def _generate_limit_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights from limit usage patterns."""
        
        insights = []
        
        utilization_rate = patterns.get("average_utilization", 0)
        violation_frequency = patterns.get("violation_frequency", 0)
        peak_usage = patterns.get("peak_usage_ratio", 0)
        
        if utilization_rate > 0.9:
            insights.append("High utilization - consider increasing limits")
        elif utilization_rate < 0.3:
            insights.append("Low utilization - limits may be over-provisioned")
        
        if violation_frequency > 0.1:  # 10% violation rate
            insights.append("Frequent limit violations - review and adjust limits")
        elif violation_frequency == 0:
            insights.append("No recent violations - limits are well-configured")
        
        if peak_usage > 0.95:
            insights.append("Peak usage is very close to limits - consider buffer increases")
        
        return insights