"""Alembic environment: the ERP passes its open connection (database.upgrade); the alembic CLI uses DATABASE_URL."""
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from powererp import config as erp_config  # noqa: E402
from powererp import models  # noqa: E402,F401  (registers every table)
from powererp.database import Base  # noqa: E402

cfg = context.config
if cfg.config_file_name and "connection" not in cfg.attributes:
    fileConfig(cfg.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=erp_config.database_url(), target_metadata=target_metadata,
                      literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def _run(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connection = cfg.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return
    engine = create_engine(erp_config.database_url())
    with engine.begin() as con:
        _run(con)
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
