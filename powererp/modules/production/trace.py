"""Traceability of a lot (step 3 of the SCOR / ISO plan): where it comes from, where it went, and what a recall must reach.

From the stock movements (every movement keeps its document: REC reception, PROD production order, SO sales invoice,
MAN / CNT / INV adjustments) and the lots the production orders used and made (M3b):
- origin (one step back, then on): the receptions of the lot (supplier, supplier lot, PO) and, for a lot made here,
  the lots of the materials each production order used, followed back the same way down to the suppliers;
- uses (one step forward, then on): the production orders that used the lot and the lots they made, followed
  forward the same way;
- recall: for the lot and every lot made from it (directly or not): the customers it was sold to (invoice, date,
  quantity, less what came back on a credit note), the stock still on hand (warehouse, location) and the orders
  still open that use or make one of them;
- timeline: every stock movement of the lot.
export() writes the same as a spreadsheet (.xlsx: Summary, Origin, Uses, Customers, Stock, Movements).
Nothing is changed: this only reads.
"""

from __future__ import annotations

import io
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from powererp.core.errors import AppError
from powererp.core.values import number, quantity, text

Row = dict[str, Any]
Rows = list[Row]
Key = tuple[str, str]  # (product, lot), upper case
EPS = 1e-9
MAX_DEPTH = 25
OPEN = ("released", "in_progress", "completed")


def key(product: Any, lot: Any) -> Key:
    return text(product).upper(), text(lot).upper()


