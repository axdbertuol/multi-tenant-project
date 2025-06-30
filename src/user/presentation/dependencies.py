from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.connection import get_db
from user.application.use_cases.auth_use_cases import AuthUseCase
from user.application.use_cases.user_use_cases import UserUseCase
from user.application.use_cases.session_use_cases import SessionUseCase
from user.infrastructure.user_unit_of_work import UserUnitOfWork


def get_user_uow(db: Session = Depends(get_db)) -> UserUnitOfWork:
    """Obtém uma instância de UserUnitOfWork com repositórios de usuário e sessão de usuário."""
    return UserUnitOfWork(db, ["user", "user_session"])


def get_auth_use_case(uow: UserUnitOfWork = Depends(get_user_uow)) -> AuthUseCase:
    """Obtém AuthUseCase com a dependência UnitOfWork apropriada."""
    return AuthUseCase(uow)


def get_user_use_case(uow: UserUnitOfWork = Depends(get_user_uow)) -> UserUseCase:
    """Obtém UserUseCase com a dependência UnitOfWork apropriada."""
    return UserUseCase(uow)


def get_session_use_case(uow: UserUnitOfWork = Depends(get_user_uow)) -> SessionUseCase:
    """Obtém SessionUseCase com a dependência UnitOfWork apropriada."""
    return SessionUseCase(uow)
