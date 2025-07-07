from typing import Dict, Any, List, Optional, Set
from uuid import UUID

from ..entities.plan_resource_feature import PlanResourceFeature
from ..entities.plan_resource import PlanResource, ResourceCategory


class PlanResourceFeatureService:
    """Domain service for managing plan resource features and their business logic."""

    def create_feature(
        self,
        resource_id: UUID,
        feature_key: str,
        feature_name: str,
        description: Optional[str] = None,
        is_default: bool = False,
    ) -> PlanResourceFeature:
        """Create a new resource feature with validation."""
        
        # Validate feature key format
        if not self._is_valid_feature_key(feature_key):
            raise ValueError(
                "Feature key must be alphanumeric with underscores/hyphens, 3-100 characters"
            )
        
        # Validate feature key uniqueness for the resource
        if self._is_feature_key_taken_for_resource(resource_id, feature_key):
            raise ValueError(f"Feature key '{feature_key}' already exists for this resource")
        
        # Validate business rules
        self._validate_feature_creation_rules(feature_key, feature_name, is_default)
        
        return PlanResourceFeature.create(
            resource_id=resource_id,
            feature_key=feature_key,
            feature_name=feature_name,
            description=description,
            is_default=is_default,
        )

    def validate_feature_dependencies(
        self, feature_key: str, resource_category: ResourceCategory
    ) -> tuple[bool, List[str]]:
        """Validate feature dependencies and conflicts."""
        
        issues = []
        
        # Define feature dependency rules
        dependency_rules = self._get_feature_dependency_rules()
        
        if feature_key in dependency_rules:
            rule = dependency_rules[feature_key]
            
            # Check category compatibility
            if "allowed_categories" in rule:
                if resource_category not in rule["allowed_categories"]:
                    issues.append(
                        f"Feature '{feature_key}' is not compatible with {resource_category.value} resources"
                    )
            
            # Check required dependencies
            if "requires" in rule:
                # This would typically check against existing features
                # For now, just validate the structure
                missing_deps = []  # Would be populated by checking existing features
                if missing_deps:
                    issues.append(
                        f"Feature '{feature_key}' requires: {', '.join(missing_deps)}"
                    )
            
            # Check conflicts
            if "conflicts_with" in rule:
                # This would check against existing features
                conflicts = []  # Would be populated by checking existing features
                if conflicts:
                    issues.append(
                        f"Feature '{feature_key}' conflicts with: {', '.join(conflicts)}"
                    )
        
        return len(issues) == 0, issues

    def get_recommended_features_for_resource(
        self, resource_type: str, resource_category: ResourceCategory
    ) -> List[Dict[str, Any]]:
        """Get recommended features for a specific resource type."""
        
        recommendations = []
        
        # Category-based recommendations
        if resource_category == ResourceCategory.MESSAGING:
            recommendations.extend([
                {
                    "feature_key": "auto_reply",
                    "feature_name": "Automatic Replies",
                    "priority": "high",
                    "is_default": True,
                    "description": "Automated response capabilities",
                    "reason": "Essential for messaging automation"
                },
                {
                    "feature_key": "message_templates",
                    "feature_name": "Message Templates",
                    "priority": "medium",
                    "is_default": False,
                    "description": "Pre-defined message templates",
                    "reason": "Improves efficiency and consistency"
                },
                {
                    "feature_key": "media_support",
                    "feature_name": "Media File Support",
                    "priority": "medium",
                    "is_default": True,
                    "description": "Support for images, videos, and documents",
                    "reason": "Modern messaging requires media support"
                }
            ])
        
        elif resource_category == ResourceCategory.ANALYTICS:
            recommendations.extend([
                {
                    "feature_key": "real_time_dashboard",
                    "feature_name": "Real-time Dashboard",
                    "priority": "high",
                    "is_default": True,
                    "description": "Live analytics and metrics",
                    "reason": "Core analytics functionality"
                },
                {
                    "feature_key": "custom_reports",
                    "feature_name": "Custom Reports",
                    "priority": "medium",
                    "is_default": False,
                    "description": "Build custom analytics reports",
                    "reason": "Advanced analytics capability"
                },
                {
                    "feature_key": "data_export",
                    "feature_name": "Data Export",
                    "priority": "medium",
                    "is_default": False,
                    "description": "Export data in various formats",
                    "reason": "Data portability and integration"
                }
            ])
        
        elif resource_category == ResourceCategory.STORAGE:
            recommendations.extend([
                {
                    "feature_key": "file_encryption",
                    "feature_name": "File Encryption",
                    "priority": "high",
                    "is_default": True,
                    "description": "Encrypt stored files",
                    "reason": "Security requirement for stored data"
                },
                {
                    "feature_key": "version_control",
                    "feature_name": "File Version Control",
                    "priority": "low",
                    "is_default": False,
                    "description": "Track file versions and changes",
                    "reason": "Advanced file management"
                }
            ])
        
        elif resource_category == ResourceCategory.INTEGRATION:
            recommendations.extend([
                {
                    "feature_key": "rate_limiting",
                    "feature_name": "Rate Limiting",
                    "priority": "high",
                    "is_default": True,
                    "description": "API request rate limiting",
                    "reason": "Essential for API stability"
                },
                {
                    "feature_key": "webhook_support",
                    "feature_name": "Webhook Support",
                    "priority": "medium",
                    "is_default": False,
                    "description": "Real-time event notifications",
                    "reason": "Modern integration pattern"
                }
            ])
        
        # Resource type specific recommendations
        type_specific = self._get_type_specific_features(resource_type)
        recommendations.extend(type_specific)
        
        return recommendations

    def validate_feature_configuration(
        self, feature: PlanResourceFeature, configuration: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """Validate feature configuration against business rules."""
        
        issues = []
        
        # Basic configuration validation
        if not isinstance(configuration, dict):
            issues.append("Feature configuration must be a dictionary")
            return False, issues
        
        # Feature-specific validation
        feature_rules = self._get_feature_validation_rules()
        
        if feature.feature_key in feature_rules:
            rules = feature_rules[feature.feature_key]
            
            # Check required fields
            if "required_fields" in rules:
                for field in rules["required_fields"]:
                    if field not in configuration:
                        issues.append(f"Feature '{feature.feature_key}' requires '{field}' configuration")
            
            # Check field types and values
            if "field_validation" in rules:
                for field, validation in rules["field_validation"].items():
                    if field in configuration:
                        value = configuration[field]
                        if not self._validate_field_value(value, validation):
                            issues.append(
                                f"Invalid value for '{field}' in feature '{feature.feature_key}'"
                            )
        
        return len(issues) == 0, issues

    def analyze_feature_usage_patterns(
        self, feature_key: str
    ) -> Dict[str, Any]:
        """Analyze usage patterns for a specific feature."""
        
        # This would typically query actual usage data
        # For now, returning example patterns
        patterns = {
            "feature_key": feature_key,
            "adoption_rate": 0.0,
            "configuration_complexity": "medium",
            "common_configurations": [],
            "user_satisfaction": 0.0,
            "support_burden": "low",
        }
        
        # Example patterns for common features
        if feature_key == "auto_reply":
            patterns.update({
                "adoption_rate": 85.0,
                "configuration_complexity": "medium",
                "common_configurations": [
                    {"enabled": True, "business_hours_only": True},
                    {"enabled": True, "keyword_triggers": ["hello", "help"]}
                ],
                "user_satisfaction": 4.2,
                "support_burden": "low"
            })
        
        elif feature_key == "custom_reports":
            patterns.update({
                "adoption_rate": 35.0,
                "configuration_complexity": "high",
                "common_configurations": [
                    {"template": "monthly_summary", "auto_generate": True},
                    {"custom_metrics": ["response_time", "resolution_rate"]}
                ],
                "user_satisfaction": 4.7,
                "support_burden": "medium"
            })
        
        return patterns

    def suggest_feature_optimizations(
        self, resource_features: List[PlanResourceFeature]
    ) -> List[Dict[str, Any]]:
        """Suggest optimizations for resource features."""
        
        suggestions = []
        
        # Check for too many default features
        default_features = [f for f in resource_features if f.is_default]
        if len(default_features) > 5:
            suggestions.append({
                "type": "too_many_defaults",
                "priority": "medium",
                "title": "Too Many Default Features",
                "description": "Having too many default features may overwhelm users",
                "action": "Review which features should truly be default",
                "impact": "Improved user experience and onboarding"
            })
        
        # Check for missing essential features
        essential_features = {"basic_functionality", "user_management"}
        existing_keys = {f.feature_key for f in resource_features}
        missing_essential = essential_features - existing_keys
        
        if missing_essential:
            suggestions.append({
                "type": "missing_essential",
                "priority": "high",
                "title": "Missing Essential Features",
                "description": f"Essential features missing: {', '.join(missing_essential)}",
                "action": "Add essential features to ensure basic functionality",
                "impact": "Resource may not function properly without these"
            })
        
        # Check for deprecated or unused features
        deprecated_patterns = ["legacy_", "deprecated_", "old_"]
        deprecated_features = [
            f for f in resource_features 
            if any(pattern in f.feature_key for pattern in deprecated_patterns)
        ]
        
        if deprecated_features:
            suggestions.append({
                "type": "deprecated_features",
                "priority": "low",
                "title": "Deprecated Features Found",
                "description": "Some features appear to be deprecated",
                "action": "Consider removing or updating deprecated features",
                "impact": "Cleaner feature set and reduced maintenance"
            })
        
        return suggestions

    def get_feature_compatibility_matrix(
        self, features: List[PlanResourceFeature]
    ) -> Dict[str, Dict[str, str]]:
        """Generate compatibility matrix for features."""
        
        matrix = {}
        
        for feature in features:
            matrix[feature.feature_key] = {}
            
            for other_feature in features:
                if feature.feature_key != other_feature.feature_key:
                    compatibility = self._check_feature_compatibility(
                        feature.feature_key, other_feature.feature_key
                    )
                    matrix[feature.feature_key][other_feature.feature_key] = compatibility
        
        return matrix

    def _is_valid_feature_key(self, feature_key: str) -> bool:
        """Validate feature key format."""
        if not feature_key or len(feature_key) < 3 or len(feature_key) > 100:
            return False
        
        # Only alphanumeric, underscores, and hyphens
        return feature_key.replace("_", "").replace("-", "").isalnum()

    def _is_feature_key_taken_for_resource(self, resource_id: UUID, feature_key: str) -> bool:
        """Check if feature key is already used for the resource."""
        # This would typically check against a feature repository
        # For now, return False to allow creation
        return False

    def _validate_feature_creation_rules(
        self, feature_key: str, feature_name: str, is_default: bool
    ) -> None:
        """Validate feature creation business rules."""
        
        if len(feature_name) < 3 or len(feature_name) > 200:
            raise ValueError("Feature name must be between 3 and 200 characters")
        
        # Default feature rules
        if is_default and feature_key.startswith("advanced_"):
            raise ValueError("Advanced features should typically not be default")

    def _get_feature_dependency_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get feature dependency rules configuration."""
        
        return {
            "auto_reply": {
                "allowed_categories": [ResourceCategory.MESSAGING],
                "requires": ["message_handling"],
                "conflicts_with": []
            },
            "custom_reports": {
                "allowed_categories": [ResourceCategory.ANALYTICS],
                "requires": ["basic_analytics", "data_storage"],
                "conflicts_with": ["simple_analytics_only"]
            },
            "webhook_support": {
                "allowed_categories": [ResourceCategory.INTEGRATION],
                "requires": ["api_access"],
                "conflicts_with": []
            },
            "file_encryption": {
                "allowed_categories": [ResourceCategory.STORAGE],
                "requires": [],
                "conflicts_with": ["unencrypted_storage"]
            },
        }

    def _get_type_specific_features(self, resource_type: str) -> List[Dict[str, Any]]:
        """Get resource type specific feature recommendations."""
        
        features = []
        
        if resource_type == "whatsapp_integration":
            features.extend([
                {
                    "feature_key": "business_hours",
                    "feature_name": "Business Hours Management",
                    "priority": "medium",
                    "is_default": False,
                    "description": "Define business hours for automatic responses",
                    "reason": "Professional WhatsApp business feature"
                },
                {
                    "feature_key": "quick_replies",
                    "feature_name": "Quick Reply Buttons",
                    "priority": "high",
                    "is_default": True,
                    "description": "Interactive quick reply buttons",
                    "reason": "Modern WhatsApp Business API feature"
                }
            ])
        
        elif resource_type == "web_chat":
            features.extend([
                {
                    "feature_key": "custom_styling",
                    "feature_name": "Custom Chat Styling",
                    "priority": "medium",
                    "is_default": False,
                    "description": "Customize chat widget appearance",
                    "reason": "Brand consistency for web chat"
                }
            ])
        
        return features

    def _get_feature_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get feature-specific validation rules."""
        
        return {
            "auto_reply": {
                "required_fields": ["enabled", "message"],
                "field_validation": {
                    "enabled": {"type": "boolean"},
                    "delay_seconds": {"type": "integer", "min": 0, "max": 300}
                }
            },
            "rate_limiting": {
                "required_fields": ["requests_per_minute"],
                "field_validation": {
                    "requests_per_minute": {"type": "integer", "min": 1, "max": 10000}
                }
            },
            "file_encryption": {
                "required_fields": ["algorithm"],
                "field_validation": {
                    "algorithm": {"type": "string", "allowed": ["AES-256", "AES-128"]}
                }
            },
        }

    def _validate_field_value(self, value: Any, validation: Dict[str, Any]) -> bool:
        """Validate a field value against validation rules."""
        
        # Type validation
        if "type" in validation:
            expected_type = validation["type"]
            if expected_type == "boolean" and not isinstance(value, bool):
                return False
            elif expected_type == "integer" and not isinstance(value, int):
                return False
            elif expected_type == "string" and not isinstance(value, str):
                return False
        
        # Range validation for integers
        if isinstance(value, int):
            if "min" in validation and value < validation["min"]:
                return False
            if "max" in validation and value > validation["max"]:
                return False
        
        # Allowed values validation
        if "allowed" in validation and value not in validation["allowed"]:
            return False
        
        return True

    def _check_feature_compatibility(self, feature1: str, feature2: str) -> str:
        """Check compatibility between two features."""
        
        # Define incompatible feature pairs
        incompatible_pairs = {
            ("simple_mode", "advanced_mode"),
            ("encrypted_storage", "unencrypted_storage"),
            ("auto_reply", "manual_reply_only"),
        }
        
        # Check if features are incompatible
        if (feature1, feature2) in incompatible_pairs or (feature2, feature1) in incompatible_pairs:
            return "incompatible"
        
        # Define synergistic feature pairs
        synergistic_pairs = {
            ("auto_reply", "business_hours"),
            ("custom_reports", "data_export"),
            ("webhook_support", "rate_limiting"),
        }
        
        if (feature1, feature2) in synergistic_pairs or (feature2, feature1) in synergistic_pairs:
            return "synergistic"
        
        return "compatible"