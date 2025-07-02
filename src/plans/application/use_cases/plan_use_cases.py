from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.entities.plan import Plan
from ...domain.repositories.plan_repository import PlanRepository
from ...domain.services.plan_authorization_service import PlanAuthorizationService
from ..dtos.plan_dto import (
    PlanCreateDTO,
    PlanUpdateDTO,
    PlanResponseDTO,
    PlanListResponseDTO,
    PlanValidationRequestDTO,
    PlanValidationResponseDTO,
)


class PlanUseCase:
    """Use case for plan management operations."""

    def __init__(self, uow: UnitOfWork):
        self._plan_repository: PlanRepository = uow.get_repository("plan")
        self._plan_authorization_service = PlanAuthorizationService(uow)
        self._uow = uow

    def create_plan(self, dto: PlanCreateDTO) -> PlanResponseDTO:
        """Create a new plan."""
        with self._uow:
            # Create plan entity
            plan = Plan(
                name=dto.name,
                description=dto.description,
                plan_type=dto.plan_type,
                resources=dto.resources,
                price_monthly=dto.price_monthly,
                price_yearly=dto.price_yearly,
                created_at=datetime.now(timezone.utc),
            )

            # Save plan
            saved_plan = self._plan_repository.save(plan)

        return self._build_plan_response(saved_plan)

    def get_plan_by_id(self, plan_id: UUID) -> Optional[PlanResponseDTO]:
        """Get plan by ID."""
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            return None

        return self._build_plan_response(plan)

    def update_plan(
        self, plan_id: UUID, dto: PlanUpdateDTO
    ) -> Optional[PlanResponseDTO]:
        """Update an existing plan."""
        with self._uow:
            plan = self._plan_repository.find_by_id(plan_id)
            if not plan:
                return None

            # Update fields
            if dto.description is not None:
                plan.description = dto.description
            if dto.resources is not None:
                plan.resources = dto.resources
            if dto.price_monthly is not None:
                plan.price_monthly = dto.price_monthly
            if dto.price_yearly is not None:
                plan.price_yearly = dto.price_yearly

            plan.updated_at = datetime.now(timezone.utc)

            # Save plan
            updated_plan = self._plan_repository.save(plan)

        return self._build_plan_response(updated_plan)

    def delete_plan(self, plan_id: UUID) -> bool:
        """Delete a plan (soft delete)."""
        with self._uow:
            plan = self._plan_repository.find_by_id(plan_id)
            if not plan:
                return False

            # Check if plan has active subscriptions
            subscription_count = self._plan_repository.get_active_subscription_count(
                plan_id
            )
            if subscription_count > 0:
                raise ValueError("Cannot delete plan with active subscriptions")

            plan.is_active = False
            plan.updated_at = datetime.now(timezone.utc)
            self._plan_repository.save(plan)

        return True

    def list_plans(
        self,
        plan_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PlanListResponseDTO:
        """List plans with pagination and filters."""
        offset = (page - 1) * page_size

        plans, total = self._plan_repository.find_paginated(
            plan_type=plan_type, is_active=is_active, offset=offset, limit=page_size
        )

        plan_responses = []
        for plan in plans:
            plan_responses.append(self._build_plan_response(plan))

        total_pages = (total + page_size - 1) // page_size

        return PlanListResponseDTO(
            plans=plan_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_active_plans(self) -> List[PlanResponseDTO]:
        """Get all active plans."""
        plans = self._plan_repository.find_active_plans()

        plan_responses = []
        for plan in plans:
            plan_responses.append(self._build_plan_response(plan))

        return plan_responses

    def get_plans_by_type(self, plan_type: str) -> List[PlanResponseDTO]:
        """Get plans by type."""
        plans = self._plan_repository.find_by_type(plan_type)

        plan_responses = []
        for plan in plans:
            plan_responses.append(self._build_plan_response(plan))

        return plan_responses

    def validate_plan_access(
        self, request_dto: PlanValidationRequestDTO
    ) -> PlanValidationResponseDTO:
        """Validate if an organization can access a plan resource."""
        plan = self._plan_repository.find_by_id(request_dto.plan_id)
        if not plan:
            return PlanValidationResponseDTO(
                is_allowed=False,
                plan_name="Unknown",
                resource_type=request_dto.resource_type,
                action=request_dto.action,
                reason="Plan not found",
            )

        # Use authorization service to check access
        is_allowed, reason, usage_info = (
            self._plan_authorization_service.can_access_resource(
                organization_id=request_dto.organization_id,
                plan_id=request_dto.plan_id,
                resource_type=request_dto.resource_type,
                action=request_dto.action,
                context=request_dto.context,
            )
        )

        suggestions = []
        if not is_allowed:
            if "limit" in reason.lower():
                suggestions.append("Consider upgrading your plan for higher limits")
            if "not enabled" in reason.lower():
                suggestions.append("This feature is not included in your current plan")

        return PlanValidationResponseDTO(
            is_allowed=is_allowed,
            plan_name=plan.name,
            resource_type=request_dto.resource_type,
            action=request_dto.action,
            reason=reason,
            current_usage=usage_info.get("current_usage") if usage_info else None,
            limits=usage_info.get("limits") if usage_info else None,
            suggestions=suggestions,
        )

    def get_plan_features(self, plan_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed plan features and capabilities."""
        plan = self._plan_repository.find_by_id(plan_id)
        if not plan:
            return None

        # Build comprehensive feature list
        features = {
            "plan_info": {
                "id": str(plan.id),
                "name": plan.name,
                "type": plan.plan_type,
                "description": plan.description,
            },
            "resources": plan.resources,
            "pricing": {"monthly": plan.price_monthly, "yearly": plan.price_yearly},
            "capabilities": [],
        }

        # Add resource capabilities
        for resource_type, config in plan.resources.items():
            if isinstance(config, dict) and config.get("enabled", False):
                features["capabilities"].append(
                    {
                        "type": resource_type,
                        "enabled": True,
                        "limits": config.get("limits", {}),
                        "features": config.get("features", []),
                    }
                )

        return features

    def compare_plans(self, plan_ids: List[UUID]) -> Dict[str, Any]:
        """Compare multiple plans side by side."""
        plans = []
        for plan_id in plan_ids:
            plan = self._plan_repository.find_by_id(plan_id)
            if plan:
                plans.append(plan)

        if not plans:
            return {"error": "No valid plans found"}

        comparison = {"plans": [], "feature_matrix": {}, "pricing_comparison": {}}

        # Build plan summaries
        for plan in plans:
            comparison["plans"].append(
                {
                    "id": str(plan.id),
                    "name": plan.name,
                    "type": plan.plan_type,
                    "monthly_price": plan.price_monthly,
                    "yearly_price": plan.price_yearly,
                }
            )

        # Build feature matrix
        all_features = set()
        for plan in plans:
            all_features.update(plan.resources.keys())

        for feature in all_features:
            comparison["feature_matrix"][feature] = []
            for plan in plans:
                resource_config = plan.resources.get(feature, {})
                comparison["feature_matrix"][feature].append(
                    {
                        "plan_id": str(plan.id),
                        "enabled": resource_config.get("enabled", False),
                        "limits": resource_config.get("limits", {}),
                    }
                )

        # Pricing comparison
        comparison["pricing_comparison"] = {
            "monthly": [p.price_monthly for p in plans],
            "yearly": [p.price_yearly for p in plans],
            "best_value_monthly": min(
                (p for p in plans if p.price_monthly),
                key=lambda x: x.price_monthly or float("inf"),
                default=None,
            ),
            "best_value_yearly": min(
                (p for p in plans if p.price_yearly),
                key=lambda x: x.price_yearly or float("inf"),
                default=None,
            ),
        }

        return comparison

    def _build_plan_response(self, plan: Plan) -> PlanResponseDTO:
        """Build plan response DTO."""
        subscription_count = self._plan_repository.get_active_subscription_count(
            plan.id
        )

        return PlanResponseDTO(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            plan_type=plan.plan_type,
            resources=plan.resources,
            price_monthly=plan.price_monthly,
            price_yearly=plan.price_yearly,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            is_active=plan.is_active,
            subscription_count=subscription_count,
        )
