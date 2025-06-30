from fastapi import APIRouter

from .routes.auth_routes import router as auth_router
from .routes.user_routes import router as user_router
from .routes.session_routes import router as session_router

# Cria o roteador principal do usuário
user_api_router = APIRouter(prefix="/api/v1/user", tags=["Contexto do Usuário"])

# Inclui todos os sub-roteadores
user_api_router.include_router(auth_router)
user_api_router.include_router(user_router)
user_api_router.include_router(session_router)

__all__ = ["user_api_router"]
