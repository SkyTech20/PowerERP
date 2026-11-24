"""
PowerERP test setup.

The app is imported once per test session, on an empty PostgreSQL test database
(TEST_DATABASE_URL; its tables are dropped and re-created by the migrations at the
start of the session) and the fictitious demo dataset (data/demo/). Every test
starts from the original demo data, so tests do not depend on each other: the demo is
loaded once (POST /api/reset) and copied to the schema test_snapshot; before each test
the tables are emptied and filled again from that copy (a few SQL statements instead of
reloading the demo through the ERP, which took most of the time of the suite).

Run from the PowerERP folder:
  docker compose up -d db                    (PostgreSQL on localhost:5433, with the powererp_test database)
  pip install -r requirements-dev.txt && python -m pytest
"""

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

API_KEY = "test-api-key"
ADMIN_PASSWORD = "admin-test-pw"
PW = "/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI"

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://powererp:powererp@127.0.0.1:5433/powererp_test"
)
if "test" not in TEST_DATABASE_URL.rsplit("/", 1)[-1]:
    sys.exit("TEST_DATABASE_URL must point to a database whose name contains 'test': it is emptied.")


def _empty_database(url):
    from powererp.config import database_url

    engine = create_engine(database_url(url))
    with engine.begin() as con:
        con.execute(text("DROP SCHEMA public CASCADE"))
        con.execute(text("CREATE SCHEMA public"))
    engine.dispose()


_empty_database(TEST_DATABASE_URL)
os.environ.update(
    {
        "DATABASE_URL": TEST_DATABASE_URL,
        "ERP_DATASET": "demo",
        "ERP_ADMIN_USER": "admin",
        "ERP_ADMIN_PASSWORD": ADMIN_PASSWORD,
        "ERP_API_KEY": API_KEY,
        "ERP_SECRET_KEY": "test-secret",
        "BACKUP_SCHEDULER": "0",  # tests run the backups themselves
    }
)
os.environ.pop("ERP_COOKIE_SECURE", None)
os.environ.pop("ERP_SCENARIO", None)  # the tests start with the manufacturing demo


@pytest.fixture(scope="session")
def app():
    import app as erp_app  # noqa: E402  (needs the environment above)

    erp_app.app.config.update(TESTING=True)
    return erp_app.app


@pytest.fixture
def anon(app):
    """A client with no login and no API key."""
    return app.test_client()


@pytest.fixture
def client(app):
    """A client authenticated with the API key (what SkyAI and scripts use)."""
    c = app.test_client()
    c.environ_base["HTTP_X_API_KEY"] = API_KEY
    return c


@pytest.fixture
def admin(app):
    """A client logged in as the administrator (session cookie)."""
    c = app.test_client()
    r = c.post("/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.get_json()
    return c


SNAPSHOT = "test_snapshot"


class DemoSnapshot:
    """A copy of every table of the demo data (schema test_snapshot), put back before each test."""

    def __init__(self, url):
        from sqlalchemy import MetaData

        from powererp.config import database_url

        self.engine = create_engine(database_url(url))
        meta = MetaData()
        meta.reflect(self.engine, schema="public")
        # parents before children (foreign keys); alembic_version is not data
        self.tables = [t.name for t in meta.sorted_tables if t.name != "alembic_version"]
        self.serials = [t.name for t in meta.sorted_tables if "id" in t.c and t.c.id.autoincrement is not False]
        # DELETE, not TRUNCATE: the tables are small and TRUNCATE rewrites the files of every table (10x slower)
        empty = "; ".join(f"DELETE FROM public.{n}" for n in reversed(self.tables))
        copies = "; ".join(f"INSERT INTO public.{n} SELECT * FROM {SNAPSHOT}.{n}" for n in self.tables)
        sequences = ", ".join(
            f"setval(pg_get_serial_sequence('public.{n}', 'id'), "
            f"COALESCE((SELECT max(id) FROM public.{n}), 0) + 1, false)"
            for n in self.serials
        )
        self.restore_sql = f"{empty}; {copies}; SELECT {sequences}"

    def take(self):
        with self.engine.begin() as con:
            con.execute(text(f"DROP SCHEMA IF EXISTS {SNAPSHOT} CASCADE"))
            con.execute(text(f"CREATE SCHEMA {SNAPSHOT}"))
            for n in self.tables:
                con.execute(text(f"CREATE TABLE {SNAPSHOT}.{n} AS TABLE public.{n}"))

    def restore(self):
        with self.engine.begin() as con:
            con.exec_driver_sql(self.restore_sql)


@pytest.fixture(scope="session")
def demo_snapshot(app):
    c = app.test_client()
    c.environ_base["HTTP_X_API_KEY"] = API_KEY
    assert c.post("/api/reset").status_code == 200
    snap = DemoSnapshot(TEST_DATABASE_URL)
    snap.take()
    yield snap
    snap.engine.dispose()


@pytest.fixture(autouse=True)
def _fresh_data(demo_snapshot):
    demo_snapshot.restore()
    yield


def new_po(client, cpo="990001", **over):
    body = {
        "cPO": cpo,
        "cSupplierCode": "TECBUR",
        "dCreationDate": "2026-10-01",
        "dFreight": "0",
        "dGST": "0",
        "dPST": "0",
        "lUnbilled": True,
        "lines": [
            {"cUnique": "1", "cProductcode": "ITEM-1", "cProductDesc": "Item 1", "dQuantity": "2", "dUnitCost": "10.00"}
        ],
    }
    body.update(over)
    return client.post("/api/purchase-orders", json=body)


def new_reception(client, no="990101", po="500301", **over):
    body = {
        "NoReception": no,
        "NoBonCommande": po,
        "DateReception": "2026-10-02",
        "CodeFournisseur": "PAPCEN",
        "Devise": "CAD",
        "lUnbilled": True,
        "Transport": "0",
        "TPS": "0",
        "TVQ": "0",
        "lines": [
            {
                "CodeArticle": "PAP-01",
                "Description": "Papier",
                "QuantiteCommandee": "5",
                "QuantiteRecue": "5",
                "PrixUnitaire": "4.00",
            }
        ],
    }
    body.update(over)
    return client.post("/api/receptions", json=body)
