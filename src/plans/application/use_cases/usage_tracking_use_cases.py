from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.entities.feature_usage import UsagePeriod
from ...domain.repositories.feature_usage_repository import FeatureUsageRepository
from ...domain.repositories.organization_plan_repository import OrganizationPlanRepository
from ...domain.repositories.plan_repository import PlanRepository
from ...domain.services.usage_tracking_service import UsageTrackingService


class UsageTrackingUseCase:
    """Use case for comprehensive usage tracking and analytics."""

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

    def get_organization_analytics_dashboard(self, organization_id: UUID) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard for an organization."""
        
        # Get basic usage summary
        usage_summary = self._usage_tracking_service.get_organization_usage_summary(organization_id)
        
        # Get plan details
        org_plan = self._org_plan_repository.get_by_organization_id(organization_id)
        plan_details = None
        if org_plan:
            plan = self._plan_repository.get_by_id(org_plan.plan_id)
            if plan:
                plan_details = {
                    "id": str(plan.id),
                    "name": plan.name.value,
                    "type": plan.plan_type.value,
                    "subscription_status": org_plan.status.value,
                    "billing_cycle": org_plan.billing_cycle.value,
                    "started_at": org_plan.started_at.isoformat(),
                    "expires_at": org_plan.expires_at.isoformat() if org_plan.expires_at else None,
                }
        
        # Get feature usage trends
        current_date = datetime.utcnow()
        trends = {}
        
        if usage_summary.get("features"):
            for feature_name in usage_summary["features"].keys():
                feature_trends = self._usage_tracking_service.get_usage_analytics(
                    organization_id, feature_name, periods=12
                )
                trends[feature_name] = feature_trends
        
        # Calculate key metrics
        key_metrics = self._calculate_key_metrics(usage_summary, trends)
        
        # Get alerts and recommendations
        alerts = self._generate_usage_alerts(usage_summary)
        recommendations = self._generate_usage_recommendations(usage_summary, trends)
        
        return {
            "organization_id": str(organization_id),
            "generated_at": current_date.isoformat(),
            "plan_details": plan_details,
            "usage_summary": usage_summary,
            "key_metrics": key_metrics,
            "feature_trends": trends,
            "alerts": alerts,
            "recommendations": recommendations,
            "period": {
                "current_month": {
                    "start": current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat(),
                    "end": (current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)).replace(day=1).isoformat(),
                }
            },
        }

    def get_feature_usage_trends(
        self, organization_id: UUID, feature_name: str, periods: int = 12
    ) -> Dict[str, Any]:
        """Get detailed usage trends for a specific feature."""
        
        analytics = self._usage_tracking_service.get_usage_analytics(
            organization_id, feature_name, periods
        )
        
        # Enhance with additional analysis
        trends = analytics.get("trends", [])
        
        # Calculate trend metrics
        trend_analysis = self._analyze_trend_patterns(trends)
        
        # Get current usage status
        current_usage = self._feature_usage_repository.get_current_usage(
            organization_id, feature_name, UsagePeriod.MONTHLY
        )
        
        current_status = None
        if current_usage:
            current_status = {
                "current_usage": current_usage.current_usage,
                "limit_value": current_usage.limit_value,
                "utilization_percent": current_usage.get_usage_percentage(),
                "remaining_usage": current_usage.get_remaining_usage(),
                "days_until_reset": current_usage.days_until_reset(),
                "is_limit_exceeded": current_usage.is_limit_exceeded(),
                "is_limit_near": current_usage.is_limit_near(),
            }
        
        return {
            "organization_id": str(organization_id),
            "feature_name": feature_name,
            "periods_analyzed": periods,
            "current_status": current_status,
            "trend_analysis": trend_analysis,
            "historical_data": trends,
            "insights": analytics.get("insights", []),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_system_wide_analytics(
        self, feature_name: Optional[str] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """Get system-wide usage analytics across all organizations."""
        
        current_date = datetime.utcnow()
        
        # Get organizations near limits
        organizations_near_limits = self._usage_tracking_service.get_organizations_near_limits(0.8)
        
        # Get feature usage across organizations
        feature_analytics = {}
        if feature_name:
            # Get usage for specific feature
            feature_usage = self._feature_usage_repository.get_feature_usage_across_organizations(
                feature_name, UsagePeriod.MONTHLY
            )
            
            feature_analytics[feature_name] = {
                "total_organizations": len(feature_usage),
                "total_usage": sum(usage.current_usage for usage in feature_usage),
                "average_usage": sum(usage.current_usage for usage in feature_usage) / len(feature_usage) if feature_usage else 0,
                "organizations_exceeded": len([usage for usage in feature_usage if usage.is_limit_exceeded()]),
                "organizations_near_limit": len([usage for usage in feature_usage if usage.is_limit_near(0.8)]),
            }
        
        # Generate system health metrics
        system_health = self._calculate_system_health_metrics(organizations_near_limits)
        
        return {
            "generated_at": current_date.isoformat(),
            "system_health": system_health,
            "organizations_near_limits": organizations_near_limits[:limit],
            "feature_analytics": feature_analytics,
            "summary": {
                "total_organizations_monitored": len(organizations_near_limits),
                "organizations_requiring_attention": len([org for org in organizations_near_limits]),
            },
        }

    def generate_usage_report(
        self,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        include_trends: bool = True,
    ) -> Dict[str, Any]:
        """Generate comprehensive usage report for a date range."""
        
        # Get usage data for the period
        usage_records = self._feature_usage_repository.get_organization_usage(
            organization_id, start_date, end_date
        )
        
        # Group by feature
        feature_data = {}
        for usage in usage_records:
            if usage.feature_name not in feature_data:
                feature_data[usage.feature_name] = []
            feature_data[usage.feature_name].append({
                "period_start": usage.period_start.isoformat(),
                "period_end": usage.period_end.isoformat(),
                "usage": usage.current_usage,
                "limit": usage.limit_value,
                "utilization_percent": usage.get_usage_percentage(),
            })
        
        # Calculate summary statistics
        summary_stats = {}
        for feature_name, records in feature_data.items():
            total_usage = sum(record["usage"] for record in records)
            avg_utilization = sum(record["utilization_percent"] for record in records) / len(records) if records else 0
            max_usage = max(record["usage"] for record in records) if records else 0
            
            summary_stats[feature_name] = {
                "total_usage": total_usage,
                "average_utilization_percent": round(avg_utilization, 2),
                "peak_usage": max_usage,
                "data_points": len(records),
            }
        
        # Get trends if requested
        trends = {}
        if include_trends:
            for feature_name in feature_data.keys():
                trends[feature_name] = self._usage_tracking_service.get_usage_analytics(
                    organization_id, feature_name, periods=6
                )
        
        return {
            "organization_id": str(organization_id),
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "duration_days": (end_date - start_date).days,
            },
            "summary_statistics": summary_stats,
            "detailed_data": feature_data,
            "trends": trends if include_trends else {},
            "generated_at": datetime.utcnow().isoformat(),
        }

    def reset_monthly_usage_bulk(self) -> Dict[str, Any]:
        """Reset monthly usage for all organizations (scheduled operation)."""
        
        try:
            with self._uow:
                reset_count = self._feature_usage_repository.bulk_reset_monthly_usage()
                
                return {
                    "success": True,
                    "reset_records": reset_count,
                    "operation": "bulk_monthly_reset",
                    "executed_at": datetime.utcnow().isoformat(),
                    "message": f"Successfully reset {reset_count} monthly usage records",
                }
                
        except Exception as e:
            return {
                "success": False,
                "operation": "bulk_monthly_reset",
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat(),
            }

    def get_limit_utilization_analysis(
        self, organization_id: UUID
    ) -> Dict[str, Any]:
        """Analyze limit utilization patterns for an organization."""
        
        usage_summary = self._usage_tracking_service.get_organization_usage_summary(organization_id)
        
        utilization_analysis = {
            "organization_id": str(organization_id),
            "overall_status": usage_summary.get("overall_status", "unknown"),
            "feature_utilization": {},
            "risk_assessment": "low",
            "recommendations": [],
        }
        
        features = usage_summary.get("features", {})
        high_utilization_count = 0
        critical_utilization_count = 0
        
        for feature_name, feature_data in features.items():
            utilization_percent = feature_data.get("usage_percentage", 0)
            
            # Categorize utilization level
            if utilization_percent >= 90:
                level = "critical"
                critical_utilization_count += 1
            elif utilization_percent >= 75:
                level = "high"
                high_utilization_count += 1
            elif utilization_percent >= 50:
                level = "moderate"
            else:
                level = "low"
            
            utilization_analysis["feature_utilization"][feature_name] = {
                "utilization_percent": utilization_percent,
                "level": level,
                "current_usage": feature_data.get("current_usage", 0),
                "limit_value": feature_data.get("limit_value", 0),
                "is_unlimited": feature_data.get("is_unlimited", False),
            }
        
        # Assess overall risk
        if critical_utilization_count > 0:
            utilization_analysis["risk_assessment"] = "critical"
            utilization_analysis["recommendations"].append(
                "Immediate action required - some features have critical utilization"
            )
        elif high_utilization_count > 1:
            utilization_analysis["risk_assessment"] = "high"
            utilization_analysis["recommendations"].append(
                "Monitor closely - multiple features have high utilization"
            )
        elif high_utilization_count > 0:
            utilization_analysis["risk_assessment"] = "medium"
            utilization_analysis["recommendations"].append(
                "Consider reviewing usage patterns and plan limits"
            )
        
        utilization_analysis["summary"] = {
            "total_features": len(features),
            "critical_utilization": critical_utilization_count,
            "high_utilization": high_utilization_count,
            "average_utilization": sum(
                f.get("usage_percentage", 0) for f in features.values()
            ) / len(features) if features else 0,
        }
        
        return utilization_analysis

    def _calculate_key_metrics(
        self, usage_summary: Dict[str, Any], trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate key metrics from usage data."""
        
        features = usage_summary.get("features", {})
        
        # Calculate utilization metrics
        total_features = len(features)
        exceeded_features = sum(1 for f in features.values() if f.get("is_limit_exceeded", False))
        near_limit_features = sum(1 for f in features.values() if f.get("is_limit_near", False))
        
        # Calculate average utilization
        avg_utilization = sum(f.get("usage_percentage", 0) for f in features.values()) / total_features if total_features > 0 else 0
        
        # Calculate growth trends
        growth_metrics = {}
        for feature_name, trend_data in trends.items():
            trend_list = trend_data.get("trends", [])
            if len(trend_list) >= 2:
                recent_usage = trend_list[0].get("usage", 0)
                previous_usage = trend_list[1].get("usage", 0) 
                growth_rate = ((recent_usage - previous_usage) / max(previous_usage, 1)) * 100
                growth_metrics[feature_name] = growth_rate
        
        return {
            "total_features": total_features,
            "features_exceeded": exceeded_features,
            "features_near_limit": near_limit_features,
            "average_utilization_percent": round(avg_utilization, 2),
            "health_score": self._calculate_health_score(exceeded_features, near_limit_features, total_features),
            "growth_metrics": growth_metrics,
        }

    def _calculate_health_score(self, exceeded: int, near_limit: int, total: int) -> float:
        """Calculate a health score based on utilization."""
        if total == 0:
            return 100.0
        
        # Penalize exceeded and near-limit features
        penalty = (exceeded * 20) + (near_limit * 10)
        score = max(0, 100 - penalty)
        
        return round(score, 1)

    def _analyze_trend_patterns(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in trend data."""
        
        if len(trends) < 2:
            return {"pattern": "insufficient_data", "confidence": 0}
        
        # Calculate trend direction
        recent_values = [t.get("usage", 0) for t in trends[:3]]
        older_values = [t.get("usage", 0) for t in trends[-3:]]
        
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        
        if recent_avg > older_avg * 1.1:
            pattern = "increasing"
        elif recent_avg < older_avg * 0.9:
            pattern = "decreasing"
        else:
            pattern = "stable"
        
        # Calculate volatility
        all_values = [t.get("usage", 0) for t in trends]
        avg_value = sum(all_values) / len(all_values)
        variance = sum((x - avg_value) ** 2 for x in all_values) / len(all_values)
        volatility = "high" if variance > avg_value else "low"
        
        return {
            "pattern": pattern,
            "volatility": volatility,
            "recent_average": round(recent_avg, 2),
            "historical_average": round(older_avg, 2),
            "confidence": 0.8 if len(trends) >= 6 else 0.5,
        }

    def _generate_usage_alerts(self, usage_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on usage summary."""
        
        alerts = []
        features = usage_summary.get("features", {})
        
        for feature_name, feature_data in features.items():
            if feature_data.get("is_limit_exceeded", False):
                alerts.append({
                    "level": "critical",
                    "feature": feature_name,
                    "message": f"Usage limit exceeded for {feature_name}",
                    "utilization": feature_data.get("usage_percentage", 0),
                })
            elif feature_data.get("is_limit_near", False):
                alerts.append({
                    "level": "warning",
                    "feature": feature_name,
                    "message": f"Approaching usage limit for {feature_name}",
                    "utilization": feature_data.get("usage_percentage", 0),
                })
        
        return alerts

    def _generate_usage_recommendations(
        self, usage_summary: Dict[str, Any], trends: Dict[str, Any]
    ) -> List[str]:
        """Generate usage recommendations."""
        
        recommendations = []
        overall_status = usage_summary.get("overall_status", "healthy")
        
        if overall_status == "over_limit":
            recommendations.append("Consider upgrading your plan to increase limits")
            recommendations.append("Review usage patterns to optimize consumption")
        elif overall_status == "approaching_limit":
            recommendations.append("Monitor usage closely over the next few days")
            recommendations.append("Plan for potential limit increases")
        
        # Analyze trends for recommendations
        for feature_name, trend_data in trends.items():
            pattern = trend_data.get("trend_analysis", {}).get("pattern")
            if pattern == "increasing":
                recommendations.append(f"Usage for {feature_name} is increasing - monitor for future capacity needs")
        
        if not recommendations:
            recommendations.append("Usage is within normal limits - no immediate action required")
        
        return recommendations

    def _calculate_system_health_metrics(self, organizations_near_limits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate system-wide health metrics."""
        
        total_orgs = len(organizations_near_limits) if organizations_near_limits else 0
        
        if total_orgs == 0:
            return {
                "status": "healthy",
                "risk_level": "low",
                "organizations_at_risk": 0,
                "system_utilization": 0,
            }
        
        # Count organizations by risk level
        critical_orgs = len([org for org in organizations_near_limits if org.get("usage_percentage", 0) >= 95])
        warning_orgs = len([org for org in organizations_near_limits if 80 <= org.get("usage_percentage", 0) < 95])
        
        # Determine system status
        if critical_orgs > total_orgs * 0.1:  # 10% of orgs are critical
            status = "critical"
            risk_level = "high"
        elif warning_orgs > total_orgs * 0.3:  # 30% of orgs are at warning
            status = "degraded" 
            risk_level = "medium"
        else:
            status = "healthy"
            risk_level = "low"
        
        avg_utilization = sum(org.get("usage_percentage", 0) for org in organizations_near_limits) / total_orgs
        
        return {
            "status": status,
            "risk_level": risk_level,
            "organizations_at_risk": total_orgs,
            "critical_organizations": critical_orgs,
            "warning_organizations": warning_orgs,
            "system_utilization": round(avg_utilization, 2),
        }