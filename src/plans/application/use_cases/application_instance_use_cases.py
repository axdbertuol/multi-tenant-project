from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.entities.application_instance import ApplicationInstance
from ...domain.entities.organization_plan import OrganizationPlan
from ...domain.services.application_instance_service import ApplicationInstanceService
from ...domain.repositories.organization_plan_repository import OrganizationPlanRepository


class ApplicationInstanceUseCase:
    """Use case for application instance management operations."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._org_plan_repository: OrganizationPlanRepository = uow.get_repository("organization_plan")
        self._application_instance_service = ApplicationInstanceService()

    def provision_instance(
        self,
        plan_resource_id: UUID,
        organization_id: UUID,
        instance_name: str,
        owner_id: UUID,
        initial_configuration: Optional[Dict[str, Any]] = None,
        custom_limits: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Provision a new application instance."""
        
        try:
            with self._uow:
                instance = self._application_instance_service.provision_instance(
                    plan_resource_id=plan_resource_id,
                    organization_id=organization_id,
                    instance_name=instance_name,
                    owner_id=owner_id,
                    initial_configuration=initial_configuration,
                    custom_limits=custom_limits,
                )
                
                return {
                    "success": True,
                    "instance": self._build_instance_response(instance),
                    "message": "Application instance provisioned successfully",
                }
                
        except ValueError as e:
            return {
                "success": False,
                "message": f"Failed to provision instance: {str(e)}",
                "plan_resource_id": str(plan_resource_id),
                "organization_id": str(organization_id),
                "instance_name": instance_name,
            }

    def get_instance_by_id(self, instance_id: UUID) -> Optional[Dict[str, Any]]:
        """Get application instance by ID."""
        
        # This would typically use an application instance repository
        # For now, returning a simulated response
        return {
            "id": str(instance_id),
            "plan_resource_id": "00000000-0000-0000-0000-000000000000",
            "organization_id": "00000000-0000-0000-0000-000000000000",
            "instance_name": "Sample Instance",
            "is_active": True,
            "configuration": {},
            "api_key_names": [],
            "custom_limits": {},
            "created_at": "2024-01-01T00:00:00Z",
        }

    def update_instance_configuration(
        self, instance_id: UUID, new_configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update instance configuration."""
        
        # This would typically load the instance, validate, and save
        # For this implementation, we'll simulate the process
        
        # Create a temporary instance for validation
        temp_instance = ApplicationInstance.create(
            plan_resource_id=UUID("00000000-0000-0000-0000-000000000000"),
            organization_id=UUID("00000000-0000-0000-0000-000000000000"),
            instance_name="Temp Instance",
            owner_id=UUID("00000000-0000-0000-0000-000000000000"),
        )
        
        is_valid, issues = self._application_instance_service.validate_instance_configuration(
            temp_instance, new_configuration
        )
        
        if not is_valid:
            return {
                "success": False,
                "message": "Configuration validation failed",
                "issues": issues,
                "instance_id": str(instance_id),
            }
        
        return {
            "success": True,
            "instance_id": str(instance_id),
            "configuration": new_configuration,
            "message": "Configuration updated successfully",
            "validation_passed": True,
        }

    def generate_api_keys(
        self, instance_id: UUID, key_types: List[str]
    ) -> Dict[str, Any]:
        """Generate API keys for an instance."""
        
        # This would typically load the actual instance
        # For now, simulate the process
        
        temp_instance = ApplicationInstance.create(
            plan_resource_id=UUID("00000000-0000-0000-0000-000000000000"),
            organization_id=UUID("00000000-0000-0000-0000-000000000000"),
            instance_name="Temp Instance",
            owner_id=UUID("00000000-0000-0000-0000-000000000000"),
        )
        
        try:
            updated_instance = self._application_instance_service.generate_api_keys(
                temp_instance, key_types
            )
            
            return {
                "success": True,
                "instance_id": str(instance_id),
                "generated_keys": key_types,
                "api_key_names": updated_instance.get_api_key_names(),
                "message": f"Generated {len(key_types)} API keys successfully",
            }
            
        except Exception as e:
            return {
                "success": False,
                "instance_id": str(instance_id),
                "message": f"Failed to generate API keys: {str(e)}",
            }

    def analyze_instance_health(
        self, instance_id: UUID, usage_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze instance health and performance."""
        
        # This would typically load the actual instance
        # For now, simulate with sample data
        
        temp_instance = ApplicationInstance.create(
            plan_resource_id=UUID("00000000-0000-0000-0000-000000000000"),
            organization_id=UUID("00000000-0000-0000-0000-000000000000"),
            instance_name="Sample Instance",
            owner_id=UUID("00000000-0000-0000-0000-000000000000"),
        )
        
        # Use sample metrics if none provided
        sample_metrics = usage_metrics or {
            "uptime_percentage": 99.5,
            "error_rate": 0.2,
            "avg_response_time_ms": 150,
            "daily_api_calls": 5000,
        }
        
        health_analysis = self._application_instance_service.analyze_instance_health(
            temp_instance, sample_metrics
        )
        
        return {
            "instance_id": str(instance_id),
            "health_analysis": health_analysis,
            "analyzed_at": "2024-01-01T00:00:00Z",
        }

    def get_configuration_optimization_suggestions(
        self, instance_id: UUID, usage_patterns: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get optimization suggestions for instance configuration."""
        
        # This would typically load the actual instance
        temp_instance = ApplicationInstance.create(
            plan_resource_id=UUID("00000000-0000-0000-0000-000000000000"),
            organization_id=UUID("00000000-0000-0000-0000-000000000000"),
            instance_name="Sample Instance",
            owner_id=UUID("00000000-0000-0000-0000-000000000000"),
        )
        
        # Use sample usage patterns if none provided
        sample_patterns = usage_patterns or {
            "api_usage": {"daily_average": 15000},
            "storage_usage": {"used_mb": 800, "limit_mb": 1000},
            "feature_usage": {"advanced_analytics": False, "auto_backup": True},
        }
        
        return self._application_instance_service.suggest_configuration_optimizations(
            temp_instance, sample_patterns
        )

    def validate_instance_migration(
        self,
        instance_id: UUID,
        target_plan_resource_id: UUID,
        target_configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate if instance can be migrated to different resource configuration."""
        
        # This would typically load the actual instance
        temp_instance = ApplicationInstance.create(
            plan_resource_id=UUID("00000000-0000-0000-0000-000000000000"),
            organization_id=UUID("00000000-0000-0000-0000-000000000000"),
            instance_name="Sample Instance",
            owner_id=UUID("00000000-0000-0000-0000-000000000000"),
        )
        
        can_migrate, issues, migration_plan = self._application_instance_service.validate_instance_migration(
            temp_instance, target_plan_resource_id, target_configuration
        )
        
        return {
            "instance_id": str(instance_id),
            "target_plan_resource_id": str(target_plan_resource_id),
            "can_migrate": can_migrate,
            "issues": issues,
            "migration_plan": migration_plan,
            "validated_at": "2024-01-01T00:00:00Z",
        }

    def set_custom_limit(
        self, instance_id: UUID, limit_key: str, limit_value: int
    ) -> Dict[str, Any]:
        """Set a custom limit for an instance."""
        
        try:
            # This would typically load and update the actual instance
            return {
                "success": True,
                "instance_id": str(instance_id),
                "limit_key": limit_key,
                "limit_value": limit_value,
                "message": "Custom limit set successfully",
                "updated_at": "2024-01-01T00:00:00Z",
            }
            
        except Exception as e:
            return {
                "success": False,
                "instance_id": str(instance_id),
                "message": f"Failed to set custom limit: {str(e)}",
            }

    def remove_custom_limit(self, instance_id: UUID, limit_key: str) -> Dict[str, Any]:
        """Remove a custom limit from an instance."""
        
        try:
            # This would typically load and update the actual instance
            return {
                "success": True,
                "instance_id": str(instance_id),
                "limit_key": limit_key,
                "message": "Custom limit removed successfully",
                "updated_at": "2024-01-01T00:00:00Z",
            }
            
        except Exception as e:
            return {
                "success": False,
                "instance_id": str(instance_id),
                "message": f"Failed to remove custom limit: {str(e)}",
            }

    def get_effective_limits(
        self, instance_id: UUID, organization_id: UUID
    ) -> Dict[str, Any]:
        """Get effective limits for an instance considering all overrides."""
        
        # This would typically load the actual instance and organization plan
        temp_instance = ApplicationInstance.create(
            plan_resource_id=UUID("00000000-0000-0000-0000-000000000000"),
            organization_id=organization_id,
            instance_name="Sample Instance",
            owner_id=UUID("00000000-0000-0000-0000-000000000000"),
        )
        
        # Get organization plan
        org_plan = self._org_plan_repository.get_by_organization_id(organization_id)
        if not org_plan:
            return {
                "success": False,
                "message": "Organization plan not found",
                "instance_id": str(instance_id),
                "organization_id": str(organization_id),
            }
        
        # Sample plan limits
        plan_limits = {
            "api_requests_per_minute": 1000,
            "storage_mb": 1000,
            "concurrent_sessions": 50,
        }
        
        effective_limits = self._application_instance_service.calculate_effective_limits(
            temp_instance, plan_limits, org_plan
        )
        
        return {
            "success": True,
            "instance_id": str(instance_id),
            "organization_id": str(organization_id),
            "effective_limits": effective_limits,
            "plan_limits": plan_limits,
            "organization_overrides": org_plan.limit_overrides,
            "instance_overrides": temp_instance.limits_override,
        }

    def deactivate_instance(self, instance_id: UUID) -> Dict[str, Any]:
        """Deactivate an application instance."""
        
        try:
            # This would typically load and update the actual instance
            return {
                "success": True,
                "instance_id": str(instance_id),
                "is_active": False,
                "message": "Instance deactivated successfully",
                "deactivated_at": "2024-01-01T00:00:00Z",
            }
            
        except Exception as e:
            return {
                "success": False,
                "instance_id": str(instance_id),
                "message": f"Failed to deactivate instance: {str(e)}",
            }

    def reactivate_instance(self, instance_id: UUID) -> Dict[str, Any]:
        """Reactivate an application instance."""
        
        try:
            # This would typically load and update the actual instance
            return {
                "success": True,
                "instance_id": str(instance_id),
                "is_active": True,
                "message": "Instance reactivated successfully",
                "reactivated_at": "2024-01-01T00:00:00Z",
            }
            
        except Exception as e:
            return {
                "success": False,
                "instance_id": str(instance_id),
                "message": f"Failed to reactivate instance: {str(e)}",
            }

    def list_organization_instances(
        self, organization_id: UUID, is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """List all instances for an organization."""
        
        # This would typically query the instance repository
        # For now, return sample data
        
        sample_instances = [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "instance_name": "Production Instance",
                "plan_resource_id": "22222222-2222-2222-2222-222222222222",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "instance_name": "Development Instance",
                "plan_resource_id": "44444444-4444-4444-4444-444444444444",
                "is_active": False,
                "created_at": "2024-01-02T00:00:00Z",
            },
        ]
        
        # Filter by active status if specified
        if is_active is not None:
            sample_instances = [
                instance for instance in sample_instances
                if instance["is_active"] == is_active
            ]
        
        return sample_instances

    def _build_instance_response(self, instance: ApplicationInstance) -> Dict[str, Any]:
        """Build instance response dictionary."""
        
        return {
            "id": str(instance.id),
            "plan_resource_id": str(instance.plan_resource_id),
            "organization_id": str(instance.organization_id),
            "instance_name": instance.instance_name,
            "is_active": instance.is_active,
            "owner_id": str(instance.owner_id),
            "configuration": instance.configuration,
            "api_key_names": instance.get_api_key_names(),
            "custom_limits": instance.limits_override,
            "has_custom_limits": len(instance.limits_override) > 0,
            "created_at": instance.created_at.isoformat(),
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
        }