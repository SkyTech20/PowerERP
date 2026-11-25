/* PowerERP: Help inside the screens (H2): the "?" button of a list or form, the ⓘ next to the documented
   fields, and the side panel that shows the help of the screen without leaving it.

   The item code of a field (help/<lang>/<screen>.md):
     <base>.<field>            a field of the form (its data-f), e.g. sales.invoices.cCustomer
     <base>.<grid>.<field>     a column (or a detail field) of a grid, e.g. sales.invoices.lines.dQty
   <base> is the screen (menu key); for the other tabs of a tab set, <screen>.<resource>, e.g. admin.taxes.taxgroups. */
import { $, $$, api, enc, esc, lang, t, toast } from "./core.js";
import { menuItemOf } from "./menu.js";
import { RES } from "./registry.js";
import { helpLink, itemsHtml } from "./screens/help.js";
import { user } from "./state.js";
import { TABSETS } from "./views.js";

// The screen of a resource (the menu key, as in the permissions), or null
export function screenOf(R) {
  const item = menuItemOf(R);
  return item ? item.k : null;
}
// The prefix of the codes of a resource's fields
export function helpBase(R) {
  const screen = screenOf(R);
  if (!screen || !R.tabset || RES[TABSETS[R.tabset][0][0]] === R) return screen;
  return `${screen}.${Object.keys(RES).find((k) => RES[k] === R)}`;
}
// The code of the field behind an input: data-f (form) or data-lf inside a grid [data-grid]
export function fieldCode(base, el) {
  if (el.dataset.f) return `${base}.${el.dataset.f}`;
  const grid = el.closest("[data-grid]");
  return el.dataset.lf && grid ? `${base}.${grid.dataset.grid}.${el.dataset.lf}` : null;
}

// The help page of a screen, once per user and language (null: no page, or not part of the role)
// (the contents say which screens have a page: no request for the others)
const pages = {};
const cached = (key, load) => { if (!(key in pages)) pages[key] = load().catch(() => null); return pages[key]; };
export async function helpPage(screen) {
  const who = `${user ? user.username : ""}:${lang}`;
  const toc = await cached(who, () => api(`help/toc?lang=${lang}`, { noAuthRedirect: true }));
  if (!toc || !toc.screens.some((s) => s.screen === screen)) return null;
  return cached(`${who}:${screen}`, () => api(`help/page/${enc(screen)}?lang=${lang}`, { noAuthRedirect: true }));
}

// The "?" button of a page head: shown once the screen's help page is known to exist (decorate)
export const helpButton = (R) => {
  const screen = screenOf(R);
  return screen ? `<button type="button" class="btn help-btn" data-help-open="${esc(screen)}" title="${esc(t("help.open"))}" aria-label="${esc(t("help.open"))}" hidden>?</button>` : "";
};

const icon = (code, it) => `<button type="button" class="help-i" data-help="${esc(code)}" title="${esc(it.summary || it.title)}" aria-label="${esc(t("help.aboutField", { f: it.title }))}">ⓘ</button>`;

// After a list or form is drawn: show its "?" and put an ⓘ next to every documented field / column
export async function decorateHelp(R) {
  const screen = screenOf(R);
  if (!screen) return;
  const view = $("#view");
  const drawn = view.firstElementChild;
  const page = await helpPage(screen);
  if (!page || view.firstElementChild !== drawn) return; // no help, or the screen was drawn again meanwhile
  const items = Object.fromEntries(page.items.map((it) => [it.code, it]));
  $$("[data-help-open]", view).forEach((b) => { b.hidden = false; });
  const base = helpBase(R);
  $$("label[for]", view).forEach((label) => {
    if ($(".help-i", label)) return;
    const input = document.getElementById(label.htmlFor);
    const code = input && fieldCode(base, input);
    if (code && items[code]) label.insertAdjacentHTML("beforeend", " " + icon(code, items[code]));
  });
  $$("label.check", view).forEach((label) => { // a checkbox holds its input inside its label
    const input = $("input", label);
    const code = input && !$(".help-i", label) && fieldCode(base, input);
    if (code && items[code]) label.insertAdjacentHTML("beforeend", " " + icon(code, items[code]));
  });
  $$("[data-grid] th[data-col]", view).forEach((th) => {
    const code = `${base}.${th.closest("[data-grid]").dataset.grid}.${th.dataset.col}`;
    if (items[code] && !$(".help-i", th)) th.insertAdjacentHTML("beforeend", " " + icon(code, items[code]));
  });
}

// ------------------------------------------------------------------ the side panel
export function closeHelpPanel() {
  const p = $("#helpPanel");
  if (p) p.remove();
  document.body.classList.remove("help-open");
}

export async function openHelpPanel(code) {
  const screen = code.split(".").slice(0, 2).join(".");
  const page = await helpPage(screen);
  if (!page) return;
  closeHelpPanel();
  const [top, ...rest] = page.items;
  document.body.insertAdjacentHTML("beforeend", `<aside class="help-panel" id="helpPanel" role="complementary" aria-label="${esc(t("help.title"))}">
    <div class="help-panel-head"><b>${esc(top.title)}</b>
      <a class="btn small" href="${helpLink(code)}">${esc(t("help.openFull"))}</a>
      <button type="button" class="icon-btn" data-help-close aria-label="${esc(t("help.close"))}">✕</button></div>
    <div class="help-panel-body"><div class="help-body help-lead">${top.html}</div>${itemsHtml(rest)}</div></aside>`);
  document.body.classList.add("help-open");
  const target = document.getElementById("help-" + code);
  if (target && code !== screen) { target.classList.add("help-target"); target.scrollIntoView({ block: "start" }); }
}

// The address of an item, to send to a colleague or to support
export async function copyHelpLink(code) {
  const url = location.href.split("#")[0] + helpLink(code);
  try {
    await navigator.clipboard.writeText(url);
    toast(t("help.copied"), "success");
  } catch (e) {
    location.hash = helpLink(code); // no clipboard (http): the address bar shows the link
  }
}

let bound = false;
export function bindHelpUi() {
  if (bound) return;
  bound = true;
  document.addEventListener("click", (e) => {
    const copy = e.target.closest("[data-copy-help]");
    if (copy) { e.preventDefault(); copyHelpLink(copy.dataset.copyHelp); return; }
    const el = e.target.closest("[data-help], [data-help-open], [data-help-close]");
    if (!el) return;
    e.preventDefault();
    e.stopPropagation();
    if (el.dataset.helpClose != null) closeHelpPanel();
    else openHelpPanel(el.dataset.help || el.dataset.helpOpen);
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && $("#helpPanel")) closeHelpPanel(); });
  window.addEventListener("hashchange", closeHelpPanel);
}
