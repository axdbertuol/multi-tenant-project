from shared.domain.repositories.unit_of_work import UnitOfWork
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: Session):
        self.session = session
        self._committed = False

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.session.close()

    def commit(self) -> None:
        if not self._committed:
            try:
                self.session.commit()
                self._committed = True
            except SQLAlchemyError:
                self.rollback()
                raise

    def rollback(self) -> None:
        self.session.rollback()
        self._committed = False
