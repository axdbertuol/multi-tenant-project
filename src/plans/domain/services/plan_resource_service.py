from typing import Dict, Any, List, Optional, Set
from uuid import UUID

from ..entities.plan_resource import PlanResource, ResourceCategory
from ..entities.plan import Plan
from ..repositories.plan_repository import PlanRepository


class PlanResourceService:
    """Domain service for managing plan resources and their business logic."""

    def __init__(self, plan_repository: PlanRepository):
        self._plan_repository = plan_repository

    def create_resource(
        self,
        resource_type: str,
        name: str,
        category: ResourceCategory,
        created_by: UUID,
        description: Optional[str] = None,
    ) -> PlanResource:
        """Create a new plan resource with validation."""
        
        # Validate resource type uniqueness
        if self._is_resource_type_taken(resource_type):
            raise ValueError(f"Resource type '{resource_type}' already exists")
        
        # Validate resource type format
        if not self._is_valid_resource_type(resource_type):
            raise ValueError(
                "Resource type must be alphanumeric with underscores, 3-50 characters"
            )
        
        # Validate business rules
        self._validate_resource_creation_rules(resource_type, name, category)
        
        return PlanResource.create(
            resource_type=resource_type,
            name=name,
            category=category,
            created_by=created_by,
            description=description,
        )

    def validate_resource_type_compatibility(
        self, resource_type: str, plan_type: str
    ) -> tuple[bool, List[str]]:
        """Validate if a resource type is compatible with a plan type."""
        
        compatibility_issues = []
        
        # Define compatibility rules
        basic_plan_restrictions = {
            "whatsapp_integration",
            "advanced_analytics",
            "custom_branding",
            "api_access_premium",
            "white_label",
        }
        
        premium_plan_restrictions = {
            "enterprise_sso",
            "custom_deployment",
            "dedicated_support",
        }
        
        # Check restrictions based on plan type
        if plan_type == "basic" and resource_type in basic_plan_restrictions:
            compatibility_issues.append(
                f"Resource '{resource_type}' is not available in basic plans"
            )
        
        if plan_type in ["basic", "premium"] and resource_type in premium_plan_restrictions:
            compatibility_issues.append(
                f"Resource '{resource_type}' is only available in enterprise plans"
            )
        
        # Category-based restrictions
        if plan_type == "basic" and resource_type.startswith("enterprise_"):
            compatibility_issues.append(
                "Enterprise-level resources are not compatible with basic plans"
            )
        
        return len(compatibility_issues) == 0, compatibility_issues

    def get_recommended_resources_for_category(
        self, category: ResourceCategory, plan_type: str
    ) -> List[Dict[str, Any]]:
        """Get recommended resources for a specific category and plan type."""
        
        recommendations = []
        
        if category == ResourceCategory.MESSAGING:
            if plan_type in ["premium", "enterprise"]:
                recommendations.extend([
                    {
                        "resource_type": "whatsapp_integration",
                        "name": "WhatsApp Business Integration",
                        "priority": "high",
                        "reason": "Essential for multi-channel communication"
                    },
                    {
                        "resource_type": "sms_integration",
                        "name": "SMS Integration",
                        "priority": "medium",
                        "reason": "Broader reach for notifications"
                    }
                ])
            
            recommendations.append({
                "resource_type": "web_chat",
                "name": "Web Chat Widget",
                "priority": "high",
                "reason": "Core messaging functionality"
            })
        
        elif category == ResourceCategory.ANALYTICS:
            recommendations.extend([
                {
                    "resource_type": "basic_analytics",
                    "name": "Basic Analytics Dashboard",
                    "priority": "high",
                    "reason": "Essential for understanding usage"
                },
                {
                    "resource_type": "conversation_analytics",
                    "name": "Conversation Analytics",
                    "priority": "medium",
                    "reason": "Insights into communication patterns"
                }
            ])
            
            if plan_type == "enterprise":
                recommendations.append({
                    "resource_type": "advanced_analytics",
                    "name": "Advanced Analytics & BI",
                    "priority": "medium",
                    "reason": "Enterprise-level insights and reporting"
                })
        
        elif category == ResourceCategory.STORAGE:
            storage_limits = {
                "basic": "5GB",
                "premium": "50GB", 
                "enterprise": "Unlimited"
            }
            
            recommendations.append({
                "resource_type": "file_storage",
                "name": f"File Storage ({storage_limits.get(plan_type, '5GB')})",
                "priority": "high",
                "reason": "Required for media and document handling"
            })
        
        elif category == ResourceCategory.INTEGRATION:
            if plan_type in ["premium", "enterprise"]:
                recommendations.extend([
                    {
                        "resource_type": "api_access",
                        "name": "REST API Access",
                        "priority": "high",
                        "reason": "Essential for system integrations"
                    },
                    {
                        "resource_type": "webhook_support",
                        "name": "Webhook Support",
                        "priority": "medium",
                        "reason": "Real-time integration capabilities"
                    }
                ])
            
            if plan_type == "enterprise":
                recommendations.append({
                    "resource_type": "custom_integrations",
                    "name": "Custom Integration Support",
                    "priority": "low",
                    "reason": "Tailored integration solutions"
                })
        
        return recommendations

    def analyze_resource_dependencies(
        self, resource_type: str
    ) -> Dict[str, Any]:
        """Analyze dependencies and conflicts for a resource."""
        
        analysis = {
            "dependencies": [],
            "conflicts": [],
            "recommendations": [],
            "required_features": [],
            "optional_features": [],
        }
        
        # Define dependency rules
        dependency_map = {
            "whatsapp_integration": {
                "dependencies": ["messaging_core", "file_storage"],
                "required_features": ["message_handling", "media_support"],
                "conflicts": ["basic_messaging_only"],
            },
            "advanced_analytics": {
                "dependencies": ["basic_analytics", "data_storage"],
                "required_features": ["reporting", "data_export"],
                "conflicts": [],
            },
            "api_access": {
                "dependencies": ["authentication_service"],
                "required_features": ["rate_limiting", "api_key_management"],
                "conflicts": ["api_disabled"],
            },
            "white_label": {
                "dependencies": ["custom_branding"],
                "required_features": ["theme_customization", "logo_upload"],
                "conflicts": ["standard_branding"],
            },
        }
        
        resource_config = dependency_map.get(resource_type, {})
        
        analysis["dependencies"] = resource_config.get("dependencies", [])
        analysis["conflicts"] = resource_config.get("conflicts", [])
        analysis["required_features"] = resource_config.get("required_features", [])
        
        # Generate recommendations based on dependencies
        if analysis["dependencies"]:
            analysis["recommendations"].append(
                f"Ensure the following resources are available: {', '.join(analysis['dependencies'])}"
            )
        
        if analysis["conflicts"]:
            analysis["recommendations"].append(
                f"Remove conflicting resources: {', '.join(analysis['conflicts'])}"
            )
        
        return analysis

    def validate_resource_configuration(
        self, resource: PlanResource, configuration: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """Validate resource configuration against business rules."""
        
        issues = []
        
        # Basic configuration validation
        if not isinstance(configuration, dict):
            issues.append("Resource configuration must be a dictionary")
            return False, issues
        
        # Category-specific validation
        if resource.category == ResourceCategory.MESSAGING:
            issues.extend(self._validate_messaging_config(configuration))
        
        elif resource.category == ResourceCategory.ANALYTICS:
            issues.extend(self._validate_analytics_config(configuration))
        
        elif resource.category == ResourceCategory.STORAGE:
            issues.extend(self._validate_storage_config(configuration))
        
        elif resource.category == ResourceCategory.INTEGRATION:
            issues.extend(self._validate_integration_config(configuration))
        
        # Resource type specific validation
        type_issues = self._validate_resource_type_config(resource.resource_type, configuration)
        issues.extend(type_issues)
        
        return len(issues) == 0, issues

    def get_resource_usage_patterns(
        self, resource_type: str
    ) -> Dict[str, Any]:
        """Analyze usage patterns for a resource type across plans."""
        
        # This would typically query actual usage data
        # For now, returning example patterns
        patterns = {
            "resource_type": resource_type,
            "adoption_rate": 0.0,
            "average_configuration_complexity": "medium",
            "common_configurations": [],
            "performance_metrics": {},
            "user_feedback": [],
        }
        
        # Example patterns for different resource types
        if resource_type == "whatsapp_integration":
            patterns.update({
                "adoption_rate": 75.0,
                "average_configuration_complexity": "high",
                "common_configurations": [
                    {"auto_reply": True, "business_hours": True},
                    {"template_messages": True, "media_support": True}
                ],
                "performance_metrics": {
                    "average_setup_time_minutes": 15,
                    "success_rate": 92.0,
                    "support_tickets_per_month": 2.3
                }
            })
        
        elif resource_type == "web_chat":
            patterns.update({
                "adoption_rate": 95.0,
                "average_configuration_complexity": "low",
                "common_configurations": [
                    {"theme": "default", "position": "bottom-right"},
                    {"custom_css": False, "file_upload": True}
                ],
                "performance_metrics": {
                    "average_setup_time_minutes": 3,
                    "success_rate": 98.5,
                    "support_tickets_per_month": 0.1
                }
            })
        
        return patterns

    def suggest_resource_optimizations(
        self, plan: Plan
    ) -> List[Dict[str, Any]]:
        """Suggest optimizations for plan resources."""
        
        suggestions = []
        
        # Analyze current resource configuration
        enabled_resources = [
            resource_type for resource_type, config in plan.resources.items()
            if config.get("enabled", False)
        ]
        
        # Check for missing essential resources
        essential_resources = {"management_app", "web_chat", "file_storage"}
        missing_essential = essential_resources - set(enabled_resources)
        
        for resource in missing_essential:
            suggestions.append({
                "type": "missing_essential",
                "priority": "high",
                "resource": resource,
                "action": "enable",
                "reason": f"Essential resource '{resource}' is not enabled",
                "impact": "May limit plan functionality and user satisfaction"
            })
        
        # Check for redundant resources
        redundant_pairs = [
            ("basic_analytics", "advanced_analytics"),
            ("basic_storage", "premium_storage"),
        ]
        
        for basic, advanced in redundant_pairs:
            if basic in enabled_resources and advanced in enabled_resources:
                suggestions.append({
                    "type": "redundant_resource",
                    "priority": "medium",
                    "resource": basic,
                    "action": "disable",
                    "reason": f"'{basic}' is redundant when '{advanced}' is enabled",
                    "impact": "Reduces plan complexity and potential confusion"
                })
        
        # Check for plan type mismatches
        if plan.plan_type.value == "basic":
            enterprise_resources = [r for r in enabled_resources if r.startswith("enterprise_")]
            for resource in enterprise_resources:
                suggestions.append({
                    "type": "plan_type_mismatch",
                    "priority": "high",
                    "resource": resource,
                    "action": "disable",
                    "reason": f"Enterprise resource '{resource}' should not be in basic plan",
                    "impact": "Maintains proper plan tiering and pricing strategy"
                })
        
        return suggestions

    def _is_resource_type_taken(self, resource_type: str) -> bool:
        """Check if resource type is already in use."""
        # This would typically check against a resource repository
        # For now, return False to allow creation
        return False

    def _is_valid_resource_type(self, resource_type: str) -> bool:
        """Validate resource type format."""
        if not resource_type or len(resource_type) < 3 or len(resource_type) > 50:
            return False
        
        # Only alphanumeric and underscores
        return resource_type.replace("_", "").isalnum()

    def _validate_resource_creation_rules(
        self, resource_type: str, name: str, category: ResourceCategory
    ) -> None:
        """Validate resource creation business rules."""
        
        if len(name) < 3 or len(name) > 100:
            raise ValueError("Resource name must be between 3 and 100 characters")
        
        # Category-specific rules
        if category == ResourceCategory.MESSAGING and not resource_type.endswith(("_chat", "_messaging", "_integration")):
            raise ValueError("Messaging resources should have descriptive suffixes")
        
        if category == ResourceCategory.STORAGE and "storage" not in resource_type.lower():
            raise ValueError("Storage resources should include 'storage' in the type")

    def _validate_messaging_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate messaging resource configuration."""
        issues = []
        
        if "enabled" not in config:
            issues.append("Messaging resources must have 'enabled' field")
        
        if config.get("enabled") and not config.get("api_keys"):
            issues.append("Enabled messaging resources require API key configuration")
        
        return issues

    def _validate_analytics_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate analytics resource configuration."""
        issues = []
        
        if config.get("enabled") and not config.get("dashboard_access"):
            issues.append("Analytics resources should specify dashboard access")
        
        return issues

    def _validate_storage_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate storage resource configuration."""
        issues = []
        
        if config.get("enabled"):
            if not config.get("limits", {}).get("storage_gb"):
                issues.append("Storage resources must specify storage limits")
        
        return issues

    def _validate_integration_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate integration resource configuration."""
        issues = []
        
        if config.get("enabled"):
            if not config.get("api_endpoints") and not config.get("webhook_urls"):
                issues.append("Integration resources should specify endpoints or webhooks")
        
        return issues

    def _validate_resource_type_config(
        self, resource_type: str, config: Dict[str, Any]
    ) -> List[str]:
        """Validate configuration for specific resource types."""
        issues = []
        
        if resource_type == "whatsapp_integration":
            if config.get("enabled") and not config.get("api_keys", {}).get("whatsapp_api_key"):
                issues.append("WhatsApp integration requires API key")
        
        elif resource_type == "web_chat":
            if config.get("enabled"):
                limits = config.get("limits", {})
                if not limits.get("concurrent_sessions"):
                    issues.append("Web chat requires concurrent session limit")
        
        return issues