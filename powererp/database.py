"""PostgreSQL connection (SQLAlchemy 2.0) and schema migrations (Alembic).

init() opens the engine and brings the schema up to date (alembic upgrade head), so a new
database needs nothing else. session_scope() is one transaction: committed at the end of the
block, rolled back on error.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from flask import g, has_request_context
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


# ---------------------------------------------------------------- unit of work
# The ERP tables use one session per HTTP request (committed when the response is a success, rolled back
# otherwise), so a request that fails half-way leaves nothing behind. Outside a request (start-up, seed,
# scripts), `with unit_of_work():` gives the same.

_standalone = ContextVar("powererp_session", default=None)


def current():
    """The session of the current request, or of the enclosing unit_of_work()."""
    s = _standalone.get()
    if s is not None:
        return s
    if has_request_context():
        if "_db_session" not in g:
            g._db_session = SessionLocal()
        return g._db_session
    raise RuntimeError("no database session: use database.unit_of_work() outside a request")


@contextmanager
def unit_of_work():
    s = SessionLocal()
    token = _standalone.set(s)
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        _standalone.reset(token)
        s.close()


def init_app(app):
    """Commit the request's session on success (status < 400), roll it back otherwise."""
    @app.after_request
    def _commit(response):
        s = g.pop("_db_session", None)
        if s is not None:
            try:
                if response.status_code < 400:
                    s.commit()
                else:
                    s.rollback()
            finally:
                s.close()
        return response

    @app.teardown_request
    def _close(exc):
        s = g.pop("_db_session", None)
        if s is not None:
            s.rollback()
            s.close()
