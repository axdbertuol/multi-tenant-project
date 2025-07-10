from fastapi import APIRouter

from .routes import (
    auth_router, 
    user_router, 
    session_router, 
    role_router, 
    organization_router,
    profile_router,
    user_profile_router,
    profile_folder_permission_router,
)

router = APIRouter(prefix="/api/v1/iam", tags=["IAM"])

# Include all IAM-related routes
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(organization_router, prefix="/organizations", tags=["Organizations"])
router.include_router(user_router, prefix="/users", tags=["Users"])
router.include_router(session_router, prefix="/sessions", tags=["Sessions"])
router.include_router(role_router, prefix="/roles", tags=["Roles"])
router.include_router(profile_router, prefix="/profiles", tags=["Profiles"])
router.include_router(user_profile_router, prefix="/user-profiles", tags=["User Profiles"])
router.include_router(profile_folder_permission_router, prefix="/profile-folder-permissions", tags=["Profile Folder Permissions"])
