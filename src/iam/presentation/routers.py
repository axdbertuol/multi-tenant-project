from fastapi import APIRouter

from .routes import auth_router, user_router, session_router, role_router, onboarding_router, organization_router

router = APIRouter(prefix="/api/v1/iam", tags=["IAM"])

# Include all IAM-related routes
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(organization_router, prefix="/organizations", tags=["Organizations"])
router.include_router(user_router, prefix="/users", tags=["Users"])
router.include_router(session_router, prefix="/sessions", tags=["Sessions"])
router.include_router(role_router, prefix="/roles", tags=["Roles"])
router.include_router(onboarding_router, prefix="/onboarding", tags=["Onboarding"])
