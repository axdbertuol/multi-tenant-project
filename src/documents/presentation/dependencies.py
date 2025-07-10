from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.connection import get_db
from ..application.use_cases.document_area_use_cases import DocumentAreaUseCase
from ..application.use_cases.document_folder_use_cases import DocumentFolderUseCase
from ..application.use_cases.user_document_access_use_cases import UserDocumentAccessUseCase
from ..infrastructure.documents_unit_of_work import DocumentsUnitOfWork
from ..domain.services.document_area_service import DocumentAreaService
from ..domain.services.document_access_service import DocumentAccessService
from ..application.contracts.iam_contract import IAMContract
from ..infrastructure.contracts.iam_contract_impl import IAMContractImpl
from src.iam.infrastructure.iam_unit_of_work import IAMUnitOfWork


def get_documents_uow(db: Session = Depends(get_db)) -> DocumentsUnitOfWork:
    """Obtém uma instância de DocumentsUnitOfWork com todos os repositórios do contexto Documents."""
    return DocumentsUnitOfWork(db)


def get_iam_uow(db: Session = Depends(get_db)) -> IAMUnitOfWork:
    """Obtém uma instância de IAMUnitOfWork para integração com IAM."""
    return IAMUnitOfWork(
        db,
        [
            "user",
            "user_organization_role", 
            "organization",
            "role",
        ],
    )


def get_iam_contract(iam_uow: IAMUnitOfWork = Depends(get_iam_uow)) -> IAMContract:
    """Obtém uma instância de IAMContract para integração com IAM."""
    return IAMContractImpl(iam_uow)


def get_document_area_service(
    uow: DocumentsUnitOfWork = Depends(get_documents_uow),
    iam_contract: IAMContract = Depends(get_iam_contract),
) -> DocumentAreaService:
    """Obtém DocumentAreaService com as dependências apropriadas."""
    return DocumentAreaService(
        document_area_repository=uow.document_areas,
        document_folder_repository=uow.document_folders,
        user_document_access_repository=uow.user_document_access,
        iam_contract=iam_contract,
    )


def get_document_access_service(
    uow: DocumentsUnitOfWork = Depends(get_documents_uow),
    iam_contract: IAMContract = Depends(get_iam_contract),
) -> DocumentAccessService:
    """Obtém DocumentAccessService com as dependências apropriadas."""
    return DocumentAccessService(
        document_area_repository=uow.document_areas,
        document_folder_repository=uow.document_folders,
        user_document_access_repository=uow.user_document_access,
        iam_contract=iam_contract,
    )


def get_document_area_use_case(
    uow: DocumentsUnitOfWork = Depends(get_documents_uow),
    document_area_service: DocumentAreaService = Depends(get_document_area_service),
    iam_contract: IAMContract = Depends(get_iam_contract),
) -> DocumentAreaUseCase:
    """Obtém DocumentAreaUseCase com as dependências apropriadas."""
    return DocumentAreaUseCase(
        document_area_repository=uow.document_areas,
        document_folder_repository=uow.document_folders,
        user_document_access_repository=uow.user_document_access,
        document_area_service=document_area_service,
        iam_contract=iam_contract,
    )


def get_document_folder_use_case(
    uow: DocumentsUnitOfWork = Depends(get_documents_uow),
    document_access_service: DocumentAccessService = Depends(get_document_access_service),
    iam_contract: IAMContract = Depends(get_iam_contract),
) -> DocumentFolderUseCase:
    """Obtém DocumentFolderUseCase com as dependências apropriadas."""
    return DocumentFolderUseCase(
        document_folder_repository=uow.document_folders,
        document_area_repository=uow.document_areas,
        user_document_access_repository=uow.user_document_access,
        document_access_service=document_access_service,
        iam_contract=iam_contract,
    )


def get_user_document_access_use_case(
    uow: DocumentsUnitOfWork = Depends(get_documents_uow),
    document_area_service: DocumentAreaService = Depends(get_document_area_service),
    iam_contract: IAMContract = Depends(get_iam_contract),
) -> UserDocumentAccessUseCase:
    """Obtém UserDocumentAccessUseCase com as dependências apropriadas."""
    return UserDocumentAccessUseCase(
        user_document_access_repository=uow.user_document_access,
        document_area_repository=uow.document_areas,
        document_area_service=document_area_service,
        iam_contract=iam_contract,
    )