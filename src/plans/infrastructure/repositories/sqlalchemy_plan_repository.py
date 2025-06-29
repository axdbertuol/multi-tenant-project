from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, text
from sqlalchemy.exc import IntegrityError

from ...domain.entities.plan import Plan
from ...domain.repositories.plan_repository import PlanRepository
from ...domain.value_objects.plan_name import PlanName
from ...infrastructure.database.models import PlanModel, PlanTypeEnum


class SqlAlchemyPlanRepository(PlanRepository):
    """SQLAlchemy implementation of PlanRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, plan: Plan) -> Plan:
        """Save a plan entity."""
        try:
            # Check if plan exists
            existing = self.session.get(PlanModel, plan.id)

            if existing:
                # Update existing plan
                existing.name = plan.name.value
                existing.description = plan.description
                existing.plan_type = PlanTypeEnum(plan.plan_type)
                existing.resources = plan.resources
                existing.price_monthly = plan.price_monthly
                existing.price_yearly = plan.price_yearly
                existing.is_active = plan.is_active
                existing.features = plan.features if hasattr(plan, "features") else []
                existing.limits = plan.limits if hasattr(plan, "limits") else {}
                existing.updated_at = datetime.now(timezone.utc)

                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                # Create new plan
                plan_model = PlanModel(
                    id=plan.id,
                    name=plan.name.value,
                    description=plan.description,
                    plan_type=PlanTypeEnum(plan.plan_type),
                    resources=plan.resources,
                    price_monthly=plan.price_monthly,
                    price_yearly=plan.price_yearly,
                    is_active=plan.is_active,
                    features=plan.features if hasattr(plan, "features") else [],
                    limits=plan.limits if hasattr(plan, "limits") else {},
                    created_at=plan.created_at,
                    updated_at=plan.updated_at,
                )

                self.session.add(plan_model)
                self.session.flush()
                return self._to_domain_entity(plan_model)

        except IntegrityError as e:
            if "name" in str(e):
                raise ValueError(f"Plan with name '{plan.name.value}' already exists")
            raise e

    def find_by_id(self, plan_id: UUID) -> Optional[Plan]:
        """Find a plan by ID."""
        result = self.session.execute(select(PlanModel).where(PlanModel.id == plan_id))
        plan_model = result.scalar_one_or_none()

        if plan_model:
            return self._to_domain_entity(plan_model)
        return None

    def find_by_name(self, name: PlanName) -> Optional[Plan]:
        """Find a plan by name."""
        result = self.session.execute(
            select(PlanModel).where(PlanModel.name == name.value)
        )
        plan_model = result.scalar_one_or_none()

        if plan_model:
            return self._to_domain_entity(plan_model)
        return None

    def find_by_type(self, plan_type: str) -> List[Plan]:
        """Find plans by type."""
        result = self.session.execute(
            select(PlanModel).where(
                and_(
                    PlanModel.plan_type == PlanTypeEnum(plan_type),
                    PlanModel.is_active,
                )
            )
        )
        plan_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in plan_models]

    def find_active_plans(self) -> List[Plan]:
        """Find all active plans."""
        result = self.session.execute(select(PlanModel).where(PlanModel.is_active))
        plan_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in plan_models]

    def find_paginated(
        self,
        plan_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Plan], int]:
        """Find plans with pagination and filters."""
        query = select(PlanModel)
        count_query = select(PlanModel)

        # Apply filters
        if plan_type:
            query = query.where(PlanModel.plan_type == PlanTypeEnum(plan_type))
            count_query = count_query.where(
                PlanModel.plan_type == PlanTypeEnum(plan_type)
            )

        if is_active is not None:
            query = query.where(PlanModel.is_active == is_active)
            count_query = count_query.where(PlanModel.is_active == is_active)

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = query.offset(offset).limit(limit).order_by(PlanModel.created_at.desc())
        result = self.session.execute(query)
        plan_models = result.scalars().all()

        plans = [self._to_domain_entity(model) for model in plan_models]
        return plans, total

    def delete(self, plan_id: UUID) -> bool:
        """Delete a plan (hard delete)."""
        result = self.session.execute(delete(PlanModel).where(PlanModel.id == plan_id))
        return result.rowcount > 0

    def get_active_subscription_count(self, plan_id: UUID) -> int:
        """Get the number of active subscriptions for a plan."""
        result = self.session.execute(
            text(
                "SELECT COUNT(*) FROM subscriptions WHERE plan_id = :plan_id AND status = 'active'"
            ).bindparam(plan_id=plan_id)
        )
        return result.scalar() or 0

    def get_plan_pricing(
        self, plan_id: UUID
    ) -> tuple[Optional[float], Optional[float]]:
        """Get plan pricing (monthly, yearly)."""
        result = self.session.execute(
            select(PlanModel.price_monthly, PlanModel.price_yearly).where(
                PlanModel.id == plan_id
            )
        )
        pricing = result.first()

        if pricing:
            return pricing[0], pricing[1]
        return None, None

    def update_pricing(
        self,
        plan_id: UUID,
        price_monthly: Optional[float] = None,
        price_yearly: Optional[float] = None,
    ) -> bool:
        """Update plan pricing."""
        update_values = {"updated_at": datetime.now(timezone.utc)}

        if price_monthly is not None:
            update_values["price_monthly"] = price_monthly

        if price_yearly is not None:
            update_values["price_yearly"] = price_yearly

        result = self.session.execute(
            update(PlanModel).where(PlanModel.id == plan_id).values(**update_values)
        )
        return result.rowcount > 0

    def search_plans(
        self,
        query: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Plan], int]:
        """Search plans with filters."""
        db_query = select(PlanModel)
        count_query = select(PlanModel)

        # Apply text search
        if query:
            search_filter = PlanModel.name.ilike(
                f"%{query}%"
            ) | PlanModel.description.ilike(f"%{query}%")
            db_query = db_query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Apply price filters
        if min_price is not None:
            price_filter = (PlanModel.price_monthly >= min_price) | (
                PlanModel.price_yearly >= min_price * 10
            )
            db_query = db_query.where(price_filter)
            count_query = count_query.where(price_filter)

        if max_price is not None:
            price_filter = (PlanModel.price_monthly <= max_price) | (
                PlanModel.price_yearly <= max_price * 10
            )
            db_query = db_query.where(price_filter)
            count_query = count_query.where(price_filter)

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        db_query = (
            db_query.offset(offset).limit(limit).order_by(PlanModel.created_at.desc())
        )
        result = self.session.execute(db_query)
        plan_models = result.scalars().all()

        plans = [self._to_domain_entity(model) for model in plan_models]
        return plans, total

    def _to_domain_entity(self, plan_model: PlanModel) -> Plan:
        """Convert SQLAlchemy model to domain entity."""
        return Plan(
            id=plan_model.id,
            name=PlanName(plan_model.name),
            description=plan_model.description,
            plan_type=plan_model.plan_type.value,
            resources=plan_model.resources,
            price_monthly=plan_model.price_monthly,
            price_yearly=plan_model.price_yearly,
            is_active=plan_model.is_active,
            features=plan_model.features,
            limits=plan_model.limits,
            created_at=plan_model.created_at,
            updated_at=plan_model.updated_at,
        )
