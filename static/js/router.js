/* PowerERP: Hash router: the URL -> the screen. */
import { $, esc, t } from "./core.js";
import { canOn, renderSidebar } from "./menu.js";
import { RES } from "./registry.js";
import { accountView } from "./screens/account.js";
import { backupView } from "./screens/backups.js";
import { dashboardView } from "./screens/dashboard.js";
import { formView } from "./screens/form.js";
import { listView } from "./screens/list.js";
import { replenishmentView } from "./screens/replenishment.js";
import { roleFormView, rolesListView } from "./screens/roles.js";
import { settingsView } from "./screens/settings.js";
import { can, isAdmin, setView } from "./state.js";
import { TABSETS } from "./views.js";

// ------------------------------------------------------------------ Router
export function currentPath() {
  const h = location.hash.replace(/^#/, "");
  return h ? (h.startsWith("/") ? h : "/" + h) : "/";
}

// Menu entries that open the first screen of a tab set
export const ALIASES = { "/gl": "gl", "/admin/taxes": "taxcodes" };
export const routeOf = (path) => {
  const norm = "/" + path.split("/").filter(Boolean).join("/");
  if (ALIASES[norm]) return { key: ALIASES[norm], rest: [] };
  const key = Object.keys(RES).filter((k) => norm === RES[k].route || norm.startsWith(RES[k].route + "/"))
    .sort((a, b) => RES[b].route.length - RES[a].route.length)[0];
  return key ? { key, rest: norm.slice(RES[key].route.length).split("/").filter(Boolean) } : null;
};
// May the user open this path (a link to another screen, e.g. the product of a stock line)?
export function canOpen(path) {
  const parts = path.replace(/^#/, "").split("/").filter(Boolean);
  if (parts.join("/") === "inv/replenishment") return can("inv.replenishment");
  const hit = routeOf(parts.join("/"));
  return !hit || canOn(RES[hit.key]);
}
export function activeMenuRoute(path) {
  const hit = routeOf(path);
  if (!hit) return path;
  const R = RES[hit.key];
  return R.menu || (R.tabset ? RES[TABSETS[R.tabset][0][0]].menu || RES[TABSETS[R.tabset][0][0]].route : R.route);
}

export function resolve(path) {
  const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
  if (!parts.length) return dashboardView();
  if (parts[0] === "account") return accountView();
  if (parts.join("/") === "admin/backups") return isAdmin() ? backupView() : dashboardView();
  if (parts.join("/") === "admin/settings") return isAdmin() ? settingsView() : dashboardView();
  if (parts.join("/") === "inv/replenishment") return can("inv.replenishment") ? replenishmentView() : dashboardView();
  if (parts[0] === "admin" && parts[1] === "roles") {
    if (!isAdmin()) return dashboardView();
    if (parts.length === 2) return rolesListView();
    return roleFormView(parts[2] === "new" ? null : parts[2]);
  }
  const hit = routeOf(parts.join("/"));
  if (!hit) return dashboardView();
  const R = RES[hit.key];
  if ((R.admin && !isAdmin()) || !canOn(R)) return dashboardView(); // a screen the role may not open
  if (!hit.rest.length) return listView(hit.key);
  if (hit.rest[0] === "new" && !R.noNew) return canOn(R, "create") ? formView(hit.key, null) : listView(hit.key);
  return formView(hit.key, hit.rest.join("/"));
}

export let navToken = 0;
export async function route() {
  const token = ++navToken;
  renderSidebar();
  const v = resolve(currentPath());
  $("#view").innerHTML = `<div class="empty">${esc(t("common.loading"))}</div>`;
  try {
    await v.load();
    if (token !== navToken) return;
    setView(v);
    v.render();
    window.scrollTo(0, 0);
  } catch (e) {
    $("#view").innerHTML = `<div class="card"><div class="empty">${esc(t("err.generic"))}</div></div>`;
  }
}
