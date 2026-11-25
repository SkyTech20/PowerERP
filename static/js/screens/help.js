/* PowerERP: Help: the manual of the screens (help/<lang>/<screen>.md on the server).
   #/help             the home page: the screens one can read about, and how to use the help
   #/help/<code>      the page of the item's screen, scrolled to the item (sales.invoices.post)
   The server sends only the screens and items the user's role may see. */
import { $, $$, api, enc, esc, lang, t } from "../core.js";
import { MENU } from "../menu.js";

const INTRO = "_intro";
const moduleOf = (screen) => (screen.startsWith("_") ? "_" : screen.split(".")[0]);
const moduleName = (m) => (m === "_" ? t("help.general") : t("menu." + m));
export const helpLink = (code) => "#/help/" + code;
// The route of the screen in the menu (to open it from its help), or ""
export const screenRoute = (screen) => {
  const item = MENU.flatMap((m) => (m.items ? m.items : [m])).find((i) => typeof i === "object" && i.k === screen);
  return item && item.route ? item.route : "";
};

function groupsOf(toc) {
  const groups = [];
  toc.screens.forEach((s) => {
    const m = moduleOf(s.screen);
    if (!groups.length || groups[groups.length - 1].m !== m) groups.push({ m, screens: [] });
    groups[groups.length - 1].screens.push(s);
  });
  return groups;
}

// The table of contents: the screens grouped by module (the server keeps the order of the menu)
export function tocHtml(toc, current) {
  return groupsOf(toc).map((g) => `<div class="help-toc-group"><div class="help-toc-module">${esc(moduleName(g.m))}</div>
    ${g.screens.map((s) => `<a class="help-toc-screen ${s.screen === current ? "active" : ""}" href="${helpLink(s.screen)}">${esc(s.title)}</a>
      ${s.screen === current ? s.sections.map((x) => `<a class="help-toc-section" data-toc="${esc(x.code)}" href="${helpLink(x.code)}">${esc(x.title)}</a>`).join("") : ""}`).join("")}
    </div>`).join("");
}

const badge = (it) => (it.untranslated ? ` <span class="badge">${esc(t("help.untranslated"))}</span>` : "");
// A small button that copies the link of an item (its code is in the tip: support and the AI quote it)
const linkButton = (code) => `<button type="button" class="help-link" data-copy-help="${esc(code)}" title="${esc(t("help.copyLink"))} · ${esc(code)}" aria-label="${esc(t("help.copyLink"))}">🔗</button>`;

// The items of a page: a section (level 2) is a heading and its text; the fields under it (level 3 and more)
// are a list of definitions, name on the left and text on the right.
export function itemsHtml(items) {
  const out = [];
  let fields = [];
  const flush = () => {
    if (fields.length) out.push(`<dl class="help-fields">${fields.join("")}</dl>`);
    fields = [];
  };
  items.forEach((it) => {
    if (it.level >= 3) {
      fields.push(`<div class="help-field" id="help-${esc(it.code)}"><dt>${esc(it.title)}${badge(it)}${linkButton(it.code)}</dt><dd class="help-body">${it.html}</dd></div>`);
      return;
    }
    flush();
    out.push(`<h2 class="help-h2" id="help-${esc(it.code)}">${esc(it.title)}${badge(it)}${linkButton(it.code)}</h2>${it.html ? `<div class="help-body">${it.html}</div>` : ""}`);
  });
  flush();
  return out.join("");
}

// The words of the query marked in a text (escaped first)
export function mark(text, q) {
  const words = String(q || "").split(/\s+/).filter((w) => w.length > 1).map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const safe = esc(text);
  return words.length ? safe.replace(new RegExp(`(${words.join("|")})`, "gi"), "<mark>$1</mark>") : safe;
}

export function resultsHtml(res) {
  if (!res.items.length) return `<div class="empty">${esc(t("help.search.none", { q: res.q }))}</div>`;
  return `<div class="help-count">${esc(t("help.search.count", { n: res.items.length }))}</div>
    <ul class="help-results">${res.items.map((r) => `<li><a href="${helpLink(r.code)}">
    <div class="help-path">${esc(r.path.join(" › "))}</div><b>${mark(r.title, res.q)}</b>
    <div class="help-snippet">${mark(r.snippet, res.q)}</div></a></li>`).join("")}</ul>`;
}

// The home page: one card per screen, by module
export function cardsHtml(toc) {
  return groupsOf(toc).filter((g) => g.m !== "_").map((g) => `<h2 class="help-h2">${esc(moduleName(g.m))}</h2>
    <div class="help-cards">${g.screens.map((s) => `<a class="help-card" href="${helpLink(s.screen)}"><b>${esc(s.title)}</b>
      <span>${esc(s.summary || "")}</span></a>`).join("")}</div>`).join("");
}

