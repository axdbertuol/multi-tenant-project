from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.dependencies import get_db_session
from plans.application.use_cases.plan_use_cases import PlanUseCase
from plans.application.use_cases.subscription_use_cases import SubscriptionUseCase
from plans.application.use_cases.plan_resource_use_cases import PlanResourceUseCase
from plans.application.use_cases.feature_usage_use_cases import FeatureUsageUseCase
from plans.application.use_cases.application_instance_use_cases import ApplicationInstanceUseCase
from plans.application.use_cases.usage_tracking_use_cases import UsageTrackingUseCase
from plans.application.use_cases.plan_resource_feature_use_cases import PlanResourceFeatureUseCase
from plans.application.use_cases.plan_resource_limit_use_cases import PlanResourceLimitUseCase
from plans.infrastructure.plans_unit_of_work import PlansUnitOfWork


def get_plans_uow(db: Session = Depends(get_db_session)) -> PlansUnitOfWork:
    """Get a PlansUnitOfWork instance with all plan repositories."""
    return PlansUnitOfWork(db, [
        "plan", 
        "subscription", 
        "plan_resource",
        "feature_usage",
        "organization_plan",
        "application_instance",
        "plan_resource_feature",
        "plan_resource_limit"
    ])


def get_plan_use_case(uow: PlansUnitOfWork = Depends(get_plans_uow)) -> PlanUseCase:
    """Get PlanUseCase with proper UnitOfWork dependency."""
    return PlanUseCase(uow)


def get_subscription_use_case(
    uow: PlansUnitOfWork = Depends(get_plans_uow),
) -> SubscriptionUseCase:
    """Get SubscriptionUseCase with proper UnitOfWork dependency."""
    return SubscriptionUseCase(uow)


def get_plan_resource_use_case(
    uow: PlansUnitOfWork = Depends(get_plans_uow),
) -> PlanResourceUseCase:
    """Get PlanResourceUseCase with proper UnitOfWork dependency."""
    return PlanResourceUseCase(uow)


def get_feature_usage_use_case(
    uow: PlansUnitOfWork = Depends(get_plans_uow),
) -> FeatureUsageUseCase:
    """Get FeatureUsageUseCase with proper UnitOfWork dependency."""
    return FeatureUsageUseCase(uow)


def get_application_instance_use_case(
    uow: PlansUnitOfWork = Depends(get_plans_uow),
) -> ApplicationInstanceUseCase:
    """Get ApplicationInstanceUseCase with proper UnitOfWork dependency."""
    return ApplicationInstanceUseCase(uow)


def get_usage_tracking_use_case(
    uow: PlansUnitOfWork = Depends(get_plans_uow),
) -> UsageTrackingUseCase:
    """Get UsageTrackingUseCase with proper UnitOfWork dependency."""
    return UsageTrackingUseCase(uow)


def get_plan_resource_feature_use_case(
    uow: PlansUnitOfWork = Depends(get_plans_uow),
) -> PlanResourceFeatureUseCase:
    """Get PlanResourceFeatureUseCase with proper UnitOfWork dependency."""
    return PlanResourceFeatureUseCase(uow)


def get_plan_resource_limit_use_case(
    uow: PlansUnitOfWork = Depends(get_plans_uow),
) -> PlanResourceLimitUseCase:
    """Get PlanResourceLimitUseCase with proper UnitOfWork dependency."""
    return PlanResourceLimitUseCase(uow)
