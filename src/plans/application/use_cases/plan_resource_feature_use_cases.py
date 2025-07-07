from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.entities.plan_resource_feature import PlanResourceFeature
from ...domain.entities.plan_resource import ResourceCategory
from ...domain.services.plan_resource_feature_service import PlanResourceFeatureService


class PlanResourceFeatureUseCase:
    """Use case for plan resource feature management operations."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._plan_resource_feature_service = PlanResourceFeatureService()

    def create_feature(
        self,
        resource_id: UUID,
        feature_key: str,
        feature_name: str,
        description: Optional[str] = None,
        is_default: bool = False,
    ) -> Dict[str, Any]:
        """Create a new plan resource feature."""
        
        try:
            feature = self._plan_resource_feature_service.create_feature(
                resource_id=resource_id,
                feature_key=feature_key,
                feature_name=feature_name,
                description=description,
                is_default=is_default,
            )
            
            return {
                "success": True,
                "feature": self._build_feature_response(feature),
                "message": "Resource feature created successfully",
            }
            
        except ValueError as e:
            return {
                "success": False,
                "message": f"Failed to create feature: {str(e)}",
                "resource_id": str(resource_id),
                "feature_key": feature_key,
            }

    def get_feature_by_id(self, feature_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a plan resource feature by ID."""
        
        # This would typically use a feature repository
        # For now, return a simulated response
        return {
            "id": str(feature_id),
            "resource_id": "00000000-0000-0000-0000-000000000000",
            "feature_key": "sample_feature",
            "feature_name": "Sample Feature",
            "description": "A sample feature for demonstration",
            "is_default": False,
            "created_at": "2024-01-01T00:00:00Z",
        }

    def update_feature(
        self,
        feature_id: UUID,
        feature_name: Optional[str] = None,
        description: Optional[str] = None,
        is_default: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update an existing plan resource feature."""
        
        try:
            # This would typically load the feature, update it, and save
            # For now, simulate the update process
            
            return {
                "success": True,
                "feature_id": str(feature_id),
                "updated_fields": {
                    "feature_name": feature_name,
                    "description": description,
                    "is_default": is_default,
                },
                "message": "Feature updated successfully",
                "updated_at": "2024-01-01T00:00:00Z",
            }
            
        except Exception as e:
            return {
                "success": False,
                "feature_id": str(feature_id),
                "message": f"Failed to update feature: {str(e)}",
            }

    def validate_feature_dependencies(
        self, feature_key: str, resource_category: ResourceCategory
    ) -> Dict[str, Any]:
        """Validate feature dependencies and conflicts."""
        
        is_valid, issues = self._plan_resource_feature_service.validate_feature_dependencies(
            feature_key, resource_category
        )
        
        return {
            "feature_key": feature_key,
            "resource_category": resource_category.value,
            "is_valid": is_valid,
            "issues": issues,
            "recommendations": self._get_dependency_recommendations(feature_key, issues),
        }

    def get_recommended_features(
        self, resource_type: str, resource_category: ResourceCategory
    ) -> List[Dict[str, Any]]:
        """Get recommended features for a resource type."""
        
        recommendations = self._plan_resource_feature_service.get_recommended_features_for_resource(
            resource_type, resource_category
        )
        
        return recommendations

    def validate_feature_configuration(
        self, feature_id: UUID, configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate feature configuration."""
        
        # Create a temporary feature for validation
        temp_feature = PlanResourceFeature.create(
            resource_id=UUID("00000000-0000-0000-0000-000000000000"),
            feature_key="temp_feature",
            feature_name="Temporary Feature",
        )
        
        is_valid, issues = self._plan_resource_feature_service.validate_feature_configuration(
            temp_feature, configuration
        )
        
        return {
            "feature_id": str(feature_id),
            "configuration": configuration,
            "is_valid": is_valid,
            "issues": issues,
            "suggestions": self._get_configuration_suggestions(configuration, issues),
        }

    def analyze_feature_usage_patterns(self, feature_key: str) -> Dict[str, Any]:
        """Analyze usage patterns for a specific feature."""
        
        patterns = self._plan_resource_feature_service.analyze_feature_usage_patterns(feature_key)
        
        # Enhance with additional insights
        insights = self._generate_feature_insights(patterns)
        
        return {
            "feature_key": feature_key,
            "usage_patterns": patterns,
            "insights": insights,
            "analyzed_at": "2024-01-01T00:00:00Z",
        }

    def get_feature_optimization_suggestions(
        self, resource_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get optimization suggestions for resource features."""
        
        # This would typically load all features for the resource
        # For now, simulate with sample features
        sample_features = [
            PlanResourceFeature.create(
                resource_id=resource_id,
                feature_key="auto_reply",
                feature_name="Auto Reply",
                is_default=True,
            ),
            PlanResourceFeature.create(
                resource_id=resource_id,
                feature_key="advanced_analytics",
                feature_name="Advanced Analytics",
                is_default=False,
            ),
        ]
        
        suggestions = self._plan_resource_feature_service.suggest_feature_optimizations(
            sample_features
        )
        
        return suggestions

    def get_feature_compatibility_matrix(self, resource_id: UUID) -> Dict[str, Any]:
        """Get compatibility matrix for features in a resource."""
        
        # This would typically load all features for the resource
        # For now, simulate with sample features
        sample_features = [
            PlanResourceFeature.create(
                resource_id=resource_id,
                feature_key="auto_reply",
                feature_name="Auto Reply",
            ),
            PlanResourceFeature.create(
                resource_id=resource_id,
                feature_key="manual_reply",
                feature_name="Manual Reply",
            ),
            PlanResourceFeature.create(
                resource_id=resource_id,
                feature_key="advanced_analytics",
                feature_name="Advanced Analytics",
            ),
        ]
        
        compatibility_matrix = self._plan_resource_feature_service.get_feature_compatibility_matrix(
            sample_features
        )
        
        return {
            "resource_id": str(resource_id),
            "compatibility_matrix": compatibility_matrix,
            "features_analyzed": len(sample_features),
            "generated_at": "2024-01-01T00:00:00Z",
        }

    def list_resource_features(
        self, resource_id: UUID, is_default: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """List all features for a resource."""
        
        # This would typically query a feature repository
        # For now, return sample data
        
        sample_features = [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "resource_id": str(resource_id),
                "feature_key": "auto_reply",
                "feature_name": "Automatic Replies",
                "description": "Automated response capabilities",
                "is_default": True,
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "resource_id": str(resource_id),
                "feature_key": "custom_templates",
                "feature_name": "Custom Templates",
                "description": "Create custom message templates",
                "is_default": False,
                "created_at": "2024-01-02T00:00:00Z",
            },
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "resource_id": str(resource_id),
                "feature_key": "analytics_dashboard",
                "feature_name": "Analytics Dashboard",
                "description": "View detailed analytics",
                "is_default": True,
                "created_at": "2024-01-03T00:00:00Z",
            },
        ]
        
        # Filter by is_default if specified
        if is_default is not None:
            sample_features = [
                feature for feature in sample_features
                if feature["is_default"] == is_default
            ]
        
        return sample_features

    def delete_feature(self, feature_id: UUID) -> Dict[str, Any]:
        """Delete a plan resource feature."""
        
        try:
            # This would typically load and delete the actual feature
            return {
                "success": True,
                "feature_id": str(feature_id),
                "message": "Feature deleted successfully",
                "deleted_at": "2024-01-01T00:00:00Z",
            }
            
        except Exception as e:
            return {
                "success": False,
                "feature_id": str(feature_id),
                "message": f"Failed to delete feature: {str(e)}",
            }

    def set_feature_as_default(self, feature_id: UUID) -> Dict[str, Any]:
        """Set a feature as default for the resource."""
        
        try:
            # This would typically load the feature and update it
            return {
                "success": True,
                "feature_id": str(feature_id),
                "is_default": True,
                "message": "Feature set as default successfully",
                "updated_at": "2024-01-01T00:00:00Z",
            }
            
        except Exception as e:
            return {
                "success": False,
                "feature_id": str(feature_id),
                "message": f"Failed to set feature as default: {str(e)}",
            }

    def unset_feature_as_default(self, feature_id: UUID) -> Dict[str, Any]:
        """Unset a feature as default for the resource."""
        
        try:
            # This would typically load the feature and update it
            return {
                "success": True,
                "feature_id": str(feature_id),
                "is_default": False,
                "message": "Feature unset as default successfully",
                "updated_at": "2024-01-01T00:00:00Z",
            }
            
        except Exception as e:
            return {
                "success": False,
                "feature_id": str(feature_id),
                "message": f"Failed to unset feature as default: {str(e)}",
            }

    def bulk_update_features(
        self, resource_id: UUID, feature_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Bulk update multiple features for a resource."""
        
        results = []
        success_count = 0
        error_count = 0
        
        for update in feature_updates:
            feature_id = update.get("feature_id")
            if not feature_id:
                results.append({
                    "feature_id": None,
                    "success": False,
                    "message": "Feature ID is required",
                })
                error_count += 1
                continue
            
            try:
                # Simulate feature update
                results.append({
                    "feature_id": feature_id,
                    "success": True,
                    "message": "Feature updated successfully",
                    "updated_fields": {k: v for k, v in update.items() if k != "feature_id"},
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    "feature_id": feature_id,
                    "success": False,
                    "message": f"Failed to update feature: {str(e)}",
                })
                error_count += 1
        
        return {
            "resource_id": str(resource_id),
            "total_features": len(feature_updates),
            "successful_updates": success_count,
            "failed_updates": error_count,
            "results": results,
            "bulk_update_completed_at": "2024-01-01T00:00:00Z",
        }

    def _build_feature_response(self, feature: PlanResourceFeature) -> Dict[str, Any]:
        """Build feature response dictionary."""
        
        return {
            "id": str(feature.id),
            "resource_id": str(feature.resource_id),
            "feature_key": feature.feature_key,
            "feature_name": feature.feature_name,
            "description": feature.description,
            "is_default": feature.is_default,
            "feature_identifier": feature.get_feature_identifier(),
            "display_name": feature.get_display_name(),
            "created_at": feature.created_at.isoformat(),
            "updated_at": feature.updated_at.isoformat() if feature.updated_at else None,
        }

    def _get_dependency_recommendations(
        self, feature_key: str, issues: List[str]
    ) -> List[str]:
        """Generate dependency recommendations."""
        
        recommendations = []
        
        if issues:
            for issue in issues:
                if "not compatible" in issue.lower():
                    recommendations.append("Consider using this feature with a different resource category")
                elif "requires" in issue.lower():
                    recommendations.append("Ensure all required dependencies are available before enabling this feature")
                elif "conflicts" in issue.lower():
                    recommendations.append("Disable conflicting features before enabling this one")
        else:
            recommendations.append("Feature dependencies are satisfied")
        
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
        if "enabled" not in configuration:
            suggestions.append("Consider adding 'enabled' field to control feature activation")
        
        if "priority" not in configuration:
            suggestions.append("Consider adding 'priority' field for feature ordering")
        
        return suggestions

    def _generate_feature_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights from feature usage patterns."""
        
        insights = []
        
        adoption_rate = patterns.get("adoption_rate", 0)
        user_satisfaction = patterns.get("user_satisfaction", 0)
        support_burden = patterns.get("support_burden", "low")
        
        if adoption_rate > 80:
            insights.append("High adoption rate indicates this is a valuable feature")
        elif adoption_rate < 30:
            insights.append("Low adoption rate - consider improving discoverability or documentation")
        
        if user_satisfaction > 4.0:
            insights.append("High user satisfaction - feature is well-received")
        elif user_satisfaction < 3.0:
            insights.append("Low user satisfaction - consider feature improvements")
        
        if support_burden == "high":
            insights.append("High support burden - consider simplifying configuration or improving documentation")
        elif support_burden == "low":
            insights.append("Low support burden - feature is well-designed and easy to use")
        
        complexity = patterns.get("configuration_complexity", "medium")
        if complexity == "high":
            insights.append("High configuration complexity - consider providing templates or wizards")
        
        return insights