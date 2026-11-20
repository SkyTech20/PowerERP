"""Settings (key / value) and the JSON datasets of older databases, in PostgreSQL.

  settings         key / value: session secret, dataset the demo data was seeded from, backup settings and status
  legacy_datasets  JSON documents of older databases (before the relational tables): moved into the tables once
                   at start-up (powererp.factory), then removed.
init() opens the database (DATABASE_URL) and applies the pending migrations.
"""

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from powererp import config, database
from powererp.models import LegacyDataset, Setting


def now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def init(url=None):
    """Open the database and apply the pending migrations. Returns the URL without its password."""
    return config.masked(database.init(url))


session = database.session_scope


# ---------------------------------------------------------------- settings


def get_setting(key, default=None):
    with session() as s:
        row = s.get(Setting, key)
        return row.value if row else default


def set_setting(key, value):
    with session() as s:
        s.execute(
            insert(Setting)
            .values(key=key, value=value)
            .on_conflict_do_update(index_elements=[Setting.key], set_={"value": value})
        )


# ---------------------------------------------------------------- legacy datasets (transition)


def load_datasets():
    """{name: data} of every stored table, or {} when the ERP was never saved."""
    with session() as s:
        return {r.name: r.data for r in s.scalars(select(LegacyDataset))}


def save_datasets(datasets):
    if not datasets:
        return
    stamp = now()
    rows = [{"name": name, "data": data, "updated_at": stamp} for name, data in datasets.items()]
    stmt = insert(LegacyDataset).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[LegacyDataset.name], set_={"data": stmt.excluded.data, "updated_at": stmt.excluded.updated_at}
    )
    with session() as s:
        s.execute(stmt)


def drop_datasets(names):
    """Remove the JSON documents of tables that moved to relational tables."""
    if names:
        with session() as s:
            s.execute(delete(LegacyDataset).where(LegacyDataset.name.in_(list(names))))


def clear_datasets():
    with session() as s:
        s.execute(delete(LegacyDataset))
