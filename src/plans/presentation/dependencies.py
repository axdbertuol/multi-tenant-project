from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.dependencies import get_db_session
from plans.application.use_cases.plan_use_cases import PlanUseCase
from plans.application.use_cases.subscription_use_cases import SubscriptionUseCase
from plans.application.use_cases.plan_resource_use_cases import PlanResourceUseCase
from plans.infrastructure.plans_unit_of_work import PlansUnitOfWork


def get_plans_uow(db: Session = Depends(get_db_session)) -> PlansUnitOfWork:
    """Get a PlansUnitOfWork instance with plan, subscription, and plan_resource repositories."""
    return PlansUnitOfWork(db, ["plan", "subscription", "plan_resource"])


def get_plan_use_case(uow: PlansUnitOfWork = Depends(get_plans_uow)) -> PlanUseCase:
    """Get PlanUseCase with proper UnitOfWork dependency."""
    return PlanUseCase(uow)


def get_subscription_use_case(uow: PlansUnitOfWork = Depends(get_plans_uow)) -> SubscriptionUseCase:
    """Get SubscriptionUseCase with proper UnitOfWork dependency."""
    return SubscriptionUseCase(uow)


def get_plan_resource_use_case(uow: PlansUnitOfWork = Depends(get_plans_uow)) -> PlanResourceUseCase:
    """Get PlanResourceUseCase with proper UnitOfWork dependency."""
    return PlanResourceUseCase(uow)