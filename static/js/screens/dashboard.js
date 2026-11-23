/* PowerERP: Dashboard. */
import { $, $$, api, esc, fmtInt, money, sourceBadge, statusBadge, t } from "../core.js";
import { pageHead } from "../views.js";

// ---------- Dashboard
export function dashboardView() {
  let data = null;
  return {
    async load() { data = await api("summary"); },
    render() {
      const kpi = (route, label, value, meta) => `<a class="card kpi" href="#${route}"><div class="label">${esc(label)}</div><div class="value">${value}</div><div class="meta">${esc(meta)}</div></a>`;
      const recent = data.recentInvoices.length
        ? `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("f.cNoFacture"))}</th><th>${esc(t("f.cNomFourn"))}</th><th>${esc(t("f.dDateFacture"))}</th><th class="num">${esc(t("f.dTotalFacture"))}</th><th>${esc(t("f.cStatut"))}</th></tr></thead><tbody>
          ${data.recentInvoices.map((i) => `<tr class="clickable" data-href="#/invoices/${i.id}"><td>${esc(i.cNoFacture)}</td><td>${esc(i.cNomFourn || i.cNoFourn)}</td><td>${esc(i.dDateFacture)}</td><td class="num">${esc(money(i.dTotalFacture, i.cDevise))}</td><td>${statusBadge(i.cStatut)} ${i.cSource === "SkyAI" ? sourceBadge(i.cSource) : ""}</td></tr>`).join("")}
          </tbody></table></div>`
        : `<div class="empty">${esc(t("common.empty"))}</div>`;
      $("#view").innerHTML = pageHead(t("dash.title"), t("dash.subtitle")) + `
        <div class="kpis">
          ${kpi("/suppliers", t("dash.suppliers"), fmtInt(data.suppliers), t("dash.activeSuppliers", { n: fmtInt(data.activeSuppliers) }))}
          ${kpi("/gl/accounts", t("dash.gl"), fmtInt(data.glAccounts), t("dash.cc", { n: fmtInt(data.costCenters) }))}
          ${kpi("/po", t("dash.po"), fmtInt(data.purchaseOrders), t("dash.unbilledPo", { n: data.unbilledPOs }))}
          ${kpi("/receptions", t("dash.receptions"), fmtInt(data.receptions), t("dash.unbilledRec", { n: data.unbilledReceptions }))}
          ${kpi("/invoices", t("dash.invoices"), fmtInt(data.openInvoices), money(data.openInvoicesAmount) + " · " + t("dash.invoicesTotal", { n: data.invoices }))}
          ${data.products != null ? kpi(data.reorderItems ? "/inv/replenishment" : "/inv/valuation", t("dash.inventory"), money(data.stockValue), t("dash.inventoryMeta", { n: fmtInt(data.products), r: data.reorderItems })) : ""}
        </div>
        <div class="card"><div class="card-head"><h2>${esc(t("dash.recent"))}</h2><a class="btn small" style="margin-left:auto" href="#/invoices">${esc(t("menu.ap.invoices"))} →</a></div>${recent}</div>`;
      $$("tr[data-href]").forEach((tr) => tr.addEventListener("click", () => { location.hash = tr.dataset.href; }));
    },
  };
}
