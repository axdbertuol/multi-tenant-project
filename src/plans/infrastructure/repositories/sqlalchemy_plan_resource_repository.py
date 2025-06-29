from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, text
from sqlalchemy.exc import IntegrityError

from ...domain.entities.plan_resource import PlanResource
from ...domain.repositories.plan_resource_repository import PlanResourceRepository
from ...infrastructure.database.models import (
    PlanResourceModel,
    PlanResourceTypeEnum,
    FeatureUsageModel,
)


class SqlAlchemyPlanResourceRepository(PlanResourceRepository):
    """SQLAlchemy implementation of PlanResourceRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, resource: PlanResource) -> PlanResource:
        """Save a plan resource entity."""
        try:
            # Check if resource exists
            existing = self.session.get(PlanResourceModel, resource.id)

            if existing:
                # Update existing resource
                existing.plan_id = resource.plan_id
                existing.resource_type = PlanResourceTypeEnum(resource.resource_type)
                existing.configuration = resource.configuration
                existing.is_enabled = resource.is_enabled
                existing.limits = resource.limits if hasattr(resource, "limits") else {}
                existing.updated_at = datetime.now(timezone.utc)

                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                # Create new resource
                resource_model = PlanResourceModel(
                    id=resource.id,
                    plan_id=resource.plan_id,
                    resource_type=PlanResourceTypeEnum(resource.resource_type),
                    configuration=resource.configuration,
                    is_enabled=resource.is_enabled,
                    limits=resource.limits if hasattr(resource, "limits") else {},
                    created_at=resource.created_at,
                    updated_at=resource.updated_at,
                )

                self.session.add(resource_model)
                self.session.flush()
                return self._to_domain_entity(resource_model)

        except IntegrityError as e:
            if "plan_id" in str(e) and "resource_type" in str(e):
                raise ValueError(
                    f"Resource {resource.resource_type} already exists for this plan"
                )
            raise e

    def find_by_id(self, resource_id: UUID) -> Optional[PlanResource]:
        """Find a plan resource by ID."""
        result = self.session.execute(
            select(PlanResourceModel).where(PlanResourceModel.id == resource_id)
        )
        resource_model = result.scalar_one_or_none()

        if resource_model:
            return self._to_domain_entity(resource_model)
        return None

    def find_by_plan(self, plan_id: UUID) -> List[PlanResource]:
        """Find all resources for a plan."""
        result = self.session.execute(
            select(PlanResourceModel).where(PlanResourceModel.plan_id == plan_id)
        )
        resource_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in resource_models]

    def find_by_plan_and_type(
        self, plan_id: UUID, resource_type: str
    ) -> Optional[PlanResource]:
        """Find a specific resource for a plan."""
        result = self.session.execute(
            select(PlanResourceModel).where(
                and_(
                    PlanResourceModel.plan_id == plan_id,
                    PlanResourceModel.resource_type
                    == PlanResourceTypeEnum(resource_type),
                )
            )
        )
        resource_model = result.scalar_one_or_none()

        if resource_model:
            return self._to_domain_entity(resource_model)
        return None

    def find_by_type(self, resource_type: str) -> List[PlanResource]:
        """Find all resources of a specific type."""
        result = self.session.execute(
            select(PlanResourceModel).where(
                and_(
                    PlanResourceModel.resource_type
                    == PlanResourceTypeEnum(resource_type),
                    PlanResourceModel.is_enabled,
                )
            )
        )
        resource_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in resource_models]

    def find_enabled_resources(self, plan_id: UUID) -> List[PlanResource]:
        """Find enabled resources for a plan."""
        result = self.session.execute(
            select(PlanResourceModel).where(
                and_(
                    PlanResourceModel.plan_id == plan_id,
                    PlanResourceModel.is_enabled,
                )
            )
        )
        resource_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in resource_models]

    def find_paginated(
        self,
        plan_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[PlanResource], int]:
        """Find plan resources with pagination and filters."""
        query = select(PlanResourceModel)
        count_query = select(PlanResourceModel)

        # Apply filters
        if plan_id:
            query = query.where(PlanResourceModel.plan_id == plan_id)
            count_query = count_query.where(PlanResourceModel.plan_id == plan_id)

        if resource_type:
            query = query.where(
                PlanResourceModel.resource_type == PlanResourceTypeEnum(resource_type)
            )
            count_query = count_query.where(
                PlanResourceModel.resource_type == PlanResourceTypeEnum(resource_type)
            )

        if is_enabled is not None:
            query = query.where(PlanResourceModel.is_enabled == is_enabled)
            count_query = count_query.where(PlanResourceModel.is_enabled == is_enabled)

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = (
            query.offset(offset)
            .limit(limit)
            .order_by(PlanResourceModel.created_at.desc())
        )
        result = self.session.execute(query)
        resource_models = result.scalars().all()

        resources = [self._to_domain_entity(model) for model in resource_models]
        return resources, total

    def delete(self, resource_id: UUID) -> bool:
        """Delete a plan resource (hard delete)."""
        result = self.session.execute(
            delete(PlanResourceModel).where(PlanResourceModel.id == resource_id)
        )
        return result.rowcount > 0

    def update_configuration(
        self, resource_id: UUID, configuration: Dict[str, Any]
    ) -> bool:
        """Update resource configuration."""
        result = self.session.execute(
            update(PlanResourceModel)
            .where(PlanResourceModel.id == resource_id)
            .values(configuration=configuration, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def enable_resource(self, resource_id: UUID) -> bool:
        """Enable a plan resource."""
        result = self.session.execute(
            update(PlanResourceModel)
            .where(PlanResourceModel.id == resource_id)
            .values(is_enabled=True, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def disable_resource(self, resource_id: UUID) -> bool:
        """Disable a plan resource."""
        result = self.session.execute(
            update(PlanResourceModel)
            .where(PlanResourceModel.id == resource_id)
            .values(is_enabled=False, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def get_usage_count(self, resource_id: UUID) -> int:
        """Get usage count for a resource."""
        result = self.session.execute(
            text(
                "SELECT COUNT(*) FROM feature_usage WHERE resource_type = (SELECT resource_type FROM plan_resources WHERE id = :resource_id)"
            ).bindparam(resource_id=resource_id)
        )
        return result.scalar() or 0

    def record_usage(
        self,
        resource_id: UUID,
        organization_id: UUID,
        usage_date: datetime,
        usage_count: int = 1,
        usage_details: Optional[Dict[str, Any]] = None,
        cost: Optional[float] = None,
    ) -> bool:
        """Record usage of a plan resource."""
        # Get resource type first
        resource_result = self.session.execute(
            select(PlanResourceModel.resource_type).where(
                PlanResourceModel.id == resource_id
            )
        )
        resource_type_enum = resource_result.scalar_one_or_none()

        if not resource_type_enum:
            return False

        usage_model = FeatureUsageModel(
            organization_id=organization_id,
            resource_type=resource_type_enum.value,
            feature_name="general_usage",
            usage_count=usage_count,
            usage_date=usage_date,
            usage_details=usage_details or {},
            cost=cost,
        )

        self.session.add(usage_model)
        self.session.flush()
        return True

    def get_usage_statistics(
        self, resource_id: UUID, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage statistics for a resource."""
        # Get resource type
        resource_result = self.session.execute(
            select(PlanResourceModel.resource_type).where(
                PlanResourceModel.id == resource_id
            )
        )
        resource_type_enum = resource_result.scalar_one_or_none()

        if not resource_type_enum:
            return {}

        # Get usage data
        usage_result = self.session.execute(
            select(FeatureUsageModel).where(
                and_(
                    FeatureUsageModel.resource_type == resource_type_enum.value,
                    FeatureUsageModel.usage_date >= start_date,
                    FeatureUsageModel.usage_date <= end_date,
                )
            )
        )
        usage_records = usage_result.scalars().all()

        # Calculate statistics
        total_usage = sum(record.usage_count for record in usage_records)
        total_cost = sum(record.cost or 0 for record in usage_records)

        # Group by date for trends
        daily_usage = {}
        for record in usage_records:
            date_key = record.usage_date.date().isoformat()
            if date_key not in daily_usage:
                daily_usage[date_key] = {"usage": 0, "cost": 0}
            daily_usage[date_key]["usage"] += record.usage_count
            daily_usage[date_key]["cost"] += record.cost or 0

        return {
            "total_usage": total_usage,
            "breakdown": {"by_date": daily_usage},
            "costs": {"total": total_cost},
            "trends": [
                {"date": date, "usage": data["usage"], "cost": data["cost"]}
                for date, data in daily_usage.items()
            ],
        }

    def bulk_update_limits(self, resource_updates: Dict[UUID, Dict[str, Any]]) -> int:
        """Update limits for multiple resources."""
        updated_count = 0

        for resource_id, limits in resource_updates.items():
            result = self.session.execute(
                update(PlanResourceModel)
                .where(PlanResourceModel.id == resource_id)
                .values(limits=limits, updated_at=datetime.now(timezone.utc))
            )
            if result.rowcount > 0:
                updated_count += 1

        return updated_count

    def _to_domain_entity(self, resource_model: PlanResourceModel) -> PlanResource:
        """Convert SQLAlchemy model to domain entity."""
        return PlanResource(
            id=resource_model.id,
            plan_id=resource_model.plan_id,
            resource_type=resource_model.resource_type.value,
            configuration=resource_model.configuration,
            is_enabled=resource_model.is_enabled,
            limits=resource_model.limits,
            created_at=resource_model.created_at,
            updated_at=resource_model.updated_at,
        )
