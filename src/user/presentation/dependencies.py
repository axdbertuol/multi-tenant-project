from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.dependencies import get_db_session
from user.application.use_cases.auth_use_cases import AuthUseCase
from user.application.use_cases.user_use_cases import UserUseCase
from user.application.use_cases.session_use_cases import SessionUseCase
from user.infrastructure.user_unit_of_work import UserUnitOfWork


def get_user_uow(db: Session = Depends(get_db_session)) -> UserUnitOfWork:
    """Get a UserUnitOfWork instance with user and user_session repositories."""
    return UserUnitOfWork(db, ["user", "user_session"])


def get_auth_use_case(uow: UserUnitOfWork = Depends(get_user_uow)) -> AuthUseCase:
    """Get AuthUseCase with proper UnitOfWork dependency."""
    return AuthUseCase(uow)


def get_user_use_case(uow: UserUnitOfWork = Depends(get_user_uow)) -> UserUseCase:
    """Get UserUseCase with proper UnitOfWork dependency."""
    return UserUseCase(uow)


def get_session_use_case(uow: UserUnitOfWork = Depends(get_user_uow)) -> SessionUseCase:
    """Get SessionUseCase with proper UnitOfWork dependency."""
    return SessionUseCase(uow)
