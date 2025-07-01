from fastapi import APIRouter

from .routes.role_routes import router as role_router

# Create main authorization router
authorization_api_router = APIRouter(prefix="/api/v1/authorization", tags=["Authorization Context"])

# Include all sub-routers
authorization_api_router.include_router(role_router)

__all__ = ["authorization_api_router"]