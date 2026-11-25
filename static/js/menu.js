/* PowerERP: The sidebar menu and the static texts of the page. */
import { $, $$, esc, lang, t, toast } from "./core.js";
import { activeMenuRoute, currentPath } from "./router.js";
import { RES } from "./registry.js";
import { can, isAdmin } from "./state.js";
import { TABSETS } from "./views.js";

// ------------------------------------------------------------------ Menu
// Items given as plain strings are visible but disabled.
export const MENU = [
  { k: "dashboard", icon: "🏠", route: "/" },
  { k: "help", icon: "❓", route: "/help" },
  { sep: true },
  { k: "gl", icon: "📒", items: [{ k: "gl.accounts", route: "/gl" }, "gl.journal", "gl.periods", "gl.statements", "gl.budgets", "gl.bankrec"] },
  { k: "ap", icon: "💳", items: [{ k: "ap.suppliers", route: "/suppliers" }, { k: "ap.invoices", route: "/invoices" }, "ap.payments", "ap.chequeRun", "ap.recurring", "ap.aging"] },
  { k: "pur", icon: "🛒", items: [{ k: "pur.po", route: "/po" }, { k: "pur.receptions", route: "/receptions" }, "pur.requisitions", "pur.returns", "pur.pricelists"] },
  { k: "ar", icon: "💰", items: ["ar.invoices", "ar.receipts", "ar.credits", "ar.collections"] },
  { k: "sales", icon: "📈", items: [{ k: "sales.customers", route: "/sales/customers" }, { k: "sales.priceLists", route: "/sales/price-lists" }, { k: "sales.invoices", route: "/sales/invoices" }, "sales.quotes", "sales.orders", "sales.shipping", "sales.commissions"] },
  { k: "inv", icon: "📦", items: [
    { k: "inv.items", route: "/inv/items" }, { k: "inv.stock", route: "/inv/stock" }, { k: "inv.movements", route: "/inv/movements" },
    { k: "inv.replenishment", route: "/inv/replenishment" }, { k: "inv.count", route: "/inv/counts" }, { k: "inv.valuation", route: "/inv/valuation" },
    { k: "inv.warehouses", route: "/inv/warehouses" }, { k: "inv.params", route: "/inv/params" }, { k: "inv.setup", route: "/inv/categories" },
  ] },
  { k: "prod", icon: "🏭", items: [
    { k: "prod.recipes", route: "/prod/recipes" }, { k: "prod.orders", route: "/prod/orders" }, "prod.shopfloor", { k: "prod.traceability", route: "/prod/traceability" }, "prod.schedule", "prod.mrp",
    { k: "prod.items", route: "/prod/items" }, { k: "prod.operations", route: "/prod/operations" }, { k: "prod.resources", route: "/prod/resources" },
    { k: "prod.workcenters", route: "/prod/work-centers" }, { k: "prod.setupmatrix", route: "/prod/setup-matrix" }, { k: "prod.calendars", route: "/prod/calendars" }, { k: "prod.setup", route: "/prod/capabilities" },
  ] },
  { k: "hr", icon: "👥", items: ["hr.employees", "hr.timesheets", "hr.payroll", "hr.benefits"] },
  { k: "fa", icon: "🏢", items: ["fa.assets", "fa.depreciation"] },
  { k: "proj", icon: "📁", items: ["proj.projects", "proj.jobcost"] },
  { k: "crm", icon: "🤝", items: ["crm.contacts", "crm.opportunities"] },
  { k: "rep", icon: "📊", items: ["rep.designer", "rep.bi"] },
  { k: "admin", icon: "⚙️", items: ["admin.companies", { k: "admin.users", route: "/admin/users", admin: true }, { k: "admin.roles", route: "/admin/roles", admin: true }, { k: "admin.audit", route: "/admin/audit", admin: true }, { k: "admin.taxes", route: "/admin/taxes" }, "admin.currencies", { k: "admin.backups", route: "/admin/backups", admin: true }, { k: "admin.settings", route: "/admin/settings", admin: true }] },
];
export const openGroups = new Set(["gl", "ap", "pur", "sales", "inv"]);
// Menu items flagged admin: true are links for administrators only; the others need the view of their screen
// (the menu key is the screen of the permissions).
export const usable = (i) => typeof i === "object" && (i.admin ? isAdmin() : can(i.k));

// The screen (menu key) of a resource: the menu entry it opens from (a tab opens from the first tab's entry).
const SCREEN_OF_ROUTE = Object.fromEntries(MENU.flatMap((m) => m.items || []).filter((i) => typeof i === "object").map((i) => [i.route, i]));
export function menuItemOf(R) {
  const first = R.tabset ? RES[TABSETS[R.tabset][0][0]] : R;
  return SCREEN_OF_ROUTE[R.menu || first.menu || first.route] || SCREEN_OF_ROUTE[R.route] || null;
}
// May the user do this on the screen of resource R? (an administrator-only screen: administrators only)
export function canOn(R, action = "view") {
  const item = menuItemOf(R);
  if (!item) return isAdmin();
  return item.admin ? isAdmin() : can(item.k, action);
}

export function renderSidebar() {
  const path = currentPath();
  const menuRoute = activeMenuRoute(path);
  const isActive = (route) => (route === "/" ? path === "/" : route === menuRoute || path === route || path.startsWith(route + "/"));
  const html = MENU.map((m) => {
    if (m.sep) return '<div class="nav-sep"></div>';
    if (m.route) {
      return `<a class="nav-link ${isActive(m.route) ? "active" : ""}" href="#${m.route}"><span class="nav-icon">${m.icon}</span>${esc(t("menu." + m.k))}</a>`;
    }
    const enabled = m.items.some(usable);
    // a role sees only what it may open; the administrator also sees the modules still to come (locked)
    if (!enabled && !isAdmin()) return "";
    const sub = m.items.filter((i) => isAdmin() || usable(i)).map((i) => {
      if (usable(i)) {
        return `<a class="nav-link ${isActive(i.route) ? "active" : ""}" href="#${i.route}">${esc(t("menu." + i.k))}</a>`;
      }
      const k = typeof i === "object" ? i.k : i;
      return `<span class="nav-link disabled" aria-disabled="true" title="${esc(t("app.menuUnavailable"))}">${esc(t("menu." + k))}<span class="lock">🔒</span></span>`;
    }).join("");
    return `<details class="nav-group ${enabled ? "" : "dimmed"}" data-group="${m.k}" ${openGroups.has(m.k) ? "open" : ""}>
      <summary><span class="nav-icon">${m.icon}</span>${esc(t("menu." + m.k))}<span class="chev">▶</span></summary>
      <div class="nav-sub">${sub}</div></details>`;
  }).join("");
  const nav = $("#sidebar");
  nav.innerHTML = html;
  $$("details.nav-group", nav).forEach((d) => d.addEventListener("toggle", () => {
    if (d.open) openGroups.add(d.dataset.group); else openGroups.delete(d.dataset.group);
  }));
  $$(".nav-link.disabled", nav).forEach((el) => el.addEventListener("click", () => toast(t("app.unavailable"))));
  $$("a.nav-link", nav).forEach((el) => el.addEventListener("click", () => document.body.classList.remove("nav-open")));
}

export function applyStaticI18n() {
  document.documentElement.lang = lang;
  $$("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  $$(".lang-switch button").forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
}
