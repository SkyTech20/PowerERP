/* PowerERP: Page header and tab sets shared by the screens. */
import { esc, t } from "./core.js";
import { RES } from "./registry.js";

// ------------------------------------------------------------------ Views
export const listState = {};

export function pageHead(title, sub, actions, crumbs) {
  return `<div class="page-head"><div>${crumbs ? `<div class="crumbs">${crumbs}</div>` : ""}<h1>${esc(title)}</h1>${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</div>
    <div class="actions">${actions || ""}</div></div>`;
}

// Screens shown as tabs of one menu entry: [resource key, label]
export const TABSETS = {
  gl: [["gl", "gl.tab.accounts"], ["cc", "gl.tab.cc"]],
  tax: [["taxcodes", "tax.tab.codes"], ["taxgroups", "tax.tab.groups"]],
  wh: [["warehouses", "wh.tab.warehouses"], ["locations", "wh.tab.locations"]],
  setup: [["categories", "setup.tab.categories"], ["uom", "setup.tab.uom"]],
  mfgsetup: [["capabilities", "mfg.tab.cap"], ["setupfamilies", "mfg.tab.fam"], ["downtimereasons", "mfg.tab.down"], ["scrapreasons", "mfg.tab.scrap"]],
};
export function tabsHtml(R) {
  return `<div class="tabs">${TABSETS[R.tabset].map(([k, l]) => `<a href="#${RES[k].route}" class="${RES[k] === R ? "active" : ""}">${esc(t(l))}</a>`).join("")}</div>`;
}
export const tabLabel = (R) => { const tab = TABSETS[R.tabset].find(([k]) => RES[k] === R); return tab ? t(tab[1]) : ""; };
