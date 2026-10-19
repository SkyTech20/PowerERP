"""
PowerERP — best supplier for each item of an internal purchase requisition.

SkyAI sends the items of a requisition (its "Offer" template) to getBestSupplier.p.
For each item the ERP:
  1. finds the product in the purchase history (same code, or a description close enough;
     the AI matches the free-text descriptions the keyword match could not place),
  2. computes, per supplier that sold it, exact metrics from the history: average and last
     unit price, lead time (reception date - order date), on-time rate (reception on or
     before the PO due date), conformity (quantity received / ordered), number of orders,
  3. scores the suppliers with the weights of Purchasing > Supplier selection (settings),
  4. lets the AI (Gemini) rank them with those weights and the free instructions and write
     the reason shown in SkyAI. Without an AI key, or when the AI fails, the rule score and a
     standard reason are used ("engine": "rules"), so the demo never stops.

Settings live in the settings table: key "supplier_selection" for the criteria, key "ai" for the
AI key and model (Purchasing > Supplier selection, administrators only; the key is never sent back).
"""
import json
import logging
import re
import unicodedata
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

import db

logger = logging.getLogger(__name__)

SETTINGS_KEY = "supplier_selection"
DEFAULT_SETTINGS = {
    "weights": {"price": 40, "leadTime": 25, "onTime": 20, "quality": 15},
    "historyMonths": 12,
    "minOrders": 1,
    "tieMargin": 5,
    "maxCandidates": 5,
    "useAI": True,
    "instructions": "",
}
CRITERIA = ("price", "leadTime", "onTime", "quality")
MATCH_THRESHOLD = 0.6


# ---------------------------------------------------------------- settings

def _int(value, default, lo, hi):
    try:
        return max(lo, min(hi, int(float(value))))
    except (TypeError, ValueError):
        return default


def clean_settings(p):
    """Validate a settings payload; unknown keys are dropped, numbers are clamped."""
    d = DEFAULT_SETTINGS
    w = p.get("weights") if isinstance(p.get("weights"), dict) else {}
    weights = {k: _int(w.get(k), d["weights"][k], 0, 100) for k in CRITERIA}
    if not any(weights.values()):
        weights = dict(d["weights"])
    return {
        "weights": weights,
        "historyMonths": _int(p.get("historyMonths"), d["historyMonths"], 1, 60),
        "minOrders": _int(p.get("minOrders"), d["minOrders"], 1, 50),
        "tieMargin": _int(p.get("tieMargin"), d["tieMargin"], 0, 50),
        "maxCandidates": _int(p.get("maxCandidates"), d["maxCandidates"], 1, 10),
        "useAI": bool(p.get("useAI", d["useAI"])),
        "instructions": str(p.get("instructions") or "")[:2000],
    }


def get_settings():
    raw = db.get_setting(SETTINGS_KEY)
    try:
        return clean_settings(json.loads(raw)) if raw else clean_settings({})
    except (ValueError, TypeError):
        return clean_settings({})


def save_settings(p):
    s = clean_settings(p)
    db.set_setting(SETTINGS_KEY, json.dumps(s))
    return s


AI_KEY = "ai"
DEFAULT_MODEL = "gemini-2.5-flash"


def _ai_config():
    try:
        raw = json.loads(db.get_setting(AI_KEY) or "{}")
    except (ValueError, TypeError):
        raw = {}
    return {"apiKey": str(raw.get("apiKey") or ""), "model": str(raw.get("model") or DEFAULT_MODEL)}


def save_ai_config(p):
    """{"model": ..., "apiKey": ...}: a missing or empty apiKey keeps the current key, "clearKey" removes it."""
    cur = _ai_config()
    model = re.sub(r"[^A-Za-z0-9.\-_]", "", str(p.get("model") or cur["model"]))[:80] or DEFAULT_MODEL
    key = cur["apiKey"]
    if p.get("clearKey"):
        key = ""
    elif str(p.get("apiKey") or "").strip():
        key = str(p["apiKey"]).strip()
    db.set_setting(AI_KEY, json.dumps({"apiKey": key, "model": model}))


