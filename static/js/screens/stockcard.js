/* PowerERP: Inventory > Stock on hand > stock card. The movements of one stock line (product, warehouse, location,
   lot, serial): what came in, what went out, the balance after each one, and the document behind each movement. */
import { $, api, enc, esc, money, num, t } from "../core.js";
import { decorateScreen, helpButtonOf } from "../helpui.js";
import { STOCK_NONE, dl, productLink, qtyFmt } from "../resources/inventory.js";
import { canOpen } from "../router.js";
import { pageHead } from "../views.js";

const SCREEN = "inv.stock";
const unpart = (v) => (v === STOCK_NONE || v == null ? "" : v);

const link = (path, label) => (path && canOpen(path) ? `<a href="#${path}">${esc(label)}</a>` : esc(label));

// What happened, in the words of the user: "Reception", "Used by a production order", "Invoice"...
export function moveKind(m) {
  const doc = m.cDocType;
  if (m.cType === "TRF") return m.dQtyIn ? t("stc.k.trfIn", { w: m.cFrom }) : t("stc.k.trfOut", { w: m.cTo });
  if (doc === "REC" && m.cType === "IN") return t("stc.k.reception");
  if (doc === "PROD") return t(m.cType === "IN" ? "stc.k.made" : m.cType === "ADJ" ? "stc.k.returned" : "stc.k.used");
  if (doc === "SO") return t(m.cType === "ADJ" ? "stc.k.credit" : "stc.k.invoice");
  if (doc === "CNT" || m.cType === "CNT") return t("stc.k.count");
  return t("o.mv." + m.cType) + (doc === "MAN" || !doc ? ` (${t("o.doc.MAN")})` : "");
}

// The document behind a movement, and where to open it
export function docOf(m) {
  const no = m.cDocNo;
  switch (m.cDocType) {
    case "REC": return { label: `${t("stc.d.reception")} ${no}`, path: no ? `/receptions/${enc(no)}` : "" };
    case "PO": return { label: `${t("o.doc.PO")} ${no}`, path: no ? `/po/${enc(no)}` : "" };
    case "PROD": return { label: `${t("stc.d.order")} ${no}`, path: no ? `/prod/orders/${enc(no)}` : "" };
    case "CNT": return { label: `${t("stc.d.count")} ${no}`, path: no ? `/inv/counts/${enc(no)}` : "" };
    case "SO": return { label: `${t(m.cType === "ADJ" ? "stc.d.credit" : "stc.d.invoice")} ${no}`, path: m.iDocId !== "" && m.iDocId != null ? `/sales/invoices/${enc(m.iDocId)}` : "" };
    default: return { label: no ? `${t("o.doc." + (m.cDocType || "MAN"))} ${no}` : "", path: "" };
  }
}

