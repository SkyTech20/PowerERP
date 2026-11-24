/* PowerERP: Help: the manual of the screens (help/<lang>/<screen>.md on the server).
   #/help             the general page
   #/help/<code>      the page of the item's screen, scrolled to the item (sales.invoices.post)
   The server sends only the screens and items the user's role may see. */
import { $, $$, api, enc, esc, lang, t } from "../core.js";
import { pageHead } from "../views.js";

const INTRO = "_intro";
const moduleOf = (screen) => (screen.startsWith("_") ? "_" : screen.split(".")[0]);
const moduleName = (m) => (m === "_" ? t("help.general") : t("menu." + m));
export const helpLink = (code) => "#/help/" + code;

// The table of contents: the screens grouped by module (the server keeps the order of the menu)
export function tocHtml(toc, current) {
  const groups = [];
  toc.screens.forEach((s) => {
    const m = moduleOf(s.screen);
    if (!groups.length || groups[groups.length - 1].m !== m) groups.push({ m, screens: [] });
    groups[groups.length - 1].screens.push(s);
  });
  return groups.map((g) => `<div class="help-toc-group"><div class="help-toc-module">${esc(moduleName(g.m))}</div>
    ${g.screens.map((s) => `<a class="help-toc-screen ${s.screen === current ? "active" : ""}" href="${helpLink(s.screen)}">${esc(s.title)}</a>
      ${s.screen === current ? s.sections.map((x) => `<a class="help-toc-section" href="${helpLink(x.code)}">${esc(x.title)}</a>`).join("") : ""}`).join("")}
    </div>`).join("");
}

// One item: its heading (with its code, a link to it) and its text (HTML made by the server from the Markdown)
export function itemHtml(it) {
  const h = Math.min(it.level + 1, 6); // the page title is the h1 of the page head
  const badge = it.untranslated ? ` <span class="badge">${esc(t("help.untranslated"))}</span>` : "";
  return `<section class="help-item level-${it.level}" id="help-${esc(it.code)}">
    <h${h}>${esc(it.title)}${badge} <a class="help-code" href="${helpLink(it.code)}" title="${esc(t("help.linkTitle"))}">${esc(it.code)}</a></h${h}>
    <div class="help-body">${it.html}</div></section>`;
}

export function resultsHtml(res) {
  if (!res.items.length) return `<div class="empty">${esc(t("help.search.none", { q: res.q }))}</div>`;
  return `<ul class="help-results">${res.items.map((r) => `<li><a href="${helpLink(r.code)}"><b>${esc(r.title)}</b></a>
    <div class="help-path">${esc(r.path.join(" › "))} · <code>${esc(r.code)}</code></div>
    <div class="help-snippet">${esc(r.snippet)}</div></li>`).join("")}</ul>`;
}

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
  function render() {
    if (loadedLang !== lang) { load().then(render); return; } // the language was switched
    const top = page.items[0];
    const body = results ? resultsHtml(results)
      : page.items.length ? page.items.slice(1).map(itemHtml).join("")
        : `<div class="empty">${esc(t("help.notFound"))}</div>`;
    const intro = top ? `<div class="help-body help-lead">${top.html}</div>` : "";
    $("#view").innerHTML = pageHead(t("help.title"), t("help.subtitle")) + `
      <div class="help-layout">
        <nav class="card help-toc" aria-label="${esc(t("help.contents"))}">${tocHtml(toc, page.screen)}</nav>
        <div class="card help-page">
          <div class="help-search"><input type="search" id="helpSearch" placeholder="${esc(t("help.search.ph"))}" value="${esc(query)}" aria-label="${esc(t("help.search.ph"))}"></div>
          ${results ? "" : top ? `<h2 class="help-title" id="help-${esc(top.code)}">${esc(top.title)}${top.untranslated ? ` <span class="badge">${esc(t("help.untranslated"))}</span>` : ""} <a class="help-code" href="${helpLink(top.code)}">${esc(top.code)}</a></h2>${intro}` : ""}
          <div class="help-content">${body}</div>
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
        const again = $("#helpSearch");
        again.focus();
        try { again.setSelectionRange(at, at); } catch (e) { /* ignore */ }
      }, 250);
    });
    $$(".help-page a[href^='#/help/']").forEach((a) => a.addEventListener("click", () => { query = ""; results = null; }));
    if (!results && code && code !== page.screen) {
      const el = document.getElementById("help-" + code);
      // after the router's scroll to the top of the page
      if (el) { el.classList.add("help-target"); setTimeout(() => el.scrollIntoView({ block: "start" }), 0); }
    }
  }
  return { load, render };
}