class TraceService:
    def __init__(self, deps: dict[str, Callable[[], Any]]):
        """deps: stock, orders (ProductionOrderService), receptions (ReceptionService), invoices (sales), products (find)."""
        self.deps = deps

    def _get(self, name: str) -> Any:
        return self.deps[name]()

    # ---------------------------------------------------------- lookups
    def products(self, fields: tuple[str, ...] = ("cDescFR",)) -> Rows:
        """The products that have lots in the stock (code, label = description; both descriptions for a change of language)."""
        codes = sorted({m["cProduct"].upper() for m in self._get("stock").ledger.all() if text(m.get("cLot"))})
        find = self._get("products")
        rows = []
        for code in codes:
            p = find(code) or {"cCode": code}
            label = next((p[f] for f in fields if p.get(f)), "")
            rows.append(
                {
                    "code": p["cCode"],
                    "label": label,
                    "cDescFR": text(p.get("cDescFR")),
                    "cDescEN": text(p.get("cDescEN")),
                }
            )
        return rows

    def lots(self, product: str) -> Rows:
        """The lots of a product known to the stock (code = lot; label = expiry, on hand)."""
        p = text(product).upper()
        seen: dict[str, Row] = {}
        for m in self._get("stock").ledger.all():
            if m["cProduct"].upper() == p and text(m.get("cLot")):
                seen.setdefault(m["cLot"].upper(), {"code": m["cLot"], "dExpiry": text(m.get("dExpiry"))[:10]})
        on_hand: dict[str, float] = defaultdict(float)
        for (bp, _w, _l, lot, _s), b in self._get("stock").balances().items():
            if bp == p:
                on_hand[lot] += b["qty"]
        rows = []
        for k, r in sorted(seen.items()):
            parts = [r["dExpiry"], quantity(on_hand.get(k, 0.0))]
            rows.append({"code": r["code"], "label": " · ".join(x for x in parts if x)})
        return rows

    # ---------------------------------------------------------- trace
    def trace(self, product: str, lot: str) -> Row:
        ctx = self._context()
        k = key(product, lot)
        if not text(lot) or k not in ctx["moves"]:
            raise AppError("unknown_lot", "cLot", 404)
        origin = self._origin(ctx, k, 0, set())
        uses = self._uses(ctx, k, 0, set())
        reached = self._reached(ctx, k)
        prod = ctx["product"](k[0])
        return {
            "cProduct": prod.get("cCode", k[0]),
            "cLot": ctx["lot_name"].get(k, lot),
            "cDescFR": text(prod.get("cDescFR")),
            "cDescEN": text(prod.get("cDescEN")),
            "cUOM": text(prod.get("cStockUOM")),
            "origin": origin,
            "uses": uses,
            "recall": self._recall(ctx, reached),
            "movements": [self._movement(ctx, m) for m in ctx["moves"][k]],
        }

    def _context(self) -> Row:
        """Everything the trace reads, indexed once."""
        moves: dict[Key, Rows] = defaultdict(list)
        lot_name: dict[Key, str] = {}
        for m in self._get("stock").ledger.all():
            if text(m.get("cLot")):
                k = key(m["cProduct"], m["cLot"])
                moves[k].append(m)
                lot_name.setdefault(k, m["cLot"])
        made_by: dict[Key, list[tuple[Row, Row]]] = defaultdict(list)
        used_by: dict[Key, list[tuple[Row, float]]] = defaultdict(list)
        orders = self._get("orders").repo.all()
        for o in orders:
            for out in o.get("outputs", []):
                if text(out.get("cLot")):
                    made_by[key(o["cProduct"], out["cLot"])].append((o, out))
            net: dict[Key, float] = defaultdict(float)
            for i in o.get("issues", []):
                if text(i.get("cLot")):
                    net[key(i["cComponent"], i["cLot"])] += number(i["dQty"])
            for k, q in net.items():
                if q > EPS:
                    used_by[k].append((o, q))
        cache: dict[str, Row] = {}

        def product(code: str) -> Row:
            if code not in cache:
                cache[code] = self._get("products")(code) or {}
            return cache[code]

        return {
            "moves": moves,
            "lot_name": lot_name,
            "made_by": made_by,
            "used_by": used_by,
            "orders": orders,
            "product": product,
            "sold": self._sold(),
            "receptions": {},
        }

    def _node(self, ctx: Row, k: Key) -> Row:
        prod = ctx["product"](k[0])
        expiry = next((text(m.get("dExpiry"))[:10] for m in ctx["moves"].get(k, []) if text(m.get("dExpiry"))), "")
        return {
            "cProduct": prod.get("cCode", k[0]),
            "cLot": ctx["lot_name"].get(k, k[1]),
            "cDescFR": text(prod.get("cDescFR")),
            "cDescEN": text(prod.get("cDescEN")),
            "cUOM": text(prod.get("cStockUOM")),
            "dExpiry": expiry,
        }

    def _origin(self, ctx: Row, k: Key, depth: int, seen: set[Key]) -> Row:
        node = {**self._node(ctx, k), "sources": [], "inputs": []}
        if k in seen or depth > MAX_DEPTH:
            node["lLoop"] = True
            return node
        seen = seen | {k}
        for m in ctx["moves"].get(k, []):
            q = number(m["dQty"])
            if m["cDocType"] == "REC" and m["cType"] == "IN":
                node["sources"].append(self._reception(ctx, k, m))
            elif m["cDocType"] not in ("PROD", "SO") and (
                m["cType"] == "IN" or (m["cType"] in ("ADJ", "CNT") and q > 0)
            ):
                node["sources"].append(
                    {
                        "cKind": "other",
                        "cDocType": m["cDocType"],
                        "cDocNo": text(m.get("cDocNo")),
                        "dDate": text(m["dDate"])[:10],
                        "dQty": m["dQty"],
                    }
                )
        for o, out in ctx["made_by"].get(k, []):
            node["sources"].append(
                {
                    "cKind": "production",
                    "iOrder": o["iNo"],
                    "dDate": text(out.get("dDate")),
                    "dQty": out["dQty"],
                    "cStatus": o["cStatus"],
                }
            )
            used: dict[Key, float] = defaultdict(float)
            for i in o.get("issues", []):
                if text(i.get("cLot")):
                    used[key(i["cComponent"], i["cLot"])] += number(i["dQty"])
            for ck, q in used.items():
                if q > EPS:
                    child = self._origin(ctx, ck, depth + 1, seen)
                    node["inputs"].append({**child, "iOrder": o["iNo"], "dQtyUsed": quantity(q)})
        return node

    def _reception(self, ctx: Row, k: Key, m: Row) -> Row:
        no = text(m.get("cDocNo"))
        if no not in ctx["receptions"]:
            try:
                ctx["receptions"][no] = self._get("receptions").get(no)
            except Exception:  # a reception deleted since: the movement keeps what is needed
                ctx["receptions"][no] = {}
        rec = ctx["receptions"][no]
        line: Row = next(
            (ln for ln in rec.get("lines", []) if key(ln.get("CodeArticle"), ln.get("cLot")) == k),
            {},
        )
        return {
            "cKind": "reception",
            "cDocNo": no,
            "dDate": text(m["dDate"])[:10],
            "dQty": m["dQty"],
            "cSupplier": text(rec.get("CodeFournisseur")) or text(m.get("cReason")),
            "cSupplierName": text(rec.get("Fournisseur")),
            "cSupplierLot": text(line.get("cSupplierLot")),
            "cPO": text(rec.get("NoBonCommande")),
        }

    def _uses(self, ctx: Row, k: Key, depth: int, seen: set[Key]) -> Row:
        node = {**self._node(ctx, k), "orders": []}
        if k in seen or depth > MAX_DEPTH:
            node["lLoop"] = True
            return node
        seen = seen | {k}
        for o, q in ctx["used_by"].get(k, []):
            outputs: dict[Key, float] = defaultdict(float)
            for out in o.get("outputs", []):
                if text(out.get("cLot")):
                    outputs[key(o["cProduct"], out["cLot"])] += number(out["dQty"])
            node["orders"].append(
                {
                    "iOrder": o["iNo"],
                    "cStatus": o["cStatus"],
                    "cProduct": o["cProduct"],
                    "dQtyUsed": quantity(q),
                    "outputs": [
                        {**self._uses(ctx, ok, depth + 1, seen), "dQtyMade": quantity(oq)} for ok, oq in outputs.items()
                    ],
                }
            )
        return node

    def _reached(self, ctx: Row, start: Key) -> list[Key]:
        """The lot and every lot made from it, directly or not (breadth first)."""
        out, todo = [start], [start]
        while todo:
            k = todo.pop(0)
            for o, _q in ctx["used_by"].get(k, []):
                for made in o.get("outputs", []):
                    mk = key(o["cProduct"], made.get("cLot"))
                    if made.get("cLot") and mk not in out:
                        out.append(mk)
                        todo.append(mk)
        return out

    def _sold(self) -> dict[int, Row]:
        """Stock movement no -> the posted sales document that moved it (invoice or credit note)."""
        out: dict[int, Row] = {}
        try:
            invoices = self._get("invoices").repo.all()
        except KeyError:  # no sales module
            return out
        for inv in invoices:
            if inv.get("cStatus") != "posted":
                continue
            for a in inv.get("allocations", []):
                if a.get("iMovement"):
                    out[int(a["iMovement"])] = inv
        return out

    def _recall(self, ctx: Row, reached: list[Key]) -> Row:
        customers: Rows = []
        stock: Rows = []
        lots = set(reached)
        for k in reached:
            node = self._node(ctx, k)
            for m in ctx["moves"].get(k, []):
                if m["cDocType"] != "SO":
                    continue
                inv = ctx["sold"].get(int(m.get("iNo") or 0), {})
                back = m["cType"] == "ADJ"
                customers.append(
                    {
                        **node,
                        "cCustomer": text(inv.get("cCustomer")) or text(m.get("cReason")),
                        "cCustomerName": text(inv.get("cCustomerName")),
                        "cInvoiceNo": text(inv.get("cInvoiceNo")) or text(m.get("cDocNo")),
                        "cType": "credit" if back else "invoice",
                        "dDate": text(m["dDate"])[:10],
                        "dQty": quantity(-abs(number(m["dQty"])) if back else abs(number(m["dQty"]))),
                    }
                )
        for (p, w, loc, lot, serial), b in self._get("stock").balances().items():
            if (p, lot) in lots and abs(b["qty"]) > EPS:
                stock.append(
                    {
                        **self._node(ctx, (p, lot)),
                        "cWarehouse": w,
                        "cLocation": loc,
                        "cSerial": serial,
                        "dQty": quantity(b["qty"]),
                    }
                )
        orders = []
        for o in ctx["orders"]:
            if o["cStatus"] not in OPEN:
                continue
            touches = any(key(i["cComponent"], i.get("cLot")) in lots for i in o.get("issues", [])) or any(
                key(o["cProduct"], out.get("cLot")) in lots for out in o.get("outputs", [])
            )
            if touches:
                orders.append({"iOrder": o["iNo"], "cStatus": o["cStatus"], "cProduct": o["cProduct"]})
        net: dict[str, float] = defaultdict(float)
        for c in customers:
            net[c["cCustomer"]] += number(c["dQty"])
        return {
            "lots": [self._node(ctx, k) for k in reached],
            "customers": customers,
            "iCustomers": sum(1 for q in net.values() if q > EPS),
            "stock": stock,
            "orders": orders,
        }

    @staticmethod
    def _movement(ctx: Row, m: Row) -> Row:
        inv = ctx["sold"].get(int(m.get("iNo") or 0), {})
        return {
            "iNo": m.get("iNo"),
            "dDate": text(m["dDate"])[:10],
            "cType": m["cType"],
            "cDocType": m["cDocType"],
            "cDocNo": text(inv.get("cInvoiceNo")) or text(m.get("cDocNo")),
            "cWarehouse": m["cWarehouse"],
            "cLocation": text(m.get("cLocation")),
            "dQty": m["dQty"],
            "cReason": text(m.get("cReason")),
            "cUser": text(m.get("cUser")),
        }

    # ---------------------------------------------------------- export
    def export(self, product: str, lot: str, lang: str = "en") -> bytes:
        """The trace as a spreadsheet (.xlsx)."""
        from openpyxl import Workbook
        from openpyxl.styles import Font

        t = self.trace(product, lot)
        fr = lang == "fr"
        L = LABELS["fr" if fr else "en"]
        desc = "cDescFR" if fr else "cDescEN"

        def d(n: Row) -> str:
            return text(n.get(desc)) or text(n.get("cDescFR"))

        wb = Workbook()
        sheets: list[tuple[str, list[str], list[list[Any]]]] = []
        summary = [
            [L["product"], t["cProduct"]],
            [L["description"], d(t)],
            [L["lot"], t["cLot"]],
            [L["lots_reached"], len(t["recall"]["lots"])],
            [L["customers"], t["recall"]["iCustomers"]],
            [L["stock_rows"], len(t["recall"]["stock"])],
            [L["open_orders"], ", ".join(str(o["iOrder"]) for o in t["recall"]["orders"])],
        ]
        origin: list[list[Any]] = []

        def walk_origin(n: Row, level: int) -> None:
            for s in n["sources"]:
                partner = f"{s.get('cSupplier', '')} {s.get('cSupplierName', '')}".strip()
                doc = s.get("cDocNo") or (f"{L['order']} {s['iOrder']}" if s.get("iOrder") else s.get("cDocType", ""))
                origin.append(
                    [
                        level,
                        n["cProduct"],
                        d(n),
                        n["cLot"],
                        n["dExpiry"],
                        L[s["cKind"]],
                        doc,
                        s.get("dDate", ""),
                        partner,
                        s.get("cSupplierLot", ""),
                        s.get("cPO", ""),
                        number(s.get("dQty")),
                        n["cUOM"],
                    ]
                )
            for c in n["inputs"]:
                walk_origin(c, level + 1)

        walk_origin(t["origin"], 0)
        uses: list[list[Any]] = []

        def walk_uses(n: Row, level: int) -> None:
            for o in n["orders"]:
                for out in o["outputs"] or [{"cProduct": o["cProduct"], "cLot": "", "dQtyMade": "", "orders": []}]:
                    uses.append(
                        [
                            level,
                            n["cProduct"],
                            n["cLot"],
                            o["iOrder"],
                            L["status"].get(o["cStatus"], o["cStatus"]),
                            number(o["dQtyUsed"]),
                            out["cProduct"],
                            out["cLot"],
                            number(out.get("dQtyMade")),
                        ]
                    )
                    if out.get("orders"):
                        walk_uses(out, level + 1)

        walk_uses(t["uses"], 0)
        customers = [
            [
                c["cCustomer"],
                c["cCustomerName"],
                L[c["cType"]],
                c["cInvoiceNo"],
                c["dDate"],
                c["cProduct"],
                d(c),
                c["cLot"],
                number(c["dQty"]),
                c["cUOM"],
            ]
            for c in t["recall"]["customers"]
        ]
        stock = [
            [
                s["cProduct"],
                d(s),
                s["cLot"],
                s["dExpiry"],
                s["cWarehouse"],
                s["cLocation"],
                number(s["dQty"]),
                s["cUOM"],
            ]
            for s in t["recall"]["stock"]
        ]
        moves = [
            [
                m["iNo"],
                m["dDate"],
                L["mv"].get(m["cType"], m["cType"]),
                (
                    L["doc"].get(m["cDocType"], m["cDocType"])
                    if m["cDocType"] != "SO"
                    else L["credit" if m["cType"] == "ADJ" else "invoice"]
                ),
                m["cDocNo"],
                m["cWarehouse"],
                m["cLocation"],
                number(m["dQty"]),
                m["cReason"],
                m["cUser"],
            ]
            for m in t["movements"]
        ]
        sheets = [
            (L["s_summary"], [L["field"], L["value"]], summary),
            (L["s_origin"], L["h_origin"], origin),
            (L["s_uses"], L["h_uses"], uses),
            (L["s_customers"], L["h_customers"], customers),
            (L["s_stock"], L["h_stock"], stock),
            (L["s_moves"], L["h_moves"], moves),
        ]
        first = True
        for title, head, rows in sheets:
            ws = wb.active if first else wb.create_sheet()
            first = False
            ws.title = title
            ws.append(head)
            for cell in ws[1]:
                cell.font = Font(bold=True)
            for r in rows:
                ws.append(r)
            for i, h in enumerate(head, 1):
                width = max([len(str(h))] + [len(str(r[i - 1])) for r in rows if i - 1 < len(r)])
                ws.column_dimensions[ws.cell(1, i).column_letter].width = min(max(width + 2, 8), 50)
            ws.freeze_panes = "A2"
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()


