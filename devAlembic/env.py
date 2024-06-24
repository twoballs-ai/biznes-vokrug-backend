from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from madsoft.database import Base

# Set the Alembic Config object
config = context.config

# Load the logging configuration from the .ini file if specified
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set SQLAlchemy URL using environment variable
config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))

# Import your SQLAlchemy models for 'autogenerate' support
from madsoft.models import *  # Adjust this import as per your actual models
target_metadata = [Base.metadata]

# Define function to run migrations in offline mode
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

# Define function to run migrations in online mode
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

# Determine if offline or online mode and execute accordingly
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
