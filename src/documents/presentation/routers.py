"""Documents routers configuration."""

from fastapi import APIRouter

from .routes import (
    document_area_router,
    document_folder_router,
    user_document_access_router,
)

# Create main documents router
documents_router = APIRouter(prefix="/documents", tags=["Documents"])

# Include all document-related routes
documents_router.include_router(
    document_area_router,
    prefix="/areas",
    tags=["Document Areas"]
)

documents_router.include_router(
    document_folder_router,
    prefix="/folders",
    tags=["Document Folders"]
)

documents_router.include_router(
    user_document_access_router,
    prefix="/access",
    tags=["User Document Access"]
)