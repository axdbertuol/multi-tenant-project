from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from domain.repositories.unit_of_work import UnitOfWork
from infrastructure.repositories.user_repository_impl import UserRepositoryImpl


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: Session):
        self.session = session
        self.users = UserRepositoryImpl(session)
        self._committed = False

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            try:
                await self.commit()
            except SQLAlchemyError:
                await self.rollback()
                raise
        else:
            await self.rollback()
        self.session.close()

    async def commit(self) -> None:
        if not self._committed:
            try:
                self.session.commit()
                self._committed = True
            except SQLAlchemyError:
                await self.rollback()
                raise

    async def rollback(self) -> None:
        self.session.rollback()
        self._committed = False
