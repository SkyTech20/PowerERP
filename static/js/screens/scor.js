/* PowerERP: Reports > Supply chain indicators (step 7 of the SCOR / ISO plan). The figures of a period, grouped by
   the SCOR performance attributes (reliability, responsiveness, cost, assets), then the lots, the stock by product,
   the nonconformances and the deviations behind them. Read only. */
import { $, $$, api, enc, esc, fmtDateTime, fmtInt, lang, money, t } from "../core.js";
import { decorateScreen, helpButtonOf } from "../helpui.js";
import { dl, qtyFmt } from "../resources/inventory.js";
import { lotBadge } from "../resources/quality.js";
import { canOpen } from "../router.js";
import { pageHead } from "../views.js";

const SCREEN = "rep.scor";
const GROUPS = ["reliability", "responsiveness", "cost", "assets"];
const PRESETS = ["30", "90", "365", "year", "custom"];
const HORIZONS = ["7", "14", "30", "60", "90"];
// the screen behind each indicator (opened when the user may)
const LINKS = {
  perfect_order: "/sales/invoices", prod_on_time: "/prod/orders", prod_yield: "/prod/orders", supplier_fill: "/receptions",
  supplier_quality: "/qa/nonconformances", steps_first_time: "/prod/orders", prod_cycle: "/prod/orders", nc_close_days: "/qa/nonconformances",
  cost_variance: "/prod/orders", gross_margin: "/sales/invoices", inventory_value: "/inv/valuation", inventory_turns: "/inv/valuation",
  days_supply: "/inv/valuation", held_value: "/qa/lots", expiring_value: "/inv/stock",
};
const nf = (digits) => new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { maximumFractionDigits: digits, minimumFractionDigits: digits });
const iso = (d) => d.toISOString().slice(0, 10);
const daysAgo = (n) => { const d = new Date(); d.setDate(d.getDate() - n + 1); return iso(d); };

export function fmtKpi(k) {
  if (k.value === null || k.value === undefined) return "—";
  if (k.unit === "pct") return `${nf(1).format(k.value * 100)} %`;
  if (k.unit === "days") return `${nf(1).format(k.value)} ${t("rep.k.daysUnit")}`;
  if (k.unit === "ratio") return `${nf(1).format(k.value)}×`;
  return money(k.value);
}

// What the figure is made of ("12 of 14 invoices", "no data in the period")
export function kpiMeta(k) {
  const n = (v) => fmtInt(Math.round(Number(v) || 0));
  const q = (v) => nf(2).format(Number(v) || 0);
  switch (k.key) {
    case "perfect_order": case "prod_on_time": case "supplier_quality": case "steps_first_time":
      return k.den ? t(`rep.k.${k.key}.meta`, { n: n(k.num), of: n(k.den) }) : t("rep.k.noData");
    case "prod_yield": case "supplier_fill":
      return k.den ? t(`rep.k.${k.key}.meta`, { n: q(k.num), of: q(k.den) }) : t("rep.k.noData");
    case "prod_cycle": case "nc_close_days":
      return k.den ? t(`rep.k.${k.key}.meta`, { n: n(k.den) }) : t("rep.k.noData");
    case "cost_variance": case "gross_margin":
      return k.den ? t(`rep.k.${k.key}.meta`, { n: money(k.num), of: money(k.den) }) : t("rep.k.noData");
    case "inventory_turns":
      return k.den ? t("rep.k.inventory_turns.meta", { n: money(k.num) }) : t("rep.k.noData");
    case "days_supply":
      return k.den ? t("rep.k.days_supply.meta", { n: money(k.den) }) : t("rep.k.noUse");
    case "held_value": case "expiring_value":
      return t(`rep.k.${k.key}.meta`, { n: n(k.num) });
    default:
      return t(`rep.k.${k.key}.meta`);
  }
}

