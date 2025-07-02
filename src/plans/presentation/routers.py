from fastapi import APIRouter

from .routes.plan_routes import router as plan_router
from .routes.subscription_routes import router as subscription_router
from .routes.plan_resource_routes import router as plan_resource_router

# Create main plans router
plans_api_router = APIRouter(prefix="/api/v1/plans", tags=["Plans Context"])

# Include all sub-routers
plans_api_router.include_router(plan_router)
plans_api_router.include_router(subscription_router)
plans_api_router.include_router(plan_resource_router)

__all__ = ["plans_api_router"]
