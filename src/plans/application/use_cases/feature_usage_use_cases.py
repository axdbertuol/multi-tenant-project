from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.entities.feature_usage import FeatureUsage, UsagePeriod
from ...domain.repositories.feature_usage_repository import FeatureUsageRepository
from ...domain.repositories.organization_plan_repository import OrganizationPlanRepository
from ...domain.repositories.plan_repository import PlanRepository
from ...domain.services.usage_tracking_service import UsageTrackingService


class FeatureUsageUseCase:
    """Use case for feature usage tracking and analytics."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._feature_usage_repository: FeatureUsageRepository = uow.get_repository("feature_usage")
        self._org_plan_repository: OrganizationPlanRepository = uow.get_repository("organization_plan")
        self._plan_repository: PlanRepository = uow.get_repository("plan")
        self._usage_tracking_service = UsageTrackingService(
            self._feature_usage_repository,
            self._org_plan_repository,
            self._plan_repository,
        )

    def track_feature_usage(
        self,
        organization_id: UUID,
        feature_name: str,
        amount: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Track feature usage for an organization."""
        
        try:
            with self._uow:
                success, message, usage = self._usage_tracking_service.track_feature_usage(
                    organization_id=organization_id,
                    feature_name=feature_name,
                    amount=amount,
                    metadata=metadata,
                )
                
                result = {
                    "success": success,
                    "message": message,
                    "organization_id": str(organization_id),
                    "feature_name": feature_name,
                    "amount": amount,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                
                if usage:
                    result["usage_summary"] = usage.get_usage_summary()
                
                return result
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to track usage: {str(e)}",
                "organization_id": str(organization_id),
                "feature_name": feature_name,
                "amount": amount,
            }

    def get_organization_usage_summary(self, organization_id: UUID) -> Dict[str, Any]:
        """Get comprehensive usage summary for an organization."""
        
        return self._usage_tracking_service.get_organization_usage_summary(organization_id)

    def get_feature_usage_details(
        self,
        organization_id: UUID,
        feature_name: str,
        period: UsagePeriod = UsagePeriod.MONTHLY,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed usage information for a specific feature."""
        
        usage = self._feature_usage_repository.get_current_usage(
            organization_id, feature_name, period
        )
        
        if not usage:
            return None
        
        return {
            "organization_id": str(organization_id),
            "feature_name": feature_name,
            "period": period.value,
            "usage_details": usage.get_usage_summary(),
            "recommendations": self._get_usage_recommendations(usage),
        }

    def check_feature_access(
        self, organization_id: UUID, feature_name: str, requested_amount: int = 1
    ) -> Dict[str, Any]:
        """Check if organization can use a feature."""
        
        can_access, message, details = self._usage_tracking_service.check_feature_access(
            organization_id, feature_name, requested_amount
        )
        
        return {
            "organization_id": str(organization_id),
            "feature_name": feature_name,
            "requested_amount": requested_amount,
            "can_access": can_access,
            "message": message,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_usage_analytics(
        self, organization_id: UUID, feature_name: str, periods: int = 12
    ) -> Dict[str, Any]:
        """Get usage analytics and trends for a feature."""
        
        return self._usage_tracking_service.get_usage_analytics(
            organization_id, feature_name, periods
        )

    def get_feature_usage_history(
        self,
        organization_id: UUID,
        feature_name: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get historical usage data for an organization."""
        
        usage_records = self._feature_usage_repository.get_organization_usage(
            organization_id, period_start, period_end
        )
        
        history = []
        for usage in usage_records:
            if feature_name is None or usage.feature_name == feature_name:
                history.append({
                    "id": str(usage.id),
                    "feature_name": usage.feature_name,
                    "period": usage.usage_period.value,
                    "period_start": usage.period_start.isoformat(),
                    "period_end": usage.period_end.isoformat(),
                    "current_usage": usage.current_usage,
                    "limit_value": usage.limit_value,
                    "utilization_percent": usage.get_usage_percentage(),
                    "is_unlimited": usage.is_unlimited(),
                    "is_limit_exceeded": usage.is_limit_exceeded(),
                    "created_at": usage.created_at.isoformat(),
                    "updated_at": usage.updated_at.isoformat() if usage.updated_at else None,
                })
        
        return history

    def reset_feature_usage(
        self, organization_id: UUID, feature_name: str, period: UsagePeriod
    ) -> Dict[str, Any]:
        """Reset usage for a specific feature and period."""
        
        try:
            with self._uow:
                success = self._feature_usage_repository.reset_usage_for_period(
                    organization_id, feature_name, period
                )
                
                return {
                    "success": success,
                    "organization_id": str(organization_id),
                    "feature_name": feature_name,
                    "period": period.value,
                    "reset_at": datetime.utcnow().isoformat(),
                    "message": "Usage reset successfully" if success else "Failed to reset usage",
                }
                
        except Exception as e:
            return {
                "success": False,
                "organization_id": str(organization_id),
                "feature_name": feature_name,
                "period": period.value,
                "message": f"Error resetting usage: {str(e)}",
            }

    def get_organizations_near_limits(
        self, threshold_percent: float = 0.8, feature_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get organizations approaching their usage limits."""
        
        return self._usage_tracking_service.get_organizations_near_limits(threshold_percent)

    def create_usage_record(
        self,
        organization_id: UUID,
        feature_name: str,
        usage_period: UsagePeriod,
        limit_value: int,
        current_usage: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new usage record."""
        
        try:
            with self._uow:
                usage = FeatureUsage.create(
                    organization_id=organization_id,
                    feature_name=feature_name,
                    usage_period=usage_period,
                    limit_value=limit_value,
                    current_usage=current_usage,
                    metadata=metadata,
                )
                
                saved_usage = self._feature_usage_repository.save(usage)
                
                return {
                    "success": True,
                    "usage_id": str(saved_usage.id),
                    "organization_id": str(organization_id),
                    "feature_name": feature_name,
                    "usage_summary": saved_usage.get_usage_summary(),
                    "message": "Usage record created successfully",
                }
                
        except Exception as e:
            return {
                "success": False,
                "organization_id": str(organization_id),
                "feature_name": feature_name,
                "message": f"Failed to create usage record: {str(e)}",
            }

    def update_usage_limit(
        self, organization_id: UUID, feature_name: str, new_limit: int
    ) -> Dict[str, Any]:
        """Update the usage limit for a feature."""
        
        try:
            current_usage = self._feature_usage_repository.get_current_usage(
                organization_id, feature_name, UsagePeriod.MONTHLY
            )
            
            if not current_usage:
                return {
                    "success": False,
                    "message": "No current usage record found",
                    "organization_id": str(organization_id),
                    "feature_name": feature_name,
                }
            
            with self._uow:
                updated_usage = current_usage.update_limit(new_limit)
                saved_usage = self._feature_usage_repository.save(updated_usage)
                
                return {
                    "success": True,
                    "organization_id": str(organization_id),
                    "feature_name": feature_name,
                    "old_limit": current_usage.limit_value,
                    "new_limit": new_limit,
                    "usage_summary": saved_usage.get_usage_summary(),
                    "message": "Usage limit updated successfully",
                }
                
        except Exception as e:
            return {
                "success": False,
                "organization_id": str(organization_id),
                "feature_name": feature_name,
                "message": f"Failed to update limit: {str(e)}",
            }

    def get_feature_usage_across_organizations(
        self, feature_name: str, period: UsagePeriod, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get usage statistics for a feature across all organizations."""
        
        usage_records = self._feature_usage_repository.get_feature_usage_across_organizations(
            feature_name, period
        )
        
        results = []
        for usage in usage_records[:limit]:  # Limit results
            results.append({
                "organization_id": str(usage.organization_id),
                "feature_name": usage.feature_name,
                "period": period.value,
                "current_usage": usage.current_usage,
                "limit_value": usage.limit_value,
                "utilization_percent": usage.get_usage_percentage(),
                "is_limit_exceeded": usage.is_limit_exceeded(),
                "is_limit_near": usage.is_limit_near(),
            })
        
        # Calculate aggregate statistics
        total_usage = sum(r["current_usage"] for r in results)
        avg_utilization = sum(r["utilization_percent"] for r in results) / len(results) if results else 0
        exceeded_count = sum(1 for r in results if r["is_limit_exceeded"])
        
        return {
            "feature_name": feature_name,
            "period": period.value,
            "total_organizations": len(results),
            "total_usage": total_usage,
            "average_utilization_percent": round(avg_utilization, 2),
            "organizations_exceeded": exceeded_count,
            "organizations": results,
            "aggregates": {
                "min_usage": min(r["current_usage"] for r in results) if results else 0,
                "max_usage": max(r["current_usage"] for r in results) if results else 0,
                "median_utilization": self._calculate_median([r["utilization_percent"] for r in results]),
            },
        }

    def cleanup_old_usage_records(self, older_than_days: int = 365) -> Dict[str, Any]:
        """Clean up old usage records."""
        
        try:
            with self._uow:
                deleted_count = self._feature_usage_repository.delete_old_records(older_than_days)
                
                return {
                    "success": True,
                    "deleted_records": deleted_count,
                    "cutoff_days": older_than_days,
                    "cleanup_date": datetime.utcnow().isoformat(),
                    "message": f"Cleaned up {deleted_count} old usage records",
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to cleanup records: {str(e)}",
                "cutoff_days": older_than_days,
            }

    def _get_usage_recommendations(self, usage: FeatureUsage) -> List[str]:
        """Generate usage recommendations based on current usage."""
        
        recommendations = []
        
        if usage.is_limit_exceeded():
            recommendations.extend([
                "Usage limit has been exceeded",
                "Consider upgrading your plan for higher limits",
                "Review usage patterns to optimize consumption",
            ])
        elif usage.is_limit_near(0.9):  # 90% threshold
            recommendations.extend([
                "Approaching usage limit",
                "Monitor usage closely",
                "Consider upgrading plan if trend continues",
            ])
        elif usage.is_limit_near(0.8):  # 80% threshold
            recommendations.append("Usage is moderately high - monitor trends")
        elif usage.get_usage_percentage() < 20:
            recommendations.append("Usage is low - current plan may be over-provisioned")
        
        if usage.is_period_expired():
            recommendations.append("Usage period has expired - will reset soon")
        elif usage.days_until_reset() <= 3:
            recommendations.append(f"Usage will reset in {usage.days_until_reset()} days")
        
        if not recommendations:
            recommendations.append("Usage is within normal limits")
        
        return recommendations

    def _calculate_median(self, values: List[float]) -> float:
        """Calculate median value from a list."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]