export function scorView() {
  const st = { preset: "90", from: daysAgo(90), to: iso(new Date()), horizon: "30" };
  let data = null;
  let error = "";
  const query = () => `from=${enc(st.from)}&to=${enc(st.to)}&horizon=${enc(st.horizon)}`;
  return {
    async load() {
      try { data = await api("kpi/scor?" + query()); error = ""; } catch (e) {
        error = t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic");
        if (!data) throw e;
      }
    },
    render() {
      const opt = (v, l, cur) => `<option value="${esc(v)}" ${v === cur ? "selected" : ""}>${esc(l)}</option>`;
      const card = (k) => {
        const link = LINKS[k.key] && canOpen(LINKS[k.key]) ? LINKS[k.key] : "";
        const inner = `<div class="label">${esc(t("rep.k." + k.key))}</div><div class="value ${k.value === null ? "muted" : ""}">${esc(fmtKpi(k))}</div>
          <div class="meta">${esc(kpiMeta(k))}</div><div class="scor-what">${esc(t("rep.k." + k.key + ".what"))}</div>`;
        return link ? `<a class="card kpi scor-kpi" href="#${link}" data-kpi="${esc(k.key)}">${inner}</a>`
          : `<div class="card kpi scor-kpi" data-kpi="${esc(k.key)}">${inner}</div>`;
      };
      const groups = GROUPS.map((g) => `<section class="scor-group"><h2>${esc(t("rep.g." + g))} <span class="muted">${esc(t("rep.g." + g + ".help"))}</span></h2>
        <div class="scor-kpis">${data[g].map(card).join("")}</div></section>`).join("");
      const p = data.period;
      $("#view").innerHTML = pageHead(t("rep.scor.title"), t("rep.scor.subtitle"), helpButtonOf(SCREEN)) + `
        <div class="card"><div class="toolbar scor-filters">
          <label>${esc(t("rep.period"))} <select id="scPreset" data-help-f="period">${PRESETS.map((v) => opt(v, t("rep.preset." + v), st.preset)).join("")}</select></label>
          <label>${esc(t("rep.from"))} <input type="date" id="scFrom" data-help-f="from" value="${esc(st.from)}"></label>
          <label>${esc(t("rep.to"))} <input type="date" id="scTo" data-help-f="to" value="${esc(st.to)}"></label>
          <label>${esc(t("rep.horizon"))} <select id="scHorizon" data-help-f="horizon">${HORIZONS.map((v) => opt(v, t("rep.horizon.days", { n: v }), st.horizon)).join("")}</select></label>
          <span class="count">${esc(t("rep.periodDays", { n: fmtInt(p.days) }))}</span></div>
          ${error ? `<div class="alert error" style="margin:0 16px 12px">${esc(error)}</div>` : ""}</div>
        ${groups}
        <div class="scor-cols">${lotsCard(data, st)}${ncCard(data)}</div>
        ${productsCard(data)}
        ${deviationsCard(data)}
        <p class="help">${esc(t("rep.scor.note"))}</p>`;
      decorateScreen(SCREEN);
      this.bind();
    },
    bind() {
      const reload = async () => { await this.load(); this.render(); };
      $("#scPreset").addEventListener("change", async (e) => {
        st.preset = e.target.value;
        const today = iso(new Date());
        if (st.preset === "year") Object.assign(st, { from: today.slice(0, 4) + "-01-01", to: today });
        else if (st.preset !== "custom") Object.assign(st, { from: daysAgo(Number(st.preset)), to: today });
        if (st.preset !== "custom") await reload(); else this.render();
      });
      const date = (id, f) => $(id).addEventListener("change", async (e) => {
        if (!e.target.value) return;
        st[f] = e.target.value;
        st.preset = "custom";
        await reload();
      });
      date("#scFrom", "from"); date("#scTo", "to");
      $("#scHorizon").addEventListener("change", async (e) => { st.horizon = e.target.value; await reload(); });
      $$("tr[data-href]").forEach((tr) => tr.addEventListener("click", () => { location.hash = tr.dataset.href; }));
    },
  };
}

const empty = (key) => `<div class="empty">${esc(t(key))}</div>`;
const trace = (r) => `/prod/traceability/${enc(r.cProduct)}/${enc(r.cLot)}`;
const rowLink = (path) => (canOpen(path) ? ` class="clickable" data-href="#${esc(path)}"` : "");

// The lots to watch: those that expire within the horizon (or already expired), and those held back by quality
function lotsCard(data, st) {
  const { expiring, held } = data.lots;
  const left = (r) => (r.iDaysLeft < 0 ? `<span class="badge no">${esc(t("rep.lots.expired"))}</span>`
    : `<span class="badge ${r.iDaysLeft <= 7 ? "no" : "warn"}">${esc(t("rep.lots.daysLeft", { n: fmtInt(r.iDaysLeft) }))}</span>`);
  const table = (rows, extra) => `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("qa.lots.product"))}</th><th>${esc(t("qa.lots.lot"))}</th>
    <th>${esc(t(extra))}</th><th class="num">${esc(t("qa.lots.onHand"))}</th><th class="num">${esc(t("rep.value"))}</th></tr></thead><tbody>
    ${rows.map((r) => `<tr${rowLink(trace(r))}><td><b>${esc(r.cProduct)}</b><div class="muted qa-small">${esc(dl(r, "cDesc"))}</div></td><td>${esc(r.cLot)}</td>
      <td>${extra === "rep.lots.expiry" ? `${esc(r.dExpiry)} ${left(r)}` : lotBadge(r.cStatus)}</td>
      <td class="num">${esc(qtyFmt(r.dQty))} ${esc(r.cUOM)}</td><td class="num">${esc(money(r.dValue))}</td></tr>`).join("")}</tbody></table></div>`;
  return `<div class="card"><div class="card-head"><h2>${esc(t("rep.lots.title"))}</h2><span class="help muted">${esc(t("rep.lots.help"))}</span></div><div class="card-body">
    <h3>${esc(t("rep.lots.expiring", { n: st.horizon }))}</h3>${expiring.length ? table(expiring, "rep.lots.expiry") : empty("rep.lots.noneExpiring")}
    <h3 style="margin-top:16px">${esc(t("rep.lots.held"))}</h3>${held.length ? table(held, "qa.lots.status") : empty("rep.lots.noneHeld")}
  </div></div>`;
}

