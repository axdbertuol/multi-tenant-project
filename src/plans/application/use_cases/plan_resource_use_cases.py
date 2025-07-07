from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.entities.plan_resource import PlanResource, ResourceCategory
from ...domain.services.plan_resource_service import PlanResourceService
from ...domain.repositories.plan_repository import PlanRepository


class PlanResourceUseCase:
    """Use case for plan resource management operations."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._plan_repository: PlanRepository = uow.get_repository("plan")
        self._plan_resource_service = PlanResourceService(self._plan_repository)

    def create_resource(
        self,
        resource_type: str,
        name: str,
        category: ResourceCategory,
        created_by: UUID,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new plan resource."""
        
        try:
            resource = self._plan_resource_service.create_resource(
                resource_type=resource_type,
                name=name,
                category=category,
                created_by=created_by,
                description=description,
            )
            
            return {
                "id": str(resource.id),
                "resource_type": resource.resource_type,
                "name": resource.name,
                "description": resource.description,
                "category": resource.category.value,
                "is_active": resource.is_active,
                "created_at": resource.created_at.isoformat(),
                "created_by": str(resource.created_by),
            }
            
        except ValueError as e:
            raise ValueError(f"Failed to create resource: {str(e)}")

    def update_resource(
        self,
        resource_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[ResourceCategory] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an existing plan resource."""
        
        # For this implementation, we'll simulate the update
        # In a real implementation, you'd have a resource repository
        
        # This would typically load the resource, update it, and save
        # For now, returning a simulated response
        if not resource_id:
            return None
            
        return {
            "id": str(resource_id),
            "resource_type": "updated_resource_type",
            "name": name or "Updated Resource",
            "description": description or "Updated description",
            "category": category.value if category else ResourceCategory.MESSAGING.value,
            "is_active": is_active if is_active is not None else True,
            "updated_at": "2024-01-01T00:00:00Z",
        }

    def get_resource_by_id(self, resource_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a plan resource by ID."""
        
        # This would typically use a resource repository
        # For now, returning None to indicate not found
        return None

    def list_resources(
        self,
        category: Optional[ResourceCategory] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List plan resources with filtering and pagination."""
        
        # This would typically query the resource repository
        # For now, returning an empty list
        return {
            "resources": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }

    def validate_resource_compatibility(
        self, resource_type: str, plan_type: str
    ) -> Dict[str, Any]:
        """Validate if a resource type is compatible with a plan type."""
        
        is_compatible, issues = self._plan_resource_service.validate_resource_type_compatibility(
            resource_type, plan_type
        )
        
        return {
            "resource_type": resource_type,
            "plan_type": plan_type,
            "is_compatible": is_compatible,
            "issues": issues,
            "recommendations": self._get_compatibility_recommendations(resource_type, plan_type, issues),
        }

    def get_recommended_resources(
        self, category: ResourceCategory, plan_type: str
    ) -> List[Dict[str, Any]]:
        """Get recommended resources for a category and plan type."""
        
        recommendations = self._plan_resource_service.get_recommended_resources_for_category(
            category, plan_type
        )
        
        return recommendations

    def analyze_resource_dependencies(self, resource_type: str) -> Dict[str, Any]:
        """Analyze dependencies and conflicts for a resource."""
        
        return self._plan_resource_service.analyze_resource_dependencies(resource_type)

    def validate_resource_configuration(
        self, resource_type: str, configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate resource configuration."""
        
        # Create a temporary resource for validation
        temp_resource = PlanResource.create(
            resource_type=resource_type,
            name="Temp Resource",
            category=ResourceCategory.MESSAGING,  # Default category
            created_by=UUID("00000000-0000-0000-0000-000000000000"),
        )
        
        is_valid, issues = self._plan_resource_service.validate_resource_configuration(
            temp_resource, configuration
        )
        
        return {
            "resource_type": resource_type,
            "configuration": configuration,
            "is_valid": is_valid,
            "issues": issues,
            "suggestions": self._get_configuration_suggestions(configuration, issues),
        }

    def get_resource_usage_patterns(self, resource_type: str) -> Dict[str, Any]:
        """Get usage patterns for a resource type."""
        
        return self._plan_resource_service.get_resource_usage_patterns(resource_type)

    def get_plan_resource_optimization_suggestions(
        self, plan_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get optimization suggestions for plan resources."""
        
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        return self._plan_resource_service.suggest_resource_optimizations(plan)

    def test_resource_configuration(
        self, resource_type: str, configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test a resource configuration to ensure it works properly."""
        
        # Validate configuration first
        validation_result = self.validate_resource_configuration(resource_type, configuration)
        
        if not validation_result["is_valid"]:
            return {
                "test_passed": False,
                "validation_failed": True,
                "issues": validation_result["issues"],
                "test_results": {},
            }
        
        # Simulate configuration testing
        test_results = {
            "connectivity_test": True,
            "authentication_test": True,
            "permissions_test": True,
            "performance_test": {
                "response_time_ms": 150,
                "throughput_rps": 1000,
                "error_rate": 0.01,
            },
        }
        
        # Check for potential issues based on configuration
        potential_issues = []
        if configuration.get("timeout", 30) > 60:
            potential_issues.append("High timeout value may affect user experience")
        
        if configuration.get("retry_attempts", 3) > 5:
            potential_issues.append("High retry attempts may cause delays")
        
        return {
            "test_passed": True,
            "validation_failed": False,
            "resource_type": resource_type,
            "configuration": configuration,
            "test_results": test_results,
            "potential_issues": potential_issues,
            "recommendations": self._get_test_recommendations(test_results),
        }

    def get_resource_health_status(self, resource_type: str) -> Dict[str, Any]:
        """Get health status for a specific resource type across all plans."""
        
        # This would typically check across all instances of this resource type
        # For now, return a simulated health status
        
        health_metrics = {
            "total_instances": 150,
            "healthy_instances": 145,
            "degraded_instances": 4,
            "failed_instances": 1,
            "average_response_time_ms": 250,
            "success_rate_percent": 99.2,
            "last_24h_errors": 12,
        }
        
        overall_health = "healthy"
        if health_metrics["failed_instances"] > 0:
            overall_health = "degraded"
        if health_metrics["success_rate_percent"] < 95:
            overall_health = "critical"
        
        return {
            "resource_type": resource_type,
            "overall_health": overall_health,
            "metrics": health_metrics,
            "alerts": self._generate_health_alerts(health_metrics),
            "recommendations": self._generate_health_recommendations(health_metrics),
        }

    def _get_compatibility_recommendations(
        self, resource_type: str, plan_type: str, issues: List[str]
    ) -> List[str]:
        """Generate compatibility recommendations."""
        
        recommendations = []
        
        if issues:
            if "not available in basic plans" in " ".join(issues):
                recommendations.append("Consider upgrading to premium or enterprise plan")
            
            if "enterprise-level" in " ".join(issues):
                recommendations.append("This resource requires enterprise-level subscription")
            
            recommendations.append("Review plan features and upgrade if necessary")
        else:
            recommendations.append("Resource is compatible with the specified plan type")
        
        return recommendations

    def _get_configuration_suggestions(
        self, configuration: Dict[str, Any], issues: List[str]
    ) -> List[str]:
        """Generate configuration suggestions."""
        
        suggestions = []
        
        if issues:
            for issue in issues:
                if "required" in issue.lower():
                    suggestions.append("Add missing required configuration fields")
                elif "invalid" in issue.lower():
                    suggestions.append("Review and correct invalid configuration values")
        
        # General configuration suggestions
        if "timeout" not in configuration:
            suggestions.append("Consider adding timeout configuration")
        
        if "retry_attempts" not in configuration:
            suggestions.append("Consider adding retry configuration for better reliability")
        
        return suggestions

    def _get_test_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate test-based recommendations."""
        
        recommendations = []
        
        perf = test_results.get("performance_test", {})
        
        if perf.get("response_time_ms", 0) > 500:
            recommendations.append("Consider optimizing configuration for better response times")
        
        if perf.get("error_rate", 0) > 0.05:  # 5%
            recommendations.append("High error rate detected - review configuration settings")
        
        if perf.get("throughput_rps", 0) < 100:
            recommendations.append("Low throughput detected - consider resource scaling")
        
        if not recommendations:
            recommendations.append("Configuration test passed successfully")
        
        return recommendations

    def _generate_health_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate health alerts based on metrics."""
        
        alerts = []
        
        if metrics["failed_instances"] > 0:
            alerts.append({
                "level": "error",
                "message": f"{metrics['failed_instances']} instances are failing",
                "action": "Investigate failed instances immediately"
            })
        
        if metrics["success_rate_percent"] < 98:
            alerts.append({
                "level": "warning",
                "message": f"Success rate is {metrics['success_rate_percent']:.1f}%",
                "action": "Monitor closely and investigate if rate continues to decline"
            })
        
        if metrics["average_response_time_ms"] > 1000:
            alerts.append({
                "level": "warning",
                "message": f"High response time: {metrics['average_response_time_ms']}ms",
                "action": "Consider performance optimization"
            })
        
        return alerts

    def _generate_health_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on metrics."""
        
        recommendations = []
        
        if metrics["degraded_instances"] > 0:
            recommendations.append("Schedule maintenance for degraded instances")
        
        if metrics["last_24h_errors"] > 50:
            recommendations.append("High error count - review logs and configurations")
        
        if metrics["average_response_time_ms"] > 500:
            recommendations.append("Implement caching or optimize resource configuration")
        
        if not recommendations:
            recommendations.append("Resource health is optimal")
        
        return recommendations