def ai_status():
    c = _ai_config()
    return {"configured": bool(c["apiKey"]), "provider": "gemini", "model": c["model"],
            "keyHint": ("…" + c["apiKey"][-4:]) if len(c["apiKey"]) >= 8 else ""}


# ---------------------------------------------------------------- text matching

_STOP = {"x", "de", "du", "des", "la", "le", "les", "en", "et", "a", "of", "the", "and", "with", "avec",
         "longueur", "length", "boite", "box", "caisse", "case", "unite", "unit"}
_SYN = {"alu": "aluminium", "aluminum": "aluminium", "pied": "pi", "pieds": "pi", "ft": "pi", "pouce": "po",
        "pouces": "po", "in": "po", "ecrou": "ecrous", "vis": "vis", "rivet": "rivets", "feuilles": "feuille",
        "sheet": "feuille", "angle": "corniere", "tube": "tube", "barre": "barre", "bar": "barre"}


def _norm(text):
    t = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"(\d+)[\s-]+(\d+/\d+)", r"\1-\2", t)  # "1 1/2" and "1-1/2" become the same token


def tokens(text):
    out = set()
    for tok in re.findall(r"[a-z0-9]+(?:[-/.,][a-z0-9]+)*", _norm(text)):
        tok = _SYN.get(tok, tok)
        if tok in _STOP:
            continue
        out.add(tok)
    return out


def match_score(query, candidate):
    q = tokens(query)
    if not q:
        return 0.0
    return len(q & tokens(candidate)) / len(q)


# ---------------------------------------------------------------- history

def _d(value):
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _f(value):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def build_history(ns, months, today=None):
    """Per product code: description and the purchase lines of the last `months` months."""
    today = today or date.today()
    since = today - timedelta(days=int(months * 30.5))
    recs_by_po = {}
    for r in ns["receiving_details"]:
        recs_by_po.setdefault(str(r.get("NoBonCommande", "")), []).append(r)
    products = {}
    for po in ns["po_details"]:
        h = po.get("ttPOheader", {})
        ordered = _d(h.get("dOrderDate"))
        if ordered is None or ordered < since:
            continue
        due = _d(h.get("dDueDate"))
        recs = recs_by_po.get(str(po["cPO"]), [])
        for ln in po.get("ttPOdetail", []):
            code = str(ln.get("cProductcode") or "").strip()
            if not code:
                continue
            p = products.setdefault(code, {"code": code, "desc": ln.get("cProductDesc", ""), "lines": []})
            got, rec_dates = 0.0, []
            for r in recs:
                for a in r.get("Articles", []):
                    if a.get("CodeArticle") == code:
                        got += _f(a.get("QuantiteRecue"))
                        if _d(r.get("DateReception")):
                            rec_dates.append(_d(r.get("DateReception")))
            p["lines"].append({
                "supplier": h.get("cSupplierCode", ""), "supplierName": h.get("cSupplierName", ""),
                "po": po["cPO"], "ordered": ordered, "due": due, "qty": _f(ln.get("dQuantity")),
                "unit": _f(ln.get("dUnitCost")), "received": got, "receivedOn": min(rec_dates) if rec_dates else None,
            })
    return products


def supplier_metrics(lines):
    by = {}
    for ln in lines:
        by.setdefault(ln["supplier"], []).append(ln)
    out = {}
    for sup, ls in by.items():
        ls.sort(key=lambda x: x["ordered"])
        leads = [(x["receivedOn"] - x["ordered"]).days for x in ls if x["receivedOn"]]
        timed = [x for x in ls if x["receivedOn"] and x["due"]]
        qty = sum(x["qty"] for x in ls if x["receivedOn"])
        out[sup] = {
            "name": ls[-1]["supplierName"],
            "avgUnitPrice": round(sum(x["unit"] for x in ls) / len(ls), 2),
            "lastUnitPrice": round(ls[-1]["unit"], 2),
            "avgLeadDays": round(sum(leads) / len(leads), 1) if leads else None,
            "onTimeRate": round(sum(1 for x in timed if x["receivedOn"] <= x["due"]) / len(timed), 2) if timed else None,
            "conformityRate": round(min(1.0, sum(x["received"] for x in ls if x["receivedOn"]) / qty), 2) if qty else None,
            "orders": len(ls),
            "lastPurchase": ls[-1]["ordered"].isoformat(),
        }
    return out