// The nonconformances found in the period, by where they were found and how serious they are
function ncCard(data) {
  const nc = data.nonconformances;
  const bars = (counts, prefix, keys) => {
    const max = Math.max(1, ...keys.map((k) => counts[k] || 0));
    return keys.map((k) => `<div class="scor-bar"><span>${esc(t(prefix + k))}</span><div><i style="width:${Math.round(((counts[k] || 0) / max) * 100)}%"></i></div><b>${esc(fmtInt(counts[k] || 0))}</b></div>`).join("");
  };
  const link = canOpen("/qa/nonconformances") ? `<a class="btn small" style="margin-left:auto" href="#/qa/nonconformances">${esc(t("menu.qa.nc"))} →</a>` : "";
  return `<div class="card"><div class="card-head"><h2>${esc(t("rep.nc.title"))}</h2>${link}</div><div class="card-body">
    <div class="scor-pair"><div><div class="value">${esc(fmtInt(nc.found))}</div><div class="muted">${esc(t("rep.nc.found"))}</div></div>
      <div><div class="value">${esc(fmtInt(nc.open))}</div><div class="muted">${esc(t("rep.nc.open"))}</div></div></div>
    ${nc.found ? `<h3>${esc(t("rep.nc.bySource"))}</h3>${bars(nc.bySource, "qa.nc.src.", ["reception", "production", "internal", "customer"])}
      <h3 style="margin-top:12px">${esc(t("rep.nc.bySeverity"))}</h3>${bars(nc.bySeverity, "qa.nc.sev.", ["critical", "major", "minor"])}` : empty("rep.nc.none")}
  </div></div>`;
}

// The stock by product: value, what was used in the period and the days it covers (the slow movers first)
function productsCard(data) {
  const pr = data.products;
  const rows = pr.rows.map((r) => `<tr${rowLink("/inv/items/" + enc(r.cProduct))}><td><b>${esc(r.cProduct)}</b><div class="muted qa-small">${esc(dl(r, "cDesc"))}</div></td>
    <td class="num">${esc(qtyFmt(r.dQty))} ${esc(r.cUOM)}</td><td class="num">${esc(money(r.dValue))}</td><td class="num">${esc(money(r.dUsed))}</td>
    <td class="num">${r.dDaysSupply === null ? `<span class="badge warn">${esc(t("rep.prod.slow"))}</span>` : esc(nf(0).format(r.dDaysSupply))}</td>
    <td>${esc(r.dLastOut || "—")}</td></tr>`).join("");
  return `<div class="card"><div class="card-head"><h2>${esc(t("rep.prod.title"))}</h2><span class="help muted">${esc(t("rep.prod.help", { n: fmtInt(pr.total), s: fmtInt(pr.slow) }))}</span></div>
    ${pr.rows.length ? `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("qa.lots.product"))}</th><th class="num">${esc(t("qa.lots.onHand"))}</th>
      <th class="num">${esc(t("rep.value"))}</th><th class="num">${esc(t("rep.prod.used"))}</th><th class="num">${esc(t("rep.prod.days"))}</th><th>${esc(t("rep.prod.lastOut"))}</th></tr></thead>
      <tbody>${rows}</tbody></table></div>` : empty("rep.prod.none")}</div>`;
}

// The values out of their limits recorded on the shop floor in the period
function deviationsCard(data) {
  const rows = data.deviations.map((d) => `<tr${rowLink("/prod/orders/" + d.iOrder)}><td>${esc(fmtDateTime(d.dAt))}</td><td>${esc(d.iOrder)} — ${esc(d.cProduct)}</td>
    <td>${esc(d.cStep)} ${esc(lang === "fr" ? d.cTitleFR || d.cTitleEN : d.cTitleEN || d.cTitleFR)}</td><td><b>${esc(d.cValue)} ${esc(d.cUOM)}</b> <span class="muted">${esc(t("mfg.st.r." + d.cReason))}</span></td>
    <td><span class="badge ${d.cAction === "warn" ? "warn" : "no"}">${esc(t("mfg.st.a." + d.cAction))}</span></td><td>${esc(d.cComment)}</td><td>${esc(d.cUser)}</td></tr>`).join("");
  return `<div class="card"><div class="card-head"><h2>${esc(t("rep.dev.title"))}</h2><span class="help muted">${esc(t("rep.dev.help"))}</span></div>
    ${data.deviations.length ? `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("mfg.ap.when"))}</th><th>${esc(t("prod.ord.one"))}</th><th>${esc(t("rep.dev.step"))}</th>
      <th>${esc(t("rep.dev.value"))}</th><th>${esc(t("rep.dev.action"))}</th><th>${esc(t("prod.st.action"))}</th><th>${esc(t("mfg.ap.who"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`
      : empty("rep.dev.none")}</div>`;
}
