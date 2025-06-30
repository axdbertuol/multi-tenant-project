import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@localhost:5432/ddd_app"
)

SCHEMA_NAME = "contas"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base with schema support
Base = declarative_base(metadata=MetaData(schema=SCHEMA_NAME))


def get_db():
    """Legacy dependency - use get_unit_of_work instead for new code."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