let spy = null; // the observer that follows the section on screen
export function helpView(code) {
  let toc = null, page = null, loadedLang = "", query = "", results = null, timer = null;
  const target = code || INTRO;
  async function load() {
    loadedLang = lang;
    toc = await api("help/toc?lang=" + lang);
    let screen = target;
    if (target !== INTRO && !toc.screens.some((s) => s.screen === target)) {
      try { screen = (await api(`help/item/${enc(target)}?lang=${lang}`)).screen; } catch (e) { screen = INTRO; }
    }
    try { page = await api(`help/page/${enc(screen)}?lang=${lang}`); } catch (e) { page = { screen, items: [] }; }
    if (query) results = await api(`help/search?q=${enc(query)}&lang=${lang}`);
  }
  function head() {
    const top = page.items[0];
    const home = page.screen === INTRO;
    const crumbs = home ? "" : `<div class="crumbs"><a href="#/help">${esc(t("help.title"))}</a> › ${esc(moduleName(moduleOf(page.screen)))}</div>`;
    const route = home ? "" : screenRoute(page.screen);
    const open = route ? `<a class="btn" href="#${route}">${esc(t("help.openScreen"))} →</a>` : "";
    return `<div class="help-head">${crumbs}<div class="help-head-row"><h1>${esc(home ? t("help.title") : top ? top.title : "")}${top ? badge(top) : ""}</h1>${open}</div>
      ${home ? `<p class="help-lead">${esc(t("help.subtitle"))}</p>` : top && top.html ? `<div class="help-body help-lead">${top.html}</div>` : ""}</div>`;
  }
  function body() {
    if (results) return resultsHtml(results);
    if (!page.items.length) return `<div class="empty">${esc(t("help.notFound"))}</div>`;
    if (page.screen === INTRO) return cardsHtml(toc) + itemsHtml(page.items.slice(1));
    return itemsHtml(page.items.slice(1));
  }
  function follow() { // the section on screen is the active one of the contents
    if (spy) spy.disconnect();
    const links = $$("[data-toc]");
    if (!links.length || typeof IntersectionObserver === "undefined") return;
    spy = new IntersectionObserver((entries) => {
      const seen = entries.filter((e) => e.isIntersecting).map((e) => e.target.id.slice(5));
      if (seen.length) links.forEach((a) => a.classList.toggle("current", a.dataset.toc === seen[0]));
    }, { rootMargin: "-70px 0px -70% 0px" });
    $$(".help-h2[id]").forEach((h) => spy.observe(h));
  }
  function render() {
    if (loadedLang !== lang) { load().then(render); return; } // the language was switched
    $("#view").innerHTML = `<div class="help-layout">
        <nav class="help-toc" aria-label="${esc(t("help.contents"))}">${tocHtml(toc, page.screen)}</nav>
        <div class="help-main">
          <div class="help-search"><span class="help-search-icon" aria-hidden="true">⌕</span>
            <input type="search" id="helpSearch" placeholder="${esc(t("help.search.ph"))}" value="${esc(query)}" aria-label="${esc(t("help.search.ph"))}">
            <kbd title="${esc(t("help.search.key"))}">/</kbd></div>
          ${results ? "" : head()}
          <div class="help-content">${body()}</div>
        </div>
      </div>`;
    const input = $("#helpSearch");
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        query = input.value.trim();
        results = query ? await api(`help/search?q=${enc(query)}&lang=${lang}`) : null;
        const at = input.selectionStart;
        render();
        window.scrollTo(0, 0);
        const again = $("#helpSearch");
        again.focus();
        try { again.setSelectionRange(at, at); } catch (e) { /* ignore */ }
      }, 250);
    });
    input.addEventListener("keydown", (e) => { if (e.key === "Escape" && input.value) { input.value = ""; input.dispatchEvent(new Event("input")); } });
    $$(".help-layout a[href^='#/help']").forEach((a) => a.addEventListener("click", () => { query = ""; results = null; }));
    follow();
    if (!results && code && code !== page.screen) {
      const el = document.getElementById("help-" + code);
      // after the router's scroll to the top of the page
      if (el) { el.classList.add("help-target"); setTimeout(() => el.scrollIntoView({ block: "start" }), 0); }
    }
  }
  return { load, render };
}

// "/" anywhere on the Help screen (outside a field) goes to the search box
if (typeof document !== "undefined") document.addEventListener("keydown", (e) => {
  const box = document.getElementById("helpSearch");
  if (e.key !== "/" || !box || /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) return;
  e.preventDefault();
  box.focus();
});
