import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

# Make app importable
sys.path.append(os.path.abspath("."))

# Load DB + Base
from app.core.db.session import Base, DATABASE_URL

# Import your models so Alembic can detect them
from app.user.models import User  # <-- add more models here


config = context.config

# Load .env variables in alembic.ini
section = config.config_ini_section
if config.get_main_option("env_file"):
    from dotenv import load_dotenv
    load_dotenv(config.get_main_option("env_file"))

fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
