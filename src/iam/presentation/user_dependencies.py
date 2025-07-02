from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.connection import get_db
from ..application.use_cases.authentication_use_cases import AuthenticationUseCase
from ..application.use_cases.user_use_cases import UserUseCase
from ..application.use_cases.session_use_cases import SessionUseCase
from ..infrastructure.iam_unit_of_work import IAMUnitOfWork


def get_iam_uow(db: Session = Depends(get_db)) -> IAMUnitOfWork:
    """Obtém uma instância de IAMUnitOfWork com repositórios IAM."""
    return IAMUnitOfWork(
        db, ["user", "user_session", "role", "permission", "policy", "resource"]
    )


def get_auth_use_case(
    uow: IAMUnitOfWork = Depends(get_iam_uow),
) -> AuthenticationUseCase:
    """Obtém AuthenticationUseCase com a dependência UnitOfWork apropriada."""
    return AuthenticationUseCase(uow)


def get_user_use_case(uow: IAMUnitOfWork = Depends(get_iam_uow)) -> UserUseCase:
    """Obtém UserUseCase com a dependência UnitOfWork apropriada."""
    return UserUseCase(uow)


def get_session_use_case(uow: IAMUnitOfWork = Depends(get_iam_uow)) -> SessionUseCase:
    """Obtém SessionUseCase com a dependência UnitOfWork apropriada."""
    return SessionUseCase(uow)
