/* PowerERP: Quality > Nonconformances (step 5 of the SCOR / ISO plan). The lot status screen is screens/lots.js. */
import { api, esc, fmtDateTime, t } from "../core.js";
import { RES } from "../registry.js";
import { opts, qtyFmt, today } from "./inventory.js";

export const LOT_STATUSES = ["released", "on_hold", "quarantine", "rejected"];
export const NC_SOURCES = ["internal", "reception", "production", "customer"];
export const NC_SEVERITIES = ["minor", "major", "critical"];
export const NC_DISPOSITIONS = ["pending", "use_as_is", "rework", "scrap", "return_supplier"];
const LOT_CLASS = { released: "yes", on_hold: "warn", quarantine: "warn", rejected: "no" };
const SEVERITY_CLASS = { minor: "", major: "warn", critical: "no" };
export const lotBadge = (s) => (s ? `<span class="badge ${LOT_CLASS[s] || ""}">${esc(t("qa.lot." + s))}</span>` : "");
const ncBadge = (s) => `<span class="badge ${s === "open" ? "warn" : "yes"}">${esc(t("qa.nc.status." + s))}</span>`;
const sevBadge = (s) => `<span class="badge ${SEVERITY_CLASS[s] || ""}">${esc(t("qa.nc.sev." + s))}</span>`;
const isOpen = (m, isNew) => !isNew && m.cStatus === "open";

const ncHistory = {
  html: (m) => `<div class="card"><div class="card-head"><h2>${esc(t("qa.nc.history"))}</h2></div><div class="table-wrap"><table class="grid"><thead><tr>
      <th>${esc(t("mfg.ap.when"))}</th><th>${esc(t("mfg.ap.who"))}</th><th>${esc(t("mfg.ap.action"))}</th><th>${esc(t("mfg.ap.comment"))}</th></tr></thead><tbody>
      ${(m.history || []).slice().reverse().map((h) => `<tr><td>${esc(fmtDateTime(h.dAt))}</td><td>${esc(h.cUser)}</td><td>${esc(t("qa.nc.a." + h.cAction))}</td>
        <td>${esc(h.cAction === "closed" ? t("qa.nc.disp." + h.cComment) : h.cComment)}</td></tr>`).join("")}</tbody></table></div></div>`,
};

