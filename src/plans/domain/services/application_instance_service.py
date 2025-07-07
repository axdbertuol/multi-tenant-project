from typing import Dict, Any, List, Optional, Set
from uuid import UUID
import json
import secrets

from ..entities.application_instance import ApplicationInstance
from ..entities.plan_resource import PlanResource
from ..entities.organization_plan import OrganizationPlan


class ApplicationInstanceService:
    """Domain service for managing application instances and their business logic."""

    def provision_instance(
        self,
        plan_resource_id: UUID,
        organization_id: UUID,
        instance_name: str,
        owner_id: UUID,
        initial_configuration: Optional[Dict[str, Any]] = None,
        custom_limits: Optional[Dict[str, int]] = None,
    ) -> ApplicationInstance:
        """Provision a new application instance with validation."""
        
        # Validate instance name
        if not self._is_valid_instance_name(instance_name):
            raise ValueError(
                "Instance name must be 3-200 characters, alphanumeric with spaces/hyphens/underscores"
            )
        
        # Validate configuration if provided
        if initial_configuration:
            is_valid, config_issues = self._validate_configuration(initial_configuration)
            if not is_valid:
                raise ValueError(f"Invalid configuration: {', '.join(config_issues)}")
        
        # Validate custom limits if provided
        if custom_limits:
            is_valid, limit_issues = self._validate_custom_limits(custom_limits)
            if not is_valid:
                raise ValueError(f"Invalid custom limits: {', '.join(limit_issues)}")
        
        return ApplicationInstance.create(
            plan_resource_id=plan_resource_id,
            organization_id=organization_id,
            instance_name=instance_name,
            owner_id=owner_id,
            configuration=initial_configuration,
            limits_override=custom_limits,
        )

    def generate_api_keys(
        self, instance: ApplicationInstance, key_types: List[str]
    ) -> ApplicationInstance:
        """Generate and encrypt API keys for the instance."""
        
        updated_instance = instance
        
        for key_type in key_types:
            # Generate secure API key
            api_key = self._generate_secure_api_key(key_type)
            
            # Encrypt the API key (simplified - in production use proper encryption)
            encrypted_key = self._encrypt_api_key(api_key)
            
            # Set the encrypted key
            updated_instance = updated_instance.set_api_key(key_type, encrypted_key)
        
        return updated_instance

    def validate_instance_configuration(
        self, instance: ApplicationInstance, new_configuration: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """Validate instance configuration against business rules."""
        
        issues = []
        
        # Basic validation
        if not isinstance(new_configuration, dict):
            issues.append("Configuration must be a dictionary")
            return False, issues
        
        # Check for required configuration fields based on resource type
        required_fields = self._get_required_config_fields(instance.plan_resource_id)
        for field in required_fields:
            if field not in new_configuration:
                issues.append(f"Required configuration field '{field}' is missing")
        
        # Validate specific configuration values
        validation_issues = self._validate_configuration_values(new_configuration)
        issues.extend(validation_issues)
        
        # Check configuration size limits
        config_json = json.dumps(new_configuration)
        if len(config_json) > 50000:  # 50KB limit
            issues.append("Configuration is too large (maximum 50KB)")
        
        return len(issues) == 0, issues

    def calculate_effective_limits(
        self,
        instance: ApplicationInstance,
        plan_limits: Dict[str, int],
        organization_plan: OrganizationPlan,
    ) -> Dict[str, int]:
        """Calculate effective limits considering plan, organization, and instance overrides."""
        
        effective_limits = {}
        
        # Start with plan defaults
        for limit_key, plan_value in plan_limits.items():
            effective_value = plan_value
            
            # Apply organization-level overrides
            if limit_key in organization_plan.limit_overrides:
                effective_value = organization_plan.limit_overrides[limit_key]
            
            # Apply instance-level overrides
            if limit_key in instance.limits_override:
                effective_value = instance.limits_override[limit_key]
            
            effective_limits[limit_key] = effective_value
        
        return effective_limits

    def analyze_instance_health(
        self, instance: ApplicationInstance, usage_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze instance health and performance."""
        
        health_status = {
            "instance_id": str(instance.id),
            "overall_health": "healthy",
            "issues": [],
            "recommendations": [],
            "metrics": {
                "uptime_percentage": usage_metrics.get("uptime_percentage", 100.0),
                "error_rate": usage_metrics.get("error_rate", 0.0),
                "response_time_ms": usage_metrics.get("avg_response_time_ms", 0),
                "api_calls_per_day": usage_metrics.get("daily_api_calls", 0),
            },
            "configuration_status": "valid",
            "security_status": "secure",
        }
        
        # Analyze configuration health
        is_config_valid, config_issues = self.validate_instance_configuration(
            instance, instance.configuration
        )
        
        if not is_config_valid:
            health_status["configuration_status"] = "invalid"
            health_status["issues"].extend(config_issues)
            health_status["overall_health"] = "degraded"
        
        # Analyze performance metrics
        uptime = health_status["metrics"]["uptime_percentage"]
        error_rate = health_status["metrics"]["error_rate"]
        response_time = health_status["metrics"]["response_time_ms"]
        
        if uptime < 99.0:
            health_status["issues"].append(f"Low uptime: {uptime:.1f}%")
            health_status["overall_health"] = "critical" if uptime < 95.0 else "degraded"
        
        if error_rate > 5.0:
            health_status["issues"].append(f"High error rate: {error_rate:.1f}%")
            health_status["overall_health"] = "critical" if error_rate > 10.0 else "degraded"
        
        if response_time > 2000:
            health_status["issues"].append(f"Slow response time: {response_time}ms")
            if health_status["overall_health"] == "healthy":
                health_status["overall_health"] = "degraded"
        
        # Generate recommendations
        recommendations = self._generate_health_recommendations(health_status)
        health_status["recommendations"] = recommendations
        
        return health_status

    def suggest_configuration_optimizations(
        self, instance: ApplicationInstance, usage_patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest configuration optimizations based on usage patterns."""
        
        suggestions = []
        
        # Analyze API usage patterns
        api_usage = usage_patterns.get("api_usage", {})
        if api_usage:
            # High API usage suggests need for rate limit optimization
            daily_calls = api_usage.get("daily_average", 0)
            if daily_calls > 10000:
                suggestions.append({
                    "type": "performance_optimization",
                    "priority": "medium",
                    "title": "High API Usage Detected",
                    "description": f"Instance averages {daily_calls:,} API calls per day",
                    "action": "Consider implementing caching or rate limiting optimizations",
                    "config_changes": {
                        "cache_enabled": True,
                        "cache_ttl_seconds": 300,
                        "request_batching": True
                    }
                })
        
        # Analyze storage usage
        storage_usage = usage_patterns.get("storage_usage", {})
        if storage_usage:
            used_mb = storage_usage.get("used_mb", 0)
            limit_mb = instance.get_effective_limit("storage_mb", 1000)
            
            if used_mb > limit_mb * 0.8:  # 80% threshold
                suggestions.append({
                    "type": "resource_optimization",
                    "priority": "high",
                    "title": "Storage Limit Approaching",
                    "description": f"Using {used_mb}MB of {limit_mb}MB storage",
                    "action": "Consider increasing storage limit or implementing cleanup",
                    "config_changes": {
                        "auto_cleanup_enabled": True,
                        "cleanup_older_than_days": 90
                    }
                })
        
        # Analyze feature usage
        feature_usage = usage_patterns.get("feature_usage", {})
        unused_features = [
            feature for feature, used in feature_usage.items() 
            if not used and feature in instance.configuration
        ]
        
        if unused_features:
            suggestions.append({
                "type": "configuration_cleanup",
                "priority": "low",
                "title": "Unused Features Detected",
                "description": f"Features not being used: {', '.join(unused_features)}",
                "action": "Consider disabling unused features to improve performance",
                "config_changes": {
                    feature: False for feature in unused_features
                }
            })
        
        return suggestions

    def validate_instance_migration(
        self,
        instance: ApplicationInstance,
        target_plan_resource_id: UUID,
        target_configuration: Dict[str, Any],
    ) -> tuple[bool, List[str], Dict[str, Any]]:
        """Validate if instance can be migrated to a different resource configuration."""
        
        issues = []
        migration_plan = {
            "source_resource_id": str(instance.plan_resource_id),
            "target_resource_id": str(target_plan_resource_id),
            "configuration_changes": {},
            "data_migration_required": False,
            "estimated_downtime_minutes": 0,
            "compatibility_issues": [],
        }
        
        # Validate target configuration
        is_config_valid, config_issues = self._validate_configuration(target_configuration)
        if not is_config_valid:
            issues.extend(config_issues)
        
        # Check for breaking changes
        breaking_changes = self._detect_breaking_changes(
            instance.configuration, target_configuration
        )
        
        if breaking_changes:
            migration_plan["compatibility_issues"] = breaking_changes
            issues.extend([f"Breaking change: {change}" for change in breaking_changes])
        
        # Estimate migration complexity
        complexity = self._estimate_migration_complexity(
            instance.configuration, target_configuration
        )
        
        migration_plan["estimated_downtime_minutes"] = complexity["downtime_minutes"]
        migration_plan["data_migration_required"] = complexity["requires_data_migration"]
        
        return len(issues) == 0, issues, migration_plan

    def _is_valid_instance_name(self, name: str) -> bool:
        """Validate instance name format."""
        if not name or len(name) < 3 or len(name) > 200:
            return False
        
        # Allow alphanumeric, spaces, hyphens, underscores
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")
        return all(char in allowed_chars for char in name)

    def _validate_configuration(self, configuration: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate configuration structure and values."""
        
        issues = []
        
        # Check for dangerous configurations
        dangerous_keys = ["password", "secret", "private_key", "token"]
        for key in configuration:
            if any(dangerous in key.lower() for dangerous in dangerous_keys):
                issues.append(f"Sensitive data should not be stored in configuration: {key}")
        
        # Validate specific configuration types
        for key, value in configuration.items():
            if key.endswith("_enabled") and not isinstance(value, bool):
                issues.append(f"Configuration '{key}' should be boolean")
            
            elif key.endswith("_count") and not isinstance(value, int):
                issues.append(f"Configuration '{key}' should be integer")
            
            elif key.endswith("_url") and not isinstance(value, str):
                issues.append(f"Configuration '{key}' should be string URL")
        
        return len(issues) == 0, issues

    def _validate_custom_limits(self, limits: Dict[str, int]) -> tuple[bool, List[str]]:
        """Validate custom limit values."""
        
        issues = []
        
        for limit_key, limit_value in limits.items():
            if not isinstance(limit_value, int):
                issues.append(f"Limit '{limit_key}' must be an integer")
                continue
            
            if limit_value < -1:
                issues.append(f"Limit '{limit_key}' must be -1 (unlimited) or non-negative")
            
            # Check for reasonable maximum values
            if limit_value > 1000000000:  # 1 billion
                issues.append(f"Limit '{limit_key}' seems unreasonably high: {limit_value}")
        
        return len(issues) == 0, issues

    def _generate_secure_api_key(self, key_type: str) -> str:
        """Generate a secure API key."""
        # Generate a secure random key
        key_length = 32
        random_bytes = secrets.token_bytes(key_length)
        
        # Create a prefixed API key
        prefix = key_type[:3].upper()
        key = f"{prefix}_{random_bytes.hex()}"
        
        return key

    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key (simplified implementation)."""
        # In production, use proper encryption with a master key
        # This is a simplified example
        import base64
        encoded = base64.b64encode(api_key.encode()).decode()
        return f"encrypted_{encoded}"

    def _get_required_config_fields(self, plan_resource_id: UUID) -> List[str]:
        """Get required configuration fields for a resource type."""
        # This would typically query the resource definition
        # For now, return common required fields
        return ["enabled", "name"]

    def _validate_configuration_values(self, configuration: Dict[str, Any]) -> List[str]:
        """Validate specific configuration values."""
        
        issues = []
        
        # URL validation
        url_fields = [key for key in configuration if key.endswith("_url")]
        for url_field in url_fields:
            url_value = configuration[url_field]
            if isinstance(url_value, str) and not (
                url_value.startswith("http://") or url_value.startswith("https://")
            ):
                issues.append(f"URL field '{url_field}' should start with http:// or https://")
        
        # Port validation
        port_fields = [key for key in configuration if "port" in key.lower()]
        for port_field in port_fields:
            port_value = configuration[port_field]
            if isinstance(port_value, int) and not (1 <= port_value <= 65535):
                issues.append(f"Port field '{port_field}' should be between 1 and 65535")
        
        return issues

    def _generate_health_recommendations(self, health_status: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on status."""
        
        recommendations = []
        
        if health_status["overall_health"] == "critical":
            recommendations.append("Immediate attention required - instance may be down")
            recommendations.append("Check error logs and system status")
            
        elif health_status["overall_health"] == "degraded":
            recommendations.append("Monitor instance closely for further degradation")
            recommendations.append("Consider implementing alerts for key metrics")
        
        # Metric-specific recommendations
        metrics = health_status["metrics"]
        
        if metrics["uptime_percentage"] < 99.0:
            recommendations.append("Investigate uptime issues and improve reliability")
        
        if metrics["error_rate"] > 1.0:
            recommendations.append("Review error logs to identify and fix common issues")
        
        if metrics["response_time_ms"] > 1000:
            recommendations.append("Optimize performance to reduce response times")
        
        return recommendations

    def _detect_breaking_changes(
        self, current_config: Dict[str, Any], target_config: Dict[str, Any]
    ) -> List[str]:
        """Detect breaking changes between configurations."""
        
        breaking_changes = []
        
        # Check for removed required fields
        current_keys = set(current_config.keys())
        target_keys = set(target_config.keys())
        removed_keys = current_keys - target_keys
        
        required_keys = {"enabled", "name"}  # Example required keys
        removed_required = removed_keys & required_keys
        
        if removed_required:
            breaking_changes.extend([
                f"Required configuration '{key}' will be removed" for key in removed_required
            ])
        
        # Check for incompatible value changes
        for key in current_keys & target_keys:
            current_value = current_config[key]
            target_value = target_config[key]
            
            if type(current_value) != type(target_value):
                breaking_changes.append(
                    f"Configuration '{key}' type change: {type(current_value).__name__} → {type(target_value).__name__}"
                )
        
        return breaking_changes

    def _estimate_migration_complexity(
        self, current_config: Dict[str, Any], target_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate migration complexity and requirements."""
        
        # Simple complexity estimation
        config_changes = len(set(current_config.keys()) ^ set(target_config.keys()))
        value_changes = sum(
            1 for key in set(current_config.keys()) & set(target_config.keys())
            if current_config[key] != target_config[key]
        )
        
        total_changes = config_changes + value_changes
        
        if total_changes <= 2:
            complexity = "low"
            downtime_minutes = 1
            requires_data_migration = False
        elif total_changes <= 5:
            complexity = "medium"
            downtime_minutes = 5
            requires_data_migration = False
        else:
            complexity = "high"
            downtime_minutes = 15
            requires_data_migration = True
        
        return {
            "complexity": complexity,
            "downtime_minutes": downtime_minutes,
            "requires_data_migration": requires_data_migration,
            "total_changes": total_changes,
        }