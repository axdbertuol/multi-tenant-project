"""Documents presentation layer module."""

from .routers import documents_router
from .dependencies import (
    get_documents_uow,
    get_document_area_use_case,
    get_document_folder_use_case,
    get_user_document_access_use_case,
)

__all__ = [
    "documents_router",
    "get_documents_uow",
    "get_document_area_use_case",
    "get_document_folder_use_case",
    "get_user_document_access_use_case",
]