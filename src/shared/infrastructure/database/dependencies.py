from sqlalchemy.orm import Session
from fastapi import Depends

from infrastructure.database.connection import SessionLocal
from infrastructure.repositories.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork


def get_db_session() -> Session:
    """Get a new database session."""
    db = SessionLocal()
    return db


def get_unit_of_work(db: Session = Depends(get_db_session)) -> SQLAlchemyUnitOfWork:
    """Get a UnitOfWork instance with the current database session."""
    return SQLAlchemyUnitOfWork(db)