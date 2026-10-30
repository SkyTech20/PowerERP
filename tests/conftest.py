"""
PowerERP test setup.

The app is imported once per test session, on a temporary SQLite file and the
fictitious demo dataset (data/demo/). Every test starts from the original demo
data (POST /api/reset), so tests do not depend on each other.

Run from the PowerERP folder:  pip install -r requirements-dev.txt && python -m pytest
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

API_KEY = "test-api-key"
ADMIN_PASSWORD = "admin-test-pw"
PW = "/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI"

_tmp = tempfile.mkdtemp(prefix="powererp-tests-")
os.environ.update({
    "ERP_DB_PATH": os.path.join(_tmp, "powererp.db"),
    "ERP_DATASET": "demo",
    "ERP_ADMIN_USER": "admin",
    "ERP_ADMIN_PASSWORD": ADMIN_PASSWORD,
    "ERP_API_KEY": API_KEY,
    "ERP_SECRET_KEY": "test-secret",
})
os.environ.pop("ERP_COOKIE_SECURE", None)


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


@pytest.fixture(autouse=True)
def _fresh_data(app):
    c = app.test_client()
    c.environ_base["HTTP_X_API_KEY"] = API_KEY
    assert c.post("/api/reset").status_code == 200
    yield


def new_po(client, cpo="990001", **over):
    body = {
        "cPO": cpo, "cSupplierCode": "TECBUR", "dCreationDate": "2026-10-01",
        "dFreight": "0", "dGST": "0", "dPST": "0", "lUnbilled": True,
        "lines": [{"cUnique": "1", "cProductcode": "ITEM-1", "cProductDesc": "Item 1", "dQuantity": "2", "dUnitCost": "10.00"}],
    }
    body.update(over)
    return client.post("/api/purchase-orders", json=body)


def new_reception(client, no="990101", po="500301", **over):
    body = {
        "NoReception": no, "NoBonCommande": po, "DateReception": "2026-10-02",
        "CodeFournisseur": "PAPCEN", "Devise": "CAD", "lUnbilled": True,
        "Transport": "0", "TPS": "0", "TVQ": "0",
        "lines": [{"CodeArticle": "PAP-01", "Description": "Papier", "QuantiteCommandee": "5", "QuantiteRecue": "5", "PrixUnitaire": "4.00"}],
    }
    body.update(over)
    return client.post("/api/receptions", json=body)
