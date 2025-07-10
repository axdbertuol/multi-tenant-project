from typing import Optional
from sqlalchemy.orm import Session
from src.shared.domain.repositories.unit_of_work import UnitOfWork

from ..domain.repositories.document_area_repository import DocumentAreaRepository
from ..domain.repositories.document_folder_repository import DocumentFolderRepository
from ..domain.repositories.user_document_access_repository import UserDocumentAccessRepository

from .repositories.sqlalchemy_document_area_repository import SqlAlchemyDocumentAreaRepository
from .repositories.sqlalchemy_document_folder_repository import SqlAlchemyDocumentFolderRepository
from .repositories.sqlalchemy_user_document_access_repository import SqlAlchemyUserDocumentAccessRepository


class DocumentsUnitOfWork(UnitOfWork):
    """
    Unit of Work for Documents bounded context.
    
    Coordena operações transacionais entre os repositórios do contexto de documentos,
    garantindo consistência e atomicidade das operações.
    """

    def __init__(self, session: Session):
        self._session = session
        self._document_area_repository: Optional[DocumentAreaRepository] = None
        self._document_folder_repository: Optional[DocumentFolderRepository] = None
        self._user_document_access_repository: Optional[UserDocumentAccessRepository] = None

    @property
    def document_areas(self) -> DocumentAreaRepository:
        """Get the document area repository."""
        if self._document_area_repository is None:
            self._document_area_repository = SqlAlchemyDocumentAreaRepository(self._session)
        return self._document_area_repository

    @property
    def document_folders(self) -> DocumentFolderRepository:
        """Get the document folder repository."""
        if self._document_folder_repository is None:
            self._document_folder_repository = SqlAlchemyDocumentFolderRepository(self._session)
        return self._document_folder_repository

    @property
    def user_document_access(self) -> UserDocumentAccessRepository:
        """Get the user document access repository."""
        if self._user_document_access_repository is None:
            self._user_document_access_repository = SqlAlchemyUserDocumentAccessRepository(self._session)
        return self._user_document_access_repository

    def commit(self) -> None:
        """Commit the transaction."""
        self._session.commit()

    def rollback(self) -> None:
        """Rollback the transaction."""
        self._session.rollback()

    def flush(self) -> None:
        """Flush the session."""
        self._session.flush()

    def __enter__(self):
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self._session.close()

    def close(self) -> None:
        """Close the session."""
        self._session.close()

    def begin(self) -> None:
        """Begin a new transaction."""
        # SQLAlchemy sessions auto-begin, so this is mostly for interface compliance
        pass

    def is_active(self) -> bool:
        """Check if the unit of work is active."""
        return self._session.is_active