export function stockCardView(product, warehouse, location, lot, serial) {
  const key = { product, warehouse, location: unpart(location), lot: unpart(lot), serial: unpart(serial) };
  const st = { from: "", to: "" };
  let data = null;
  const query = () => Object.entries({ ...key, ...st }).filter(([, v]) => v).map(([k, v]) => `${k}=${enc(v)}`).join("&");
  return {
    async load() { data = await api("inventory/stock/card?" + query()); },
    render() {
      const d = data;
      const u = d.cUOM || "";
      const q = (v) => (v === "" || v == null ? "" : esc(qtyFmt(v)));
      const place = [d.cWarehouse + (d.cWarehouseName ? " — " + d.cWarehouseName : ""), d.cLocation].filter(Boolean).join(" / ");
      const trace = d.cLot ? `/prod/traceability/${enc(d.cProduct)}/${enc(d.cLot)}` : "";
      const actions = [
        helpButtonOf(SCREEN),
        canOpen(productLink(d)) ? `<a class="btn" id="scProduct" href="#${productLink(d)}">${esc(t("stc.openProduct"))}</a>` : "",
        trace && canOpen(trace) ? `<a class="btn" id="scTrace" href="#${trace}">${esc(t("stc.trace"))}</a>` : "",
      ].join("");
      const crumbs = `<a href="#/inv/stock">${esc(t("stk.title"))}</a> /`;
      const fact = (l, v) => (v ? `<div><span class="muted">${esc(t(l))}</span> <b>${esc(v)}</b></div>` : "");
      const kpi = (l, v, meta) => `<div class="card kpi"><div class="label">${esc(t(l))}</div><div class="value">${q(v)} <small class="muted">${esc(u)}</small></div><div class="meta">${esc(t(meta))}</div></div>`;
      const rows = d.items.map((m) => {
        const doc = docOf(m);
        const mv = link(`/inv/movements/${m.iNo}`, t("stc.moveNo", { n: m.iNo }));
        return `<tr class="${num(m.dBalance) < 0 ? "sc-neg" : ""}"><td>${esc(m.dDate)}<div class="muted sc-small">${mv}</div></td><td><span class="badge mv-${esc(m.cType)}">${esc(moveKind(m))}</span></td>
          <td>${doc.label ? link(doc.path, doc.label) : `<span class="muted">—</span>`}</td><td class="wrap">${esc(m.cReason)}</td>
          <td class="num sc-in">${q(m.dQtyIn)}</td><td class="num sc-out">${m.dQtyOut ? "−" + q(m.dQtyOut) : ""}</td>
          <td class="num"><b>${q(m.dBalance)}</b>${m.dQtyReserved ? `<div class="muted sc-small">${esc(t("stc.reservedChange", { q: qtyFmt(m.dQtyReserved) }))}</div>` : ""}</td>
          <td class="num">${m.dQtyIn || m.dQtyOut ? esc(money(m.dUnitCost)) : ""}</td><td class="num">${m.dValue ? esc(money(m.dValue)) : ""}</td>
          <td>${esc(m.cUser)}</td></tr>`;
      });
      const opening = d.dFrom ? `<tr class="total-row"><td>${esc(d.dFrom)}</td><td colspan="5">${esc(t("stc.opening"))}</td><td class="num"><b>${q(d.dOpening)}</b></td><td colspan="3"></td></tr>` : "";
      const closing = `<tr class="total-row"><td>${esc(d.dTo || "")}</td><td colspan="5">${esc(t(d.dTo ? "stc.closingAt" : "stc.closing"))}</td><td class="num"><b>${q(d.dClosing)}</b> ${esc(u)}</td><td colspan="3"></td></tr>`;
      const head = ["stc.c.date", "stc.c.what", "stc.c.doc", "stc.c.reason", "stc.c.in", "stc.c.out", "stc.c.balance", "stc.c.unitCost", "stc.c.value", "stc.c.user"];
      const numCols = new Set(["stc.c.in", "stc.c.out", "stc.c.balance", "stc.c.unitCost", "stc.c.value"]);
      const table = rows.length || d.dFrom
        ? `<div class="table-wrap"><table class="grid sc-grid"><thead><tr>${head.map((h) => `<th class="${numCols.has(h) ? "num" : ""}">${esc(t(h))}</th>`).join("")}</tr></thead>
            <tbody>${opening}${rows.join("") || `<tr><td colspan="10" class="muted">${esc(t("stc.noneInPeriod"))}</td></tr>`}${closing}</tbody></table></div>`
        : `<div class="empty">${esc(t("stc.none"))}</div>`;
      $("#view").innerHTML = pageHead(`${d.cProduct} — ${dl(d, "cDesc")}`, t("stc.subtitle"), actions, crumbs) + `
        <div class="card"><div class="card-body sc-facts">
          ${fact("stc.where", place)}${fact("f.mv.cLot", d.cLot)}${fact("f.mv.cSerial", d.cSerial)}${fact("f.mv.dExpiry", d.dExpiry)}
        </div></div>
        <div class="kpis sc-kpis">${kpi("f.inv.dQtyOnHand", d.dQtyOnHand, "stc.kpi.onHand")}${kpi("f.inv.dQtyReserved", d.dQtyReserved, "stc.kpi.reserved")}${kpi("f.inv.dQtyAvailable", d.dQtyAvailable, "stc.kpi.available")}</div>
        <div class="card"><div class="card-head"><h2>${esc(t("stc.movements"))}</h2>
            <span class="help muted">${esc(t("stc.help"))}</span></div>
          <div class="toolbar">
            <label for="scFrom">${esc(t("stc.from"))}</label><input type="date" id="scFrom" data-help-f="card.from" value="${esc(st.from)}" style="width:auto">
            <label for="scTo">${esc(t("stc.to"))}</label><input type="date" id="scTo" data-help-f="card.to" value="${esc(st.to)}" style="width:auto">
            ${st.from || st.to ? `<button type="button" class="btn small" id="scAll">${esc(t("stc.allDates"))}</button>` : ""}
            <span class="count">${esc(t("stc.count", { n: d.items.length }))}</span>
          </div>${table}</div>`;
      decorateScreen(SCREEN);
      const reload = async () => { await this.load(); this.render(); };
      $("#scFrom").addEventListener("change", (e) => { st.from = e.target.value; reload(); });
      $("#scTo").addEventListener("change", (e) => { st.to = e.target.value; reload(); });
      if ($("#scAll")) $("#scAll").addEventListener("click", () => { st.from = ""; st.to = ""; reload(); });
    },
  };
}