PRICE_POINTS_PER_PCT = 2.5   # price: -2.5 points for each 1 % above the cheapest supplier of the item
LEAD_POINTS_PER_DAY = 5      # lead time: -5 points for each day slower than the fastest supplier


def rule_scores(metrics, weights):
    """0-100 score per supplier: each criterion relative to the best supplier of the item,
    then the weighted average with the configured weights."""
    prices = [m["avgUnitPrice"] for m in metrics.values() if m["avgUnitPrice"] > 0]
    leads = [m["avgLeadDays"] for m in metrics.values() if m["avgLeadDays"] is not None]
    best_price, best_lead = (min(prices) if prices else 0), (min(leads) if leads else 0)
    total = sum(weights.values()) or 1
    clip = lambda v: max(0.0, min(100.0, v))
    scores = {}
    for sup, m in metrics.items():
        part = {
            "price": clip(100 - PRICE_POINTS_PER_PCT * 100 * (m["avgUnitPrice"] / best_price - 1))
            if m["avgUnitPrice"] > 0 and best_price else 50,
            "leadTime": clip(100 - LEAD_POINTS_PER_DAY * (m["avgLeadDays"] - best_lead))
            if m["avgLeadDays"] is not None else 50,
            "onTime": 100 * m["onTimeRate"] if m["onTimeRate"] is not None else 50,
            "quality": 100 * m["conformityRate"] if m["conformityRate"] is not None else 50,
        }
        scores[sup] = round(sum(weights[k] * part[k] for k in CRITERIA) / total)
    return scores


# ---------------------------------------------------------------- reasons (rules engine)

_TXT = {
    "fr": {"score": "Score {s}/100", "price": "prix moyen {v}", "lead": "délai moyen {v} j", "ontime": "{v} % livré à temps",
           "conf": "{v} % conforme", "orders": "{v} commande(s) en {m} mois", "best": " (le meilleur)",
           "none": "Aucun achat de cet article dans l'historique ({m} mois) : choisir le fournisseur manuellement.",
           "nomatch": "Article introuvable dans l'historique d'achats : choisir le fournisseur manuellement."},
    "en": {"score": "Score {s}/100", "price": "average price {v}", "lead": "average lead time {v} d", "ontime": "{v}% on time",
           "conf": "{v}% conforming", "orders": "{v} order(s) in {m} months", "best": " (best)",
           "none": "No purchase of this item in the history ({m} months): choose the supplier manually.",
           "nomatch": "Item not found in the purchase history: choose the supplier manually."},
}


def _money(v, lang):
    s = f"{v:,.2f}"
    return (s.replace(",", " ").replace(".", ",") + " $") if lang == "fr" else "$" + s


def rule_reason(m, score, metrics, months, lang):
    T = _TXT.get(lang, _TXT["en"])
    best = lambda key, low=True: (lambda vals: vals and m[key] == (min(vals) if low else max(vals)))(
        [x[key] for x in metrics.values() if x[key] is not None]) and len(metrics) > 1
    parts = [T["score"].format(s=score),
             T["price"].format(v=_money(m["avgUnitPrice"], lang)) + (T["best"] if best("avgUnitPrice") else "")]
    if m["avgLeadDays"] is not None:
        lead = f"{m['avgLeadDays']:g}"
        parts.append(T["lead"].format(v=lead.replace(".", ",") if lang == "fr" else lead) + (T["best"] if best("avgLeadDays") else ""))
    if m["onTimeRate"] is not None:
        parts.append(T["ontime"].format(v=round(m["onTimeRate"] * 100)))
    if m["conformityRate"] is not None:
        parts.append(T["conf"].format(v=round(m["conformityRate"] * 100)))
    parts.append(T["orders"].format(v=m["orders"], m=months))
    return ", ".join(parts) + "."


