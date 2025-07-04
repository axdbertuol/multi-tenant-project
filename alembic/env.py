import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

load_dotenv()

from shared.infrastructure.database.base import Base

# Import only the model files directly to avoid circular imports
import sys
import importlib.util

# Import IAM models (combines user and authorization models)
iam_spec = importlib.util.spec_from_file_location(
    "iam_models",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src",
        "iam",
        "infrastructure",
        "database",
        "models.py",
    ),
)
iam_models = importlib.util.module_from_spec(iam_spec)
iam_spec.loader.exec_module(iam_models)

# Organization models are now included in IAM models
# No separate organization models file needed

# Import plans models
plans_spec = importlib.util.spec_from_file_location(
    "plans_models",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "plans", "infrastructure", "database", "models.py")
)
plans_models = importlib.util.module_from_spec(plans_spec)
plans_spec.loader.exec_module(plans_models)


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    return os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/ddd_app"
    )


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=target_metadata.schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        # Create schema if it doesn't exist
        if target_metadata.schema:
            connection.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {target_metadata.schema}")
            )
            connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=target_metadata.schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
