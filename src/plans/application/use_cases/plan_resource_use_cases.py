from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.entities.plan_resource import PlanResource
from ...domain.repositories.plan_resource_repository import PlanResourceRepository
from ...domain.repositories.plan_repository import PlanRepository
from ...domain.services.plan_resource_service import PlanResourceService
from ..dtos.plan_resource_dto import (
    PlanResourceCreateDTO,
    PlanResourceUpdateDTO,
    PlanResourceResponseDTO,
    PlanResourceListResponseDTO,
    PlanResourceTestDTO,
    PlanResourceTestResponseDTO,
    PlanResourceUsageDTO,
    PlanResourceUsageResponseDTO,
)


class PlanResourceUseCase:
    """Use case for plan resource management operations."""

    def __init__(
        self,
        plan_resource_repository: PlanResourceRepository,
        plan_repository: PlanRepository,
        plan_resource_service: PlanResourceService,
    ):
        self.plan_resource_repository = plan_resource_repository
        self.plan_repository = plan_repository
        self.plan_resource_service = plan_resource_service

    def create_plan_resource(
        self, dto: PlanResourceCreateDTO
    ) -> PlanResourceResponseDTO:
        """Create a new plan resource."""
        # Validate plan exists
        plan = self.plan_repository.find_by_id(dto.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        # Check if resource already exists for this plan
        existing = self.plan_resource_repository.find_by_plan_and_type(
            dto.plan_id, dto.resource_type
        )
        if existing:
            raise ValueError(
                f"Resource {dto.resource_type} already exists for this plan"
            )

        # Create resource using factory method
        resource = PlanResource.create_resource(
            plan_id=dto.plan_id,
            resource_type=dto.resource_type,
            configuration=dto.configuration,
            is_enabled=dto.is_enabled,
        )

        # Save resource
        saved_resource = self.plan_resource_repository.save(resource)

        return self._build_resource_response(saved_resource)

    def get_resource_by_id(
        self, resource_id: UUID
    ) -> Optional[PlanResourceResponseDTO]:
        """Get plan resource by ID."""
        resource = self.plan_resource_repository.find_by_id(resource_id)
        if not resource:
            return None

        return self._build_resource_response(resource)

    def update_plan_resource(
        self, resource_id: UUID, dto: PlanResourceUpdateDTO
    ) -> Optional[PlanResourceResponseDTO]:
        """Update an existing plan resource."""
        with self._uow:
            resource = self._plan_resource_repository.find_by_id(resource_id)
            if not resource:
                return None

            # Update fields
            if dto.configuration is not None:
                # Validate configuration based on resource type
                validated_config = self._plan_resource_service.validate_configuration(
                    resource.resource_type, dto.configuration
                )
                resource.configuration = validated_config

            if dto.is_enabled is not None:
                resource.is_enabled = dto.is_enabled

            resource.updated_at = datetime.now(timezone.utc)

            # Save resource
            updated_resource = self._plan_resource_repository.save(resource)

        return self._build_resource_response(updated_resource)

    def delete_plan_resource(self, resource_id: UUID) -> bool:
        """Delete a plan resource."""
        with self._uow:
            resource = self._plan_resource_repository.find_by_id(resource_id)
            if not resource:
                return False

            # Check if resource is being used
            usage_count = self._plan_resource_repository.get_usage_count(resource_id)
            if usage_count > 0:
                # Soft delete if in use
                resource.is_enabled = False
                resource.updated_at = datetime.now(timezone.utc)
                self._plan_resource_repository.save(resource)
            else:
                # Hard delete if not in use
                self._plan_resource_repository.delete(resource_id)

        return True

    def list_plan_resources(
        self,
        plan_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PlanResourceListResponseDTO:
        """List plan resources with pagination and filters."""
        offset = (page - 1) * page_size

        resources, total = self.plan_resource_repository.find_paginated(
            plan_id=plan_id,
            resource_type=resource_type,
            is_enabled=is_enabled,
            offset=offset,
            limit=page_size,
        )

        resource_responses = []
        for resource in resources:
            resource_responses.append(self._build_resource_response(resource))

        total_pages = (total + page_size - 1) // page_size

        return PlanResourceListResponseDTO(
            resources=resource_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_plan_resources(self, plan_id: UUID) -> List[PlanResourceResponseDTO]:
        """Get all resources for a specific plan."""
        resources = self.plan_resource_repository.find_by_plan(plan_id)

        resource_responses = []
        for resource in resources:
            resource_responses.append(self._build_resource_response(resource))

        return resource_responses

    def test_resource_configuration(
        self, dto: PlanResourceTestDTO
    ) -> PlanResourceTestResponseDTO:
        """Test a plan resource configuration."""
        start_time = datetime.now(timezone.utc)

        try:
            # Test the configuration
            test_results = self.plan_resource_service.test_configuration(
                resource_type=dto.resource_type,
                configuration=dto.test_configuration,
                test_parameters=dto.test_parameters,
            )

            end_time = datetime.now(timezone.utc)
            test_duration = (end_time - start_time).total_seconds() * 1000

            # Generate recommendations based on test results
            recommendations = self._generate_configuration_recommendations(
                dto.resource_type, dto.test_configuration, test_results
            )

            return PlanResourceTestResponseDTO(
                success=test_results.get("success", False),
                resource_type=dto.resource_type,
                test_results=test_results,
                performance_metrics={"test_duration_ms": test_duration},
                recommendations=recommendations,
            )

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            test_duration = (end_time - start_time).total_seconds() * 1000

            return PlanResourceTestResponseDTO(
                success=False,
                resource_type=dto.resource_type,
                test_results={},
                error_message=str(e),
                performance_metrics={"test_duration_ms": test_duration},
            )

    def record_resource_usage(self, dto: PlanResourceUsageDTO) -> bool:
        """Record usage of a plan resource."""
        return self.plan_resource_repository.record_usage(
            resource_id=dto.resource_id,
            organization_id=dto.organization_id,
            usage_date=dto.usage_date,
            usage_count=dto.usage_count,
            usage_details=dto.usage_details,
            cost=dto.cost,
        )

    def get_resource_usage(
        self, resource_id: UUID, start_date: datetime, end_date: datetime
    ) -> PlanResourceUsageResponseDTO:
        """Get usage statistics for a plan resource."""
        usage_data = self.plan_resource_repository.get_usage_statistics(
            resource_id=resource_id, start_date=start_date, end_date=end_date
        )

        resource = self.plan_resource_repository.find_by_id(resource_id)
        resource_type = resource.resource_type if resource else "Unknown"

        return PlanResourceUsageResponseDTO(
            resource_id=resource_id,
            resource_type=resource_type,
            total_usage=usage_data.get("total_usage", 0),
            usage_period=f"{start_date.date()} to {end_date.date()}",
            usage_breakdown=usage_data.get("breakdown", {}),
            cost_breakdown=usage_data.get("costs", {}),
            usage_trends=usage_data.get("trends", []),
        )

    def enable_resource(self, resource_id: UUID) -> Optional[PlanResourceResponseDTO]:
        """Enable a plan resource."""
        with self._uow:
            resource = self._plan_resource_repository.find_by_id(resource_id)
            if not resource:
                return None

            resource.is_enabled = True
            resource.updated_at = datetime.now(timezone.utc)

            updated_resource = self._plan_resource_repository.save(resource)

        return self._build_resource_response(updated_resource)

    def disable_resource(self, resource_id: UUID) -> Optional[PlanResourceResponseDTO]:
        """Disable a plan resource."""
        with self._uow:
            resource = self._plan_resource_repository.find_by_id(resource_id)
            if not resource:
                return None

            resource.is_enabled = False
            resource.updated_at = datetime.now(timezone.utc)

            updated_resource = self._plan_resource_repository.save(resource)

        return self._build_resource_response(updated_resource)

    def duplicate_resource(
        self, resource_id: UUID, target_plan_id: UUID
    ) -> Optional[PlanResourceResponseDTO]:
        """Duplicate a resource to another plan."""
        with self._uow:
            source_resource = self._plan_resource_repository.find_by_id(resource_id)
            if not source_resource:
                return None

            # Validate target plan exists
            target_plan = self._plan_repository.find_by_id(target_plan_id)
            if not target_plan:
                raise ValueError("Target plan not found")

            # Check if resource already exists in target plan
            existing = self._plan_resource_repository.find_by_plan_and_type(
                target_plan_id, source_resource.resource_type
            )
            if existing:
                raise ValueError("Resource already exists in target plan")

            # Create duplicate
            duplicate_resource = PlanResource.create_resource(
                plan_id=target_plan_id,
                resource_type=source_resource.resource_type,
                configuration=source_resource.configuration.copy(),
                is_enabled=source_resource.is_enabled,
            )

            saved_duplicate = self._plan_resource_repository.save(duplicate_resource)

        return self._build_resource_response(saved_duplicate)

    def _generate_configuration_recommendations(
        self,
        resource_type: str,
        configuration: Dict[str, Any],
        test_results: Dict[str, Any],
    ) -> List[str]:
        """Generate configuration recommendations based on test results."""
        recommendations = []

        if resource_type == "chat_whatsapp":
            if not test_results.get("webhook_reachable", True):
                recommendations.append(
                    "Ensure webhook URL is accessible from external networks"
                )
            if test_results.get("response_time_ms", 0) > 2000:
                recommendations.append(
                    "Consider optimizing webhook response time (currently > 2s)"
                )

        elif resource_type == "chat_iframe":
            if not test_results.get("domains_valid", True):
                recommendations.append(
                    "Verify all allowed domains are correctly formatted"
                )
            if test_results.get("load_time_ms", 0) > 3000:
                recommendations.append("Consider optimizing iframe content load time")

        # General recommendations
        if not test_results.get("success", False):
            recommendations.append(
                "Review configuration parameters and ensure all required fields are provided"
            )

        return recommendations

    def _build_resource_response(
        self, resource: PlanResource
    ) -> PlanResourceResponseDTO:
        """Build plan resource response DTO."""
        # Get plan name
        plan = self.plan_repository.find_by_id(resource.plan_id)
        plan_name = plan.name if plan else "Unknown Plan"

        # Get usage count
        usage_count = self.plan_resource_repository.get_usage_count(resource.id)

        return PlanResourceResponseDTO(
            id=resource.id,
            plan_id=resource.plan_id,
            plan_name=plan_name,
            resource_type=resource.resource_type,
            configuration=resource.configuration,
            is_enabled=resource.is_enabled,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
            usage_count=usage_count,
        )