# ---------------------------------------------------------------- AI (Gemini)

class AIError(Exception):
    pass


def call_ai(prompt, timeout=40):
    """One JSON-mode call to the configured AI (Gemini). Returns the parsed JSON."""
    c = _ai_config()
    key, model = c["apiKey"], c["model"]
    if not key:
        raise AIError("not configured")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError) as e:
        raise AIError(str(e)) from e


def ai_match(unmatched, catalog):
    """{line: product code} for free-text lines; the AI only picks codes from the catalogue."""
    prompt = (
        "You match purchase requisition lines to products of a purchase history.\n"
        "For each line, return the code of the product that is the SAME item (same material, alloy, "
        "dimensions and packaging), or null when no product is the same item. Never invent codes.\n"
        'Answer JSON: {"matches": [{"line": <line>, "productCode": <code or null>}]}\n\n'
        f"Products:\n{json.dumps(catalog, ensure_ascii=False)}\n\n"
        f"Lines:\n{json.dumps(unmatched, ensure_ascii=False)}"
    )
    res = call_ai(prompt)
    codes = {c["code"] for c in catalog}
    out = {}
    for mt in res.get("matches", []) if isinstance(res, dict) else []:
        code = mt.get("productCode")
        if code in codes:
            out[str(mt.get("line"))] = code
    return out


def ai_rank(items, settings, lang):
    """{line: [{cCode, score, reason}]} — the AI ranks the candidates of each item and explains why."""
    language = "French" if lang == "fr" else "English"
    prompt = (
        "You are the purchasing assistant of an ERP. For each requisition item, rank the candidate "
        "suppliers to choose the best one, using the metrics (computed from the purchase history), the "
        "criteria weights (percent) and the company instructions. Scores are 0-100. Keep the facts exact: "
        "quote only numbers present in the metrics. Write each reason in "
        f"{language}, one or two short sentences, saying why this supplier is (or is not) the best choice "
        "compared to the others.\n"
        f"Weights: {json.dumps(settings['weights'])}\n"
        f"Company instructions: {settings['instructions'] or '(none)'}\n"
        'Answer JSON: {"items": [{"line": <line>, "ranking": [{"cCode": <code>, "score": <0-100>, "reason": <text>}]}]}\n\n'
        f"Items:\n{json.dumps(items, ensure_ascii=False)}"
    )
    res = call_ai(prompt)
    out = {}
    for it in res.get("items", []) if isinstance(res, dict) else []:
        out[str(it.get("line"))] = it.get("ranking") or []
    return out


# ---------------------------------------------------------------- main entry