Object.assign(RES, {
  qanc: {
    api: "nonconformances", route: "/qa/nonconformances", title: "qa.nc.title", sub: "qa.nc.subtitle",
    one: "qa.nc.one", newTitle: "qa.nc.new", id: (r) => r.iNo, label: (r) => `${r.iNo}${r.cProduct ? " — " + r.cProduct : ""}${r.cLot ? " · " + r.cLot : ""}`, sort: "iNo", dir: "desc",
    columns: [
      { f: "iNo", l: "qa.nc.f.iNo", n: true }, { f: "cStatus", l: "qa.nc.f.cStatus", fmt: ncBadge }, { f: "dDate", l: "qa.nc.f.dDate" },
      { f: "cSource", l: "qa.nc.f.cSource", fmt: (v) => esc(t("qa.nc.src." + v)) }, { f: "cSeverity", l: "qa.nc.f.cSeverity", fmt: sevBadge },
      { f: "cProduct", l: "qa.nc.f.cProduct" }, { f: "cLot", l: "qa.nc.f.cLot" }, { f: "cLotStatus", l: "qa.nc.f.cLotStatus", fmt: lotBadge },
      { f: "dQty", l: "qa.nc.qty", n: true, fmt: (v, r) => (v === "" || v == null ? "" : `${esc(qtyFmt(v))} ${esc(r.cUOM || "")}`) },
      { f: "cDescription", l: "qa.nc.f.cDescription", wrap: true }, { f: "cDisposition", l: "qa.nc.f.cDisposition", fmt: (v) => esc(t("qa.nc.disp." + v)) },
    ],
    filters: [
      { f: "cStatus", l: "qa.nc.f.cStatus", options: opts("qa.nc.status.", ["open", "closed"]) },
      { f: "cSource", l: "qa.nc.f.cSource", options: opts("qa.nc.src.", NC_SOURCES) },
      { f: "cSeverity", l: "qa.nc.f.cSeverity", options: opts("qa.nc.sev.", NC_SEVERITIES) },
      { f: "cProduct", l: "qa.nc.f.cProduct", lookup: "products" },
    ],
    defaults: () => ({ cStatus: "open", dDate: today(), cSource: "internal", cSeverity: "minor", cDisposition: "pending", lHoldLot: true, history: [] }),
    // a closed nonconformance is read; it is opened again through its action
    locked: (m, isNew) => !isNew && m.cStatus === "closed",
    badge: (m, isNew) => (isNew ? "" : ncBadge(m.cStatus)),
    actions: [
      { id: "close", l: "qa.nc.close", perm: "close", primary: true, show: isOpen, confirm: "qa.nc.close.confirm", done: "qa.nc.closed",
        run: (m, ctx) => api(ctx.path + "/close", { method: "POST", body: m }) },
      { id: "reopen", l: "qa.nc.reopen", perm: "close", show: (m, isNew) => !isNew && m.cStatus === "closed", done: "qa.nc.reopened",
        run: (m, ctx) => {
          const why = prompt(t("qa.nc.reopen.why"));
          return why === null ? null : api(ctx.path + "/reopen", { method: "POST", body: { cComment: why } });
        } },
    ],
    sections: [
      { t: "qa.nc.what", help: "qa.nc.what.help", fields: [
        { f: "dDate", l: "qa.nc.f.dDate", type: "date", req: true },
        { f: "cSource", l: "qa.nc.f.cSource", type: "select", options: opts("qa.nc.src.", NC_SOURCES) },
        { f: "cRef", l: "qa.nc.f.cRef", help: "qa.nc.f.cRef.help" },
        { f: "cSeverity", l: "qa.nc.f.cSeverity", type: "select", options: opts("qa.nc.sev.", NC_SEVERITIES) },
        { f: "cProduct", l: "qa.nc.f.cProduct", lookup: "products", rerender: true, span: 2 },
        { f: "cLot", l: "qa.nc.f.cLot", lookup: "lot_choices", lookupParams: (m) => ({ product: m.cProduct }), help: "qa.nc.f.cLot.help" },
        { f: "dQty", l: "qa.nc.f.dQty", type: "number" },
        { f: "cUOM", l: "qa.nc.f.cUOM", readonly: true, show: (m) => !!m.cUOM },
        { f: "cDescription", l: "qa.nc.f.cDescription", type: "textarea", req: true, span: 4 },
        { f: "lHoldLot", l: "qa.nc.f.lHoldLot", type: "check", help: "qa.nc.f.lHoldLot.help" },
        { f: "cLotStatus", l: "qa.nc.f.cLotStatus", readonly: true, fmt: (v) => (v ? t("qa.lot." + v) : ""), show: (m) => !!m.cLotStatus },
      ] },
      { t: "qa.nc.decision", help: "qa.nc.decision.help", fields: [
        { f: "cCause", l: "qa.nc.f.cCause", type: "textarea", span: 4 },
        { f: "cDisposition", l: "qa.nc.f.cDisposition", type: "select", options: opts("qa.nc.disp.", NC_DISPOSITIONS), help: "qa.nc.f.cDisposition.help" },
        { f: "cAction", l: "qa.nc.f.cAction", type: "textarea", span: 4, help: "qa.nc.f.cAction.help" },
      ] },
      { t: "qa.nc.tracking", fields: [
        { f: "cUser", l: "qa.nc.f.cUser", readonly: true, show: (m) => !!m.iNo },
        { f: "dCreated", l: "qa.nc.f.dCreated", readonly: true, fmt: fmtDateTime, show: (m) => !!m.iNo },
        { f: "cClosedBy", l: "qa.nc.f.cClosedBy", readonly: true, show: (m) => !!m.dClosed },
        { f: "dClosed", l: "qa.nc.f.dClosed", readonly: true, fmt: fmtDateTime, show: (m) => !!m.dClosed },
      ] },
    ],
    panels: [ncHistory],
  },
});
