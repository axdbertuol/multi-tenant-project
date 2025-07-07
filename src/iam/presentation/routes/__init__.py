from .role_routes import router as role_router
from .auth_routes import router as auth_router
from .session_routes import router as session_router
from .user_routes import router as user_router
from .onboarding_routes import router as onboarding_router
from .organization_routes import router as organization_router
from .authorization_subject_routes import router as authorization_subject_router

__all__ = [
    "role_router", 
    "auth_router", 
    "session_router", 
    "user_router", 
    "onboarding_router", 
    "organization_router",
    "authorization_subject_router"
]