def best_suppliers(ns, req, settings=None, today=None):
    """Answer of getBestSupplier.p for a requisition payload (see SkyAI Offer workflow)."""
    s = settings or get_settings()
    lang = "fr" if str(req.get("lang", "fr")).lower().startswith("fr") else "en"
    months = s["historyMonths"]
    history = build_history(ns, months, today)
    known = {sup["cCode"]: sup for sup in ns["supplier_terms_data"]}
    items = [it for it in (req.get("items") or []) if isinstance(it, dict)]
    use_ai = s["useAI"] and ai_status()["configured"]
    engine = "rules"
    notes = []

    # 1. product of each line: exact code, else best description match
    matched = {}
    unmatched = []
    for i, it in enumerate(items, 1):
        line = str(it.get("line") or i)
        it["_line"] = line
        code = str(it.get("productCode") or "").strip()
        if code in history:
            matched[line] = code
            continue
        desc = str(it.get("description") or "")
        best = max(((match_score(desc, p["desc"]), c) for c, p in history.items()), default=(0, None))
        if best[0] >= MATCH_THRESHOLD:
            matched[line] = best[1]
        unmatched.append({"line": line, "description": desc, "productCode": code})
    if use_ai and unmatched:
        catalog = [{"code": c, "description": p["desc"]} for c, p in sorted(history.items())]
        try:
            for line, code in ai_match(unmatched, catalog).items():
                matched[line] = code
            engine = "gemini"
        except AIError as e:
            notes.append(f"AI match failed: {e}")
            logger.warning("Supplier selection: AI match failed (%s); keyword match kept", e)

    # 2-3. metrics and rule scores
    result_items, ai_input = [], []
    for it in items:
        line = it["_line"]
        code = matched.get(line)
        entry = {"line": int(line) if line.isdigit() else line, "description": it.get("description", ""),
                 "quantity": it.get("quantity"), "unit": it.get("unit", ""),
                 "matchedProduct": {"code": code, "desc": history[code]["desc"]} if code else None,
                 "decision": "none", "candidates": []}
        if code:
            metrics = {sup: m for sup, m in supplier_metrics(history[code]["lines"]).items()
                       if m["orders"] >= s["minOrders"] and sup in known}
            scores = rule_scores(metrics, s["weights"])
            for sup, m in metrics.items():
                entry["candidates"].append({
                    "cCode": sup, "cName": known[sup].get("cName") or m["name"], "score": scores[sup],
                    "reason": rule_reason(m, scores[sup], metrics, months, lang),
                    "metrics": {k: v for k, v in m.items() if k != "name"}})
            if entry["candidates"]:
                ai_input.append({"line": line, "product": history[code]["desc"], "quantity": it.get("quantity"),
                                 "candidates": [{"cCode": c["cCode"], "name": c["cName"], "ruleScore": c["score"],
                                                 **c["metrics"]} for c in entry["candidates"]]})
        result_items.append(entry)

    # 4. AI ranking and reasons
    if use_ai and ai_input:
        try:
            ranking = ai_rank(ai_input, s, lang)
            for entry in result_items:
                by_code = {c["cCode"]: c for c in entry["candidates"]}
                ranked = ranking.get(str(entry["line"])) or []
                if not by_code or {r.get("cCode") for r in ranked} != set(by_code):
                    continue  # AI answer incomplete for this item: rules kept
                for r in ranked:
                    c = by_code[r["cCode"]]
                    c["score"] = _int(r.get("score"), c["score"], 0, 100)
                    c["reason"] = str(r.get("reason") or c["reason"])
                    c["source"] = "gemini"
            engine = "gemini"
        except AIError as e:
            notes.append(f"AI ranking failed: {e}")
            logger.warning("Supplier selection: AI ranking failed (%s); rule scores kept", e)

    # ranking, tie, decision
    for entry in result_items:
        cands = sorted(entry["candidates"], key=lambda c: (-c["score"], c["metrics"]["avgUnitPrice"]))
        cands = cands[: s["maxCandidates"]]
        for rank, c in enumerate(cands, 1):
            c["rank"] = rank
            c["recommended"] = rank == 1
            c.setdefault("source", "rules")
        entry["candidates"] = cands
        if not cands:
            T = _TXT[lang]
            entry["decision"] = "none"
            entry["reason"] = (T["none"] if entry["matchedProduct"] else T["nomatch"]).format(m=months)
        else:
            tied = [c for c in cands if c["score"] >= cands[0]["score"] - s["tieMargin"]]
            entry["decision"] = "multiple" if len(tied) > 1 else "single"
            for c in cands:
                c["tied"] = len(tied) > 1 and c in tied

    return {
        "status": "ok",
        "requisitionNumber": req.get("requisitionNumber", ""),
        "engine": engine,
        "criteria": s["weights"],
        "settings": {k: s[k] for k in ("historyMonths", "minOrders", "tieMargin", "maxCandidates")},
        "items": result_items,
        **({"notes": notes} if notes else {}),
    }
