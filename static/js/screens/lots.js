/* PowerERP: Quality > Lot status. Which lots may go out (released) and which are held back, why, and by whom. */
import { $, $$, api, enc, esc, fmtDateTime, fmtInt, lang, t, toast } from "../core.js";
import { decorateScreen, helpButtonOf } from "../helpui.js";
import { dl, qtyFmt } from "../resources/inventory.js";
import { LOT_STATUSES, lotBadge } from "../resources/quality.js";
import { canOpen } from "../router.js";
import { can } from "../state.js";
import { pageHead } from "../views.js";

const SCREEN = "qa.lots";
const rowKey = (r) => `${r.cProduct}|${r.cLot}`;

export function lotsView() {
  const st = { status: "", product: "", q: "" };
  let data = null;
  let products = [];
  let open = { key: "", mode: "" }; // the row whose change form (mode "change") or history (mode "history") is open
  let history = [];
  let error = "";
  let pick = ""; // the new status chosen in the change form (kept when the reason is missing)
  const query = () => Object.entries(st).filter(([, v]) => v).map(([k, v]) => `${k}=${enc(v)}`).join("&");
  return {
    async load() {
      [data, products] = await Promise.all([api("lot-status?" + query()), api("lookups/lot_products?all=1&lang=" + lang)]);
    },
    render() {
      const mayChange = can(SCREEN, "change");
      const c = data.counts;
      const kpi = (s) => `<button type="button" class="card kpi qa-kpi ${st.status === s ? "on" : ""}" data-kpi="${s}"><div class="label">${lotBadge(s)}</div>
        <div class="value">${esc(fmtInt(c[s] || 0))}</div><div class="meta">${esc(t("qa.lots.kpi." + s))}</div></button>`;
      const opt = (v, l, cur) => `<option value="${esc(v)}" ${v === cur ? "selected" : ""}>${esc(l)}</option>`;
      const rows = data.items.map((r) => {
        const k = rowKey(r);
        const trace = `/prod/traceability/${enc(r.cProduct)}/${enc(r.cLot)}`;
        const by = r.dChanged ? `<div class="muted qa-small">${esc(r.cUser)} · ${esc(fmtDateTime(r.dChanged))}${r.iNC ? ` · ${link(`/qa/nonconformances/${r.iNC}`, `${t("qa.lots.nc")} ${r.iNC}`)}` : ""}</div>` : "";
        const buttons = [
          mayChange ? `<button type="button" class="btn small ${r.cStatus === "released" ? "" : "primary"}" data-change="${esc(k)}">${esc(t("qa.lots.change"))}</button>` : "",
          r.dChanged ? `<button type="button" class="btn small" data-history="${esc(k)}">${esc(t(open.key === k && open.mode === "history" ? "qa.lots.hideHistory" : "qa.lots.history"))}</button>` : "",
          canOpen(trace) ? `<a class="btn small" href="#${trace}">${esc(t("qa.lots.trace"))}</a>` : "",
        ].join("");
        const main = `<tr class="${r.cStatus === "released" ? "" : "qa-held"}"><td><b>${esc(r.cProduct)}</b><div class="muted qa-small">${esc(dl(r, "cDesc"))}</div></td>
          <td><b>${esc(r.cLot)}</b>${r.dExpiry ? `<div class="muted qa-small">${esc(t("qa.lots.expiry"))} ${esc(r.dExpiry)}</div>` : ""}</td>
          <td class="num">${esc(qtyFmt(r.dOnHand))} ${esc(r.cUOM)}<div class="muted qa-small">${esc(r.cWhere)}</div></td>
          <td>${lotBadge(r.cStatus)}</td><td class="qa-text qa-why">${esc(r.cReason)}${by}</td><td><div class="qa-actions">${buttons}</div></td></tr>`;
        if (open.key !== k) return main;
        if (open.mode === "history") {
          const items = history.map((h) => `<li>${esc(fmtDateTime(h.dAt))} · <b>${esc(h.cUser)}</b> · ${lotBadge(h.cFrom)} → ${lotBadge(h.cTo)} · ${esc(h.cReason)}</li>`).join("");
          return main + `<tr class="qa-detail"><td colspan="6"><ul class="qa-history">${items || `<li class="muted">${esc(t("qa.lots.noHistory"))}</li>`}</ul></td></tr>`;
        }
        const choices = LOT_STATUSES.filter((s) => s !== r.cStatus);
        return main + `<tr class="qa-detail"><td colspan="6"><div class="qa-change">
          <label>${esc(t("qa.lots.newStatus"))} <select id="qaNew" data-help-f="newStatus">${choices.map((s) => opt(s, t("qa.lot." + s), pick)).join("")}</select></label>
          <label class="qa-reason">${esc(t("qa.lots.reason"))} <input type="text" id="qaReason" data-help-f="reason" maxlength="300" placeholder="${esc(t("qa.lots.reason.ph"))}"></label>
          <button type="button" class="btn primary" id="qaSave">${esc(t("common.save"))}</button> <button type="button" class="btn" id="qaCancel">${esc(t("common.cancel"))}</button>
          <p class="help muted">${esc(t("qa.lots.change.help"))}</p>
          ${error ? `<div class="alert error">${esc(error)}</div>` : ""}</div></td></tr>`;
      }).join("");
      $("#view").innerHTML = pageHead(t("qa.lots.title"), t("qa.lots.subtitle"), helpButtonOf(SCREEN)) + `
        <div class="kpis qa-kpis">${["on_hold", "quarantine", "rejected", "released"].map(kpi).join("")}</div>
        <div class="card"><div class="toolbar qa-filters">
          <select id="qaStatus" data-help-f="status" aria-label="${esc(t("qa.lots.status"))}">${opt("", t("qa.lots.status") + ": " + t("common.all"), st.status)}${opt("blocked", t("qa.lots.blocked"), st.status)}${LOT_STATUSES.map((s) => opt(s, t("qa.lot." + s), st.status)).join("")}</select>
          <select id="qaProduct" data-help-f="product" aria-label="${esc(t("qa.lots.product"))}">${opt("", t("qa.lots.product") + ": " + t("common.all"), st.product)}${products.map((p) => opt(p.code, p.label ? `${p.code} — ${p.label}` : p.code, st.product)).join("")}</select>
          <input type="search" id="qaQ" data-help-f="search" placeholder="${esc(t("qa.lots.search"))}" value="${esc(st.q)}">
          <span class="count">${esc(t("common.records", { n: fmtInt(data.total) }))}</span></div>
          <div class="table-wrap">${data.items.length ? `<table class="grid"><thead><tr><th>${esc(t("qa.lots.product"))}</th><th>${esc(t("qa.lots.lot"))}</th>
            <th class="num">${esc(t("qa.lots.onHand"))}</th><th>${esc(t("qa.lots.status"))}</th><th>${esc(t("qa.lots.why"))}</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
            : `<div class="empty">${esc(t(st.status || st.product || st.q ? "qa.lots.noneFound" : "qa.lots.none"))}</div>`}</div></div>
        <p class="help">${esc(t("qa.lots.note"))}</p>`;
      decorateScreen(SCREEN);
      this.bind();
    },
    bind() {
      const reload = async () => { open = { key: "", mode: "" }; error = ""; await this.load(); this.render(); };
      const on = (id, f) => $(id).addEventListener("change", async (e) => { st[f] = e.target.value; await reload(); });
      on("#qaStatus", "status"); on("#qaProduct", "product");
      $$("[data-kpi]").forEach((b) => b.addEventListener("click", async () => { st.status = st.status === b.dataset.kpi ? "" : b.dataset.kpi; await reload(); }));
      let timer = null;
      $("#qaQ").addEventListener("input", (e) => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          st.q = e.target.value;
          await reload();
          const q = $("#qaQ"); q.focus(); q.setSelectionRange(q.value.length, q.value.length);
        }, 350);
      });
      const find = (k) => data.items.find((r) => rowKey(r) === k);
      $$("[data-change]").forEach((b) => b.addEventListener("click", () => {
        const k = b.dataset.change;
        open = open.key === k && open.mode === "change" ? { key: "", mode: "" } : { key: k, mode: "change" };
        error = "";
        pick = "";
        this.render();
        if ($("#qaReason")) $("#qaReason").focus();
      }));
      $$("[data-history]").forEach((b) => b.addEventListener("click", async () => {
        const k = b.dataset.history;
        if (open.key === k && open.mode === "history") { open = { key: "", mode: "" }; this.render(); return; }
        const r = find(k);
        history = (await api(`lot-status/${enc(r.cProduct)}/${enc(r.cLot)}`)).history;
        open = { key: k, mode: "history" };
        this.render();
      }));
      if ($("#qaCancel")) $("#qaCancel").addEventListener("click", () => { open = { key: "", mode: "" }; error = ""; this.render(); });
      if ($("#qaSave")) {
        const save = async () => {
          const r = find(open.key);
          const status = $("#qaNew").value;
          pick = status;
          const reason = $("#qaReason").value.trim();
          if (!reason) { error = t("qa.lots.reason.required"); this.render(); $("#qaReason").focus(); return; }
          try {
            await api(`lot-status/${enc(r.cProduct)}/${enc(r.cLot)}`, { method: "POST", body: { cStatus: status, cReason: reason } });
            toast(t("qa.lots.changed", { lot: r.cLot, s: t("qa.lot." + status) }), "success");
            await reload();
          } catch (e) {
            error = t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic");
            this.render();
          }
        };
        $("#qaSave").addEventListener("click", save);
        $("#qaReason").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); save(); } });
      }
    },
  };
}

const link = (path, label) => (canOpen(path) ? `<a href="#${path}">${esc(label)}</a>` : esc(label));
