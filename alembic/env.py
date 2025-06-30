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

# Import authorization models
auth_spec = importlib.util.spec_from_file_location(
    "auth_models", 
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "authorization", "infrastructure", "database", "models.py")
)
auth_models = importlib.util.module_from_spec(auth_spec)
auth_spec.loader.exec_module(auth_models)

# Import user models  
user_spec = importlib.util.spec_from_file_location(
    "user_models",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "user", "infrastructure", "database", "models.py")
)
user_models = importlib.util.module_from_spec(user_spec)
user_spec.loader.exec_module(user_models)

# Import organization models
org_spec = importlib.util.spec_from_file_location(
    "org_models",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "organization", "infrastructure", "database", "models.py")
)
org_models = importlib.util.module_from_spec(org_spec)
org_spec.loader.exec_module(org_models)

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
    current_schema = context.get_x_argument(as_dictionary=True).get("schema")
    with connectable.connect() as connection:
        # Create schema if it doesn't exist
        if target_metadata.schema:
            connection.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {target_metadata.schema}")
            )
            connection.execute(text('set search_path to "%s"' % current_schema))
            connection.commit()
        connection.dialect.default_schema_name = current_schema

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # version_table_schema=target_metadata.schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