LABELS: dict[str, dict[str, Any]] = {
    "en": {
        "product": "Product",
        "description": "Description",
        "lot": "Lot",
        "lots_reached": "Lots made from it (with itself)",
        "customers": "Customers reached",
        "stock_rows": "Stock lines still on hand",
        "open_orders": "Open production orders",
        "order": "Order",
        "reception": "Reception",
        "production": "Production",
        "other": "Other entry",
        "invoice": "Invoice",
        "credit": "Credit note",
        "field": "Field",
        "value": "Value",
        "status": {
            "draft": "Draft",
            "released": "Released",
            "in_progress": "In progress",
            "completed": "Completed",
            "closed": "Closed",
            "cancelled": "Cancelled",
        },
        "mv": {
            "IN": "Receipt",
            "OUT": "Issue",
            "TRF": "Transfer",
            "ADJ": "Adjustment",
            "CNT": "Count",
            "RSV": "Reservation",
        },
        "doc": {
            "MAN": "Manual",
            "PO": "PO",
            "REC": "Reception",
            "INV": "Invoice",
            "CNT": "Count",
            "PROD": "Production",
        },
        "s_summary": "Summary",
        "s_origin": "Origin",
        "s_uses": "Uses",
        "s_customers": "Customers",
        "s_stock": "Stock",
        "s_moves": "Movements",
        "h_origin": [
            "Level",
            "Product",
            "Description",
            "Lot",
            "Expiry",
            "Source",
            "Document",
            "Date",
            "Supplier",
            "Supplier lot",
            "PO",
            "Quantity",
            "Unit",
        ],
        "h_uses": [
            "Level",
            "Product",
            "Lot",
            "Order",
            "Status",
            "Quantity used",
            "Product made",
            "Lot made",
            "Quantity made",
        ],
        "h_customers": [
            "Customer",
            "Name",
            "Document",
            "Number",
            "Date",
            "Product",
            "Description",
            "Lot",
            "Quantity",
            "Unit",
        ],
        "h_stock": ["Product", "Description", "Lot", "Expiry", "Warehouse", "Location", "Quantity", "Unit"],
        "h_moves": [
            "Movement",
            "Date",
            "Type",
            "Document",
            "Number",
            "Warehouse",
            "Location",
            "Quantity",
            "Reason",
            "User",
        ],
    },
    "fr": {
        "product": "Produit",
        "description": "Description",
        "lot": "Lot",
        "lots_reached": "Lots fabriqués avec (lui compris)",
        "customers": "Clients touchés",
        "stock_rows": "Lignes de stock encore en main",
        "open_orders": "Ordres de fabrication ouverts",
        "order": "Ordre",
        "reception": "Réception",
        "production": "Production",
        "other": "Autre entrée",
        "invoice": "Facture",
        "credit": "Note de crédit",
        "field": "Champ",
        "value": "Valeur",
        "status": {
            "draft": "Brouillon",
            "released": "Lancé",
            "in_progress": "En cours",
            "completed": "Terminé",
            "closed": "Fermé",
            "cancelled": "Annulé",
        },
        "mv": {
            "IN": "Entrée",
            "OUT": "Sortie",
            "TRF": "Transfert",
            "ADJ": "Ajustement",
            "CNT": "Inventaire",
            "RSV": "Réservation",
        },
        "doc": {
            "MAN": "Manuel",
            "PO": "BC",
            "REC": "Réception",
            "INV": "Facture",
            "CNT": "Inventaire",
            "PROD": "Production",
        },
        "s_summary": "Résumé",
        "s_origin": "Origine",
        "s_uses": "Utilisations",
        "s_customers": "Clients",
        "s_stock": "Stock",
        "s_moves": "Mouvements",
        "h_origin": [
            "Niveau",
            "Produit",
            "Description",
            "Lot",
            "Expiration",
            "Source",
            "Document",
            "Date",
            "Fournisseur",
            "Lot fournisseur",
            "BC",
            "Quantité",
            "Unité",
        ],
        "h_uses": [
            "Niveau",
            "Produit",
            "Lot",
            "Ordre",
            "Statut",
            "Quantité utilisée",
            "Produit fabriqué",
            "Lot fabriqué",
            "Quantité fabriquée",
        ],
        "h_customers": [
            "Client",
            "Nom",
            "Document",
            "Numéro",
            "Date",
            "Produit",
            "Description",
            "Lot",
            "Quantité",
            "Unité",
        ],
        "h_stock": ["Produit", "Description", "Lot", "Expiration", "Entrepôt", "Emplacement", "Quantité", "Unité"],
        "h_moves": [
            "Mouvement",
            "Date",
            "Type",
            "Document",
            "Numéro",
            "Entrepôt",
            "Emplacement",
            "Quantité",
            "Motif",
            "Utilisateur",
        ],
    },
}
