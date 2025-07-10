"""Documents presentation routes module."""

from .document_area_routes import router as document_area_router
from .document_folder_routes import router as document_folder_router
from .user_document_access_routes import router as user_document_access_router

__all__ = [
    "document_area_router",
    "document_folder_router", 
    "user_document_access_router",
]