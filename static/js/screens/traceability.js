/* PowerERP: Production > Lots and traceability. Where a lot comes from, where it went, and what a recall must reach. */
import { $, api, enc, esc, fmtInt, lang, t, toast } from "../core.js";
import { dl, qtyFmt } from "../resources/inventory.js";
import { lotBadge } from "../resources/quality.js";
import { canOpen } from "../router.js";
import { can } from "../state.js";
import { decorateScreen, helpButtonOf } from "../helpui.js";
import { pageHead } from "../views.js";

const SCREEN = "prod.traceability";
const tOr = (k, d) => (t(k) !== k ? t(k) : d);
// A sales movement carries the invoice (or credit note) number: say so rather than "Sales order"
const docLabel = (m) => (m.cDocType === "SO" ? t(m.cType === "ADJ" ? "prod.tr.k.credit" : "prod.tr.k.invoice") : tOr("o.doc." + m.cDocType, m.cDocType));
const qty = (v, u) => `${esc(qtyFmt(v))} ${esc(u || "")}`.trim();
const link = (path, label) => (canOpen(path) ? `<a href="#${path}">${esc(label)}</a>` : esc(label));
const orderLink = (no) => link(`/prod/orders/${enc(no)}`, `${t("prod.tr.order")} ${no}`);
const mvLink = (no) => (no ? link(`/inv/movements/${enc(no)}`, String(no)) : "");
const status = (s) => `<span class="badge">${esc(t("prod.ord.status." + s))}</span>`;
const lotLabel = (n) => `<b>${esc(n.cProduct)}</b> ${esc(dl(n, "cDesc"))} · ${esc(t("prod.tr.lot"))} <b>${esc(n.cLot)}</b>${n.dExpiry ? ` · ${esc(t("prod.tr.expiry"))} ${esc(n.dExpiry)}` : ""}`;
const table = (head, rows, empty) => (rows.length
  ? `<div class="table-wrap"><table class="grid"><thead><tr>${head.map(([l, c]) => `<th class="${c || ""}">${esc(t(l))}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`
  : `<p class="help">${esc(t(empty))}</p>`);

// One step back, then on: the receptions (supplier, supplier lot, PO), the orders that made it and the lots they used
function originHtml(n) {
  const src = n.sources.map((s) => {
    if (s.cKind === "reception") {
      const sup = [s.cSupplier, s.cSupplierName].filter(Boolean).join(" — ");
      return `<li class="src">${esc(t("prod.tr.received"))} ${esc(s.dDate)} · ${link(`/receptions/${enc(s.cDocNo)}`, `${t("prod.tr.reception")} ${s.cDocNo}`)}
        ${sup ? ` · ${esc(t("prod.tr.supplier"))} <b>${esc(sup)}</b>` : ""}${s.cSupplierLot ? ` · ${esc(t("prod.tr.supplierLot"))} <b>${esc(s.cSupplierLot)}</b>` : ""}
        ${s.cPO ? ` · ${esc(t("prod.tr.po"))} ${esc(s.cPO)}` : ""} · ${qty(s.dQty, n.cUOM)}</li>`;
    }
    if (s.cKind === "production") return `<li class="src">${esc(t("prod.tr.made"))} ${esc(s.dDate)} · ${orderLink(s.iOrder)} ${status(s.cStatus)} · ${qty(s.dQty, n.cUOM)}</li>`;
    return `<li class="src">${esc(t("prod.tr.otherIn"))} ${esc(s.dDate)} · ${esc(tOr("o.doc." + s.cDocType, s.cDocType))} ${esc(s.cDocNo || "")} · ${qty(s.dQty, n.cUOM)}</li>`;
  }).join("");
  const inputs = n.inputs.map((c) => `<li>${esc(t("prod.tr.usedIn", { q: `${qtyFmt(c.dQtyUsed)} ${c.cUOM}` }))} ${orderLink(c.iOrder)}: ${originHtml(c)}</li>`).join("");
  const none = !n.sources.length && !n.inputs.length ? `<li class="src muted">${esc(t("prod.tr.noOrigin"))}</li>` : "";
  return `<div class="tr-node">${lotLabel(n)}${n.lLoop ? ` <span class="badge no">${esc(t("prod.tr.loop"))}</span>` : ""}</div><ul class="tr-tree">${src}${none}${inputs}</ul>`;
}

// One step forward, then on: the orders that used the lot and the lots they made
function usesHtml(n) {
  const orders = n.orders.map((o) => {
    const outs = o.outputs.map((out) => `<li>${esc(t("prod.tr.madeQty", { q: `${qtyFmt(out.dQtyMade)} ${out.cUOM}` }))} ${usesHtml(out)}</li>`).join("");
    return `<li>${orderLink(o.iOrder)} ${status(o.cStatus)} ${esc(t("prod.tr.used", { q: `${qtyFmt(o.dQtyUsed)} ${n.cUOM}` }))}
      ${outs ? `<ul class="tr-tree">${outs}</ul>` : `<span class="muted"> · ${esc(t("prod.tr.nothingMade"))}</span>`}</li>`;
  }).join("");
  return `<div class="tr-node">${lotLabel(n)}</div>${orders ? `<ul class="tr-tree">${orders}</ul>` : ""}`;
}

export function traceabilityView(product0, lot0) {
  let products = [];
  let lots = [];
  let product = product0 || "";
  let lot = lot0 || "";
  let data = null;
  let error = "";
  const trace = async () => {
    data = null;
    error = "";
    if (!product || !lot) return;
    try {
      data = await api(`traceability?product=${enc(product)}&lot=${enc(lot)}`);
    } catch (e) { error = t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic"); }
  };
  const loadLots = async () => { lots = product ? await api(`lookups/trace_lots?all=1&product=${enc(product)}`) : []; };
  return {
    async load() {
      products = await api("lookups/traced_products?all=1&lang=" + lang);
      await loadLots();
      await trace();
    },
    render() {
      const exportUrl = data ? `api/traceability/export?product=${enc(product)}&lot=${enc(lot)}&lang=${enc(lang)}` : "";
      const actions = helpButtonOf(SCREEN) + (data ? `<a class="btn" id="trExport" href="${exportUrl}" download>${esc(t("prod.tr.export"))}</a>` : "");
      $("#view").innerHTML = pageHead(t("prod.tr.title"), t("prod.tr.subtitle"), actions) + `
        <div class="card"><div class="toolbar">
          <label class="tr-pick">${esc(t("prod.tr.product"))} <select id="trProduct" data-help-f="product" style="width:auto;max-width:100%"><option value="">${esc(t("prod.tr.pick"))}</option>
            ${products.map((p) => `<option value="${esc(p.code)}" ${p.code === product ? "selected" : ""}>${esc(p.code)}${dl(p, "cDesc") || p.label ? " — " + esc(dl(p, "cDesc") || p.label) : ""}</option>`).join("")}</select></label>
          <label class="tr-pick">${esc(t("prod.tr.lot"))} <select id="trLot" data-help-f="lot" style="width:auto;max-width:100%" ${product ? "" : "disabled"}><option value="">${esc(t("prod.tr.pick"))}</option>
            ${lots.map((l) => `<option value="${esc(l.code)}" ${l.code === lot ? "selected" : ""}>${esc(l.code)}${l.label ? " — " + esc(l.label) : ""}</option>`).join("")}</select></label>
          <span class="help muted">${esc(t("prod.tr.help"))}</span></div></div>
        ${error ? `<div class="alert error">${esc(error)}</div>` : ""}
        ${data ? this.result(data) : `<div class="card"><div class="empty">${esc(t(products.length ? "prod.tr.start" : "prod.tr.noLots"))}</div></div>`}`;
      decorateScreen(SCREEN);
      $("#trProduct").addEventListener("change", async (e) => {
        product = e.target.value; lot = ""; data = null; error = "";
        await loadLots();
        if (lots.length === 1) { lot = lots[0].code; await trace(); }
        this.go();
      });
      $("#trLot").addEventListener("change", async (e) => { lot = e.target.value; await trace(); this.go(); });
      if ($("#trExport")) $("#trExport").addEventListener("click", () => toast(t("prod.tr.exporting"), "success"));
      if ($("#trHold")) {
        const hold = async () => {
          const reason = $("#trHoldReason").value.trim();
          if (!reason) { toast(t("qa.lots.reason.required"), "error"); $("#trHoldReason").focus(); return; }
          const lots = data.recall.lots.filter((n) => n.cStatus === "released").map((n) => ({ cProduct: n.cProduct, cLot: n.cLot }));
          try {
            const res = await api("lot-status/hold", { method: "POST", body: { lots, cReason: reason } });
            toast(t("prod.tr.held", { n: res.changed.length }), "success");
            await trace();
            this.render();
          } catch (e) { toast(t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic"), "error"); }
        };
        $("#trHold").addEventListener("click", hold);
        $("#trHoldReason").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); hold(); } });
      }
    },
    go() {
      const path = "#/prod/traceability" + (product && lot ? `/${enc(product)}/${enc(lot)}` : "");
      if (location.hash !== path) history.replaceState(null, "", path);
      this.render();
    },
    result(d) {
      const r = d.recall;
      const onHand = r.stock.length;
      const customers = r.iCustomers;
      const kpi = (label, value, meta) => `<div class="card kpi"><div class="label">${esc(t(label))}</div><div class="value">${esc(fmtInt(value))}</div><div class="meta">${esc(t(meta))}</div></div>`;
      const alert = customers || onHand || r.orders.length
        ? `<div class="alert warn"><b>${esc(t("prod.tr.recallTitle"))}</b> ${esc(t("prod.tr.recallText", { lots: r.lots.length, c: customers, s: onHand, o: r.orders.length }))}</div>`
        : `<div class="alert success">${esc(t("prod.tr.recallNone"))}</div>`;
      const lotsReached = r.lots.length > 1 ? `<p class="help">${esc(t("prod.tr.lotsReached"))} ${r.lots.map((n) => `<b>${esc(n.cProduct)}</b> ${esc(n.cLot)} ${lotBadge(n.cStatus)}`).join(", ")}</p>` : "";
      // quality: the status of the lot, and holding every lot the recall reaches that is still released
      const free = r.lots.filter((n) => n.cStatus === "released").length;
      const lotsLink = can("qa.lots") ? ` · <a href="#/qa/lots">${esc(t("prod.tr.lotStatusLink"))}</a>` : "";
      const holdBox = free && can("qa.lots", "change")
        ? `<div class="tr-hold"><label>${esc(t("prod.tr.holdReason"))} <input type="text" id="trHoldReason" data-help-f="holdReason" maxlength="300" placeholder="${esc(t("prod.tr.holdReason.ph"))}"></label>
          <button type="button" class="btn primary" id="trHold">${esc(t("prod.tr.hold", { n: free }))}</button></div>`
        : "";
      const statusCard = `<div class="card"><div class="card-body tr-status"><span>${esc(t("prod.tr.lotStatus"))} ${lotBadge(d.cStatus)}${lotsLink}</span>
        <span class="help muted">${esc(t(free ? "prod.tr.hold.help" : "prod.tr.allHeld"))}</span>${holdBox}</div></div>`;
      const custRows = r.customers.map((c) => `<tr><td><b>${esc(c.cCustomer)}</b> ${esc(c.cCustomerName)}</td><td><span class="badge ${c.cType === "credit" ? "no" : ""}">${esc(t("prod.tr.k." + c.cType))}</span> ${esc(c.cInvoiceNo)}</td>
        <td>${esc(c.dDate)}</td><td>${esc(c.cProduct)} ${esc(dl(c, "cDesc"))}</td><td>${esc(c.cLot)}</td><td class="num">${qty(c.dQty, c.cUOM)}</td></tr>`);
      const stockRows = r.stock.map((s) => `<tr><td>${esc(s.cProduct)} ${esc(dl(s, "cDesc"))}</td><td>${esc(s.cLot)} ${lotBadge(s.cStatus)}</td><td>${esc(s.dExpiry)}</td><td>${esc(s.cWarehouse)}</td><td>${esc(s.cLocation)}</td><td class="num">${qty(s.dQty, s.cUOM)}</td></tr>`);
      const orderRows = r.orders.map((o) => `<tr><td>${orderLink(o.iOrder)}</td><td>${status(o.cStatus)}</td><td>${esc(o.cProduct)}</td></tr>`);
      const moveRows = d.movements.map((m) => `<tr><td>${mvLink(m.iNo)}</td><td>${esc(m.dDate)}</td><td><span class="badge mv-${esc(m.cType)}">${esc(tOr("o.mv." + m.cType, m.cType))}</span></td>
        <td>${esc(docLabel(m))} ${esc(m.cDocNo)}</td><td>${esc(m.cWarehouse)}</td><td>${esc(m.cLocation)}</td>
        <td class="num">${esc(qtyFmt(m.dQty))}</td><td>${esc(m.cReason)}</td><td>${esc(m.cUser)}</td></tr>`);
      const card = (title, help, body) => `<div class="card"><div class="card-head"><h2>${esc(t(title))}</h2><span class="help muted">${esc(t(help))}</span></div><div class="card-body">${body}</div></div>`;
      return `<div class="kpis tr-kpis">${kpi("prod.tr.kpi.lots", r.lots.length, "prod.tr.kpi.lots.meta")}${kpi("prod.tr.kpi.customers", customers, "prod.tr.kpi.customers.meta")}
          ${kpi("prod.tr.kpi.stock", onHand, "prod.tr.kpi.stock.meta")}${kpi("prod.tr.kpi.orders", r.orders.length, "prod.tr.kpi.orders.meta")}</div>
        ${alert}
        ${statusCard}
        ${card("prod.tr.origin", "prod.tr.origin.help", originHtml(d.origin))}
        ${card("prod.tr.uses", "prod.tr.uses.help", d.uses.orders.length ? usesHtml(d.uses) : `<p class="help">${esc(t("prod.tr.noUses"))}</p>`)}
        ${card("prod.tr.customers", "prod.tr.customers.help", lotsReached + table([["prod.tr.customer"], ["prod.tr.document"], ["prod.tr.date"], ["prod.tr.product"], ["prod.tr.lot"], ["prod.tr.qty", "num"]], custRows, "prod.tr.noCustomers"))}
        ${card("prod.tr.stock", "prod.tr.stock.help", table([["prod.tr.product"], ["prod.tr.lot"], ["prod.tr.expiry"], ["prod.tr.warehouse"], ["prod.tr.location"], ["prod.tr.qty", "num"]], stockRows, "prod.tr.noStock"))}
        ${r.orders.length ? card("prod.tr.orders", "prod.tr.orders.help", table([["prod.tr.orderNo"], ["prod.tr.status"], ["prod.tr.product"]], orderRows, "")) : ""}
        ${card("prod.tr.moves", "prod.tr.moves.help", table([["prod.tr.movement"], ["prod.tr.date"], ["prod.tr.type"], ["prod.tr.document"], ["prod.tr.warehouse"], ["prod.tr.location"], ["prod.tr.qty", "num"], ["prod.tr.reason"], ["prod.tr.user"]], moveRows, ""))}`;
    },
  };
}
