"""Stock in relational tables (R3): ledger, balances kept with each movement, one movement per product at a time."""

import threading

from conftest import API_KEY
from sqlalchemy import text

from powererp import database


def _sql(query, **params):
    with database.engine.connect() as con:
        return con.execute(text(query), params).all()


def _qty(client, product="CLAV-SF", wh="ENT-01"):
    p = client.get(f"/api/products/{product}").get_json()
    return float(next((s["dQtyOnHand"] for s in p["stock"] if s["cWarehouse"] == wh), 0))


def test_balance_table_follows_the_movements(client):
    before = _qty(client)
    r = client.post(
        "/api/stock-movements",
        json={"cType": "IN", "cProduct": "CLAV-SF", "dQty": "5", "cWarehouse": "ENT-01", "cLocation": "A-01-02-A"},
    )
    assert r.status_code == 201
    assert _qty(client) == before + 5
    total = _sql("SELECT sum(qty) FROM stock_balances WHERE lower(product) = 'clav-sf' AND lower(warehouse) = 'ent-01'")
    assert float(total[0][0]) == before + 5


def test_balances_match_a_replay_of_the_ledger(client):
    """The running balances equal the balances recalculated from every movement."""
    client.post(
        "/api/stock-movements",
        json={"cType": "IN", "cProduct": "CLAV-SF", "dQty": "3", "cWarehouse": "ENT-01", "cLocation": "A-01-02-A"},
    )
    rows = _sql(
        "SELECT lower(product), lower(warehouse), lower(location), lower(lot), lower(serial), qty FROM stock_balances"
    )
    running = {r[:5]: float(r[5]) for r in rows}
    client.post("/api/reset")  # reset rebuilds the balances from the seed movements only
    assert running  # balances exist
    rebuilt = {
        r[:5]: float(r[5])
        for r in _sql(
            "SELECT lower(product), lower(warehouse), lower(location), lower(lot), lower(serial), qty FROM stock_balances"
        )
    }
    key = ("clav-sf", "ent-01", "a-01-02-a", "", "")
    assert running[key] == rebuilt[key] + 3


def test_movements_cannot_be_changed(client):
    no = client.get("/api/stock-movements").get_json()["items"][0]["iNo"]
    assert client.put(f"/api/stock-movements/{no}", json={"dQty": "1"}).status_code == 409
    assert client.delete(f"/api/stock-movements/{no}").status_code == 409


def test_two_simultaneous_issues_cannot_both_take_the_last_units(app, client):
    """Two requests issue the whole available quantity at the same time: one succeeds, the other is refused."""
    avail = None
    for s in client.get("/api/inventory/stock?size=500").get_json()["items"]:
        if s["cProduct"] == "CLAV-SF" and s["cLocation"] == "A-01-02-A" and not s["cLot"]:
            avail = s["dQtyAvailable"]
    assert avail and float(avail) > 0
    body = {"cType": "OUT", "cProduct": "CLAV-SF", "dQty": avail, "cWarehouse": "ENT-01", "cLocation": "A-01-02-A"}
    results = []
    barrier = threading.Barrier(2)

    def issue():
        c = app.test_client()
        c.environ_base["HTTP_X_API_KEY"] = API_KEY
        barrier.wait()
        results.append(c.post("/api/stock-movements", json=body).status_code)

    threads = [threading.Thread(target=issue) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [201, 400]
    left = _sql(
        "SELECT qty - reserved FROM stock_balances WHERE lower(product) = 'clav-sf' AND lower(location) = 'a-01-02-a' "
        "AND lot = '' AND serial = ''"
    )
    assert float(left[0][0]) == 0


def test_count_is_stored_with_its_lines(client):
    r = client.post(
        "/api/stock-counts", json={"cWarehouse": "ENT-01", "cDescription": "Cycle A", "cLocationPrefix": "A-01"}
    )
    assert r.status_code == 201
    c = r.get_json()
    assert c["lineCount"] > 0 and "movements" not in c
    rows = _sql(
        "SELECT count(*) FROM stock_counts_lines l JOIN stock_counts c ON c.id = l.parent_id WHERE c.no = :n",
        n=c["iNo"],
    )
    assert rows[0][0] == c["lineCount"]


def test_a_movement_waits_for_another_transaction_on_the_same_product(app):
    """While another transaction holds the product (it is posting a movement), a new movement of that product waits;
    so it is checked against the stock left by the other one, never against a stale balance."""
    import time

    other = database.engine.connect()
    tx = other.begin()
    other.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:k))"),
        {"k": f"stock:{_sql('SELECT id FROM companies WHERE code = :c', c='MAIN')[0][0]}:CLAV-SF"},
    )
    done = []

    def post():
        c = app.test_client()
        c.environ_base["HTTP_X_API_KEY"] = API_KEY
        done.append(
            c.post(
                "/api/stock-movements",
                json={
                    "cType": "IN",
                    "cProduct": "CLAV-SF",
                    "dQty": "1",
                    "cWarehouse": "ENT-01",
                    "cLocation": "A-01-02-A",
                },
            ).status_code
        )

    t = threading.Thread(target=post)
    t.start()
    time.sleep(1.0)
    assert done == []  # blocked by the other transaction
    tx.commit()
    other.close()
    t.join(10)
    assert done == [201]
