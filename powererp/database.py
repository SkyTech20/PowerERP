"""PostgreSQL connection (SQLAlchemy 2.0) and schema migrations (Alembic).

init() opens the engine and brings the schema up to date (alembic upgrade head), so a new
database needs nothing else. session_scope() is one transaction: committed at the end of the
block, rolled back on error.
"""
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from . import config

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "migrations"


class Base(DeclarativeBase):
    pass


engine = None
SessionLocal = sessionmaker(expire_on_commit=False)


def init(url=None, migrate=True):
    """Open the database (DATABASE_URL by default) and apply the pending migrations. Returns the URL."""
    global engine
    url = config.database_url(url)
    if engine is not None:
        engine.dispose()
    engine = create_engine(url, pool_pre_ping=True, future=True)
    SessionLocal.configure(bind=engine)
    if migrate:
        upgrade()
    return url


def alembic_config():
    from alembic.config import Config
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(MIGRATIONS))
    return cfg


def upgrade(revision="head"):
    """alembic upgrade on the open engine."""
    from alembic import command
    cfg = alembic_config()
    with engine.begin() as con:
        cfg.attributes["connection"] = con
        command.upgrade(cfg, revision)


@contextmanager
def session_scope():
    """One transaction."""
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
