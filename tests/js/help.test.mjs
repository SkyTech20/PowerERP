// The Help screen (static/js/screens/help.js): the HTML it builds from the answers of /api/help.
// Run from the PowerERP folder: node --test tests/js/
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import vm from "node:vm";

const STATIC = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "static");
globalThis.window = { addEventListener() {} };
const files = readdirSync(STATIC).filter((f) => /^i18n.*\.js$/.test(f)).sort((a, b) => (a === "i18n.js" ? -1 : b === "i18n.js" ? 1 : a.localeCompare(b)));
for (const f of files) vm.runInThisContext(readFileSync(join(STATIC, f), "utf-8"), { filename: f });
globalThis.localStorage = { getItem: () => "en", setItem() {} };
const H = await import(pathToFileURL(join(STATIC, "js", "screens", "help.js")).href);
for (const f of ["erp.js", "inventory.js", "production.js", "sales.js"]) await import(pathToFileURL(join(STATIC, "js", "resources", f)).href);
const { RES } = await import(pathToFileURL(join(STATIC, "js", "registry.js")).href);
const { MENU } = await import(pathToFileURL(join(STATIC, "js", "menu.js")).href);
const U = await import(pathToFileURL(join(STATIC, "js", "helpui.js")).href);

// The codes of help/en/<screen>.md (the headings' {#code})
const HELP = join(STATIC, "..", "help", "en");
const documented = Object.fromEntries(readdirSync(HELP).filter((f) => f.endsWith(".md") && !f.startsWith("_"))
  .map((f) => [f.slice(0, -3), new Set([...readFileSync(join(HELP, f), "utf-8").matchAll(/\{#([^}\s]+)\}\s*$/gm)].map((m) => m[1]))]));

// The screens of the menu with no help page yet. Remove a screen from this list when its page is written;
// a new screen of the menu must be added here or get its page.
const PENDING = [
  "gl.accounts", "ap.suppliers", "ap.invoices", "pur.po", "pur.receptions", "sales.customers", "sales.priceLists",
  "inv.items", "inv.stock", "inv.movements", "inv.replenishment", "inv.count", "inv.valuation", "inv.warehouses", "inv.params",
  "inv.setup", "prod.recipes", "prod.items", "prod.operations", "prod.resources", "prod.workcenters", "prod.setupmatrix",
  "prod.calendars", "prod.setup", "admin.users", "admin.roles", "admin.taxes", "admin.backups", "admin.settings",
];

const TOC = {
  screens: [
    { screen: "_intro", title: "Using the help", sections: [{ code: "_intro.find", title: "Finding an answer" }] },
    { screen: "sales.customers", title: "Customers", sections: [] },
    { screen: "sales.invoices", title: "Sales invoices", sections: [{ code: "sales.invoices.lines", title: "Lines" }] },
  ],
};

test("the contents group the screens by module and open the sections of the current one", () => {
  const html = H.tocHtml(TOC, "sales.invoices");
  assert.equal((html.match(/help-toc-module/g) || []).length, 2); // General, Sales
  assert.match(html, />General</);
  assert.match(html, />Sales</);
  assert.match(html, /class="help-toc-screen active" href="#\/help\/sales.invoices"/);
  assert.match(html, /href="#\/help\/sales.invoices.lines">Lines</);
  assert.doesNotMatch(html, /_intro.find/); // sections of another screen stay closed
});

test("an item shows its code as a link, and the untranslated notice", () => {
  const html = H.itemHtml({ code: "sales.invoices.post", level: 3, title: "Post", html: "<p>Posts.</p>", untranslated: true });
  assert.match(html, /id="help-sales.invoices.post"/);
  assert.match(html, /<h4>Post <span class="badge">Not yet translated<\/span>/);
  assert.match(html, /<a class="help-code" href="#\/help\/sales.invoices.post"/);
  assert.match(html, /<p>Posts.<\/p>/);
});

test("search results show the path and the code, escaped", () => {
  const html = H.resultsHtml({ q: "x", items: [{ code: "sales.invoices.dDate", title: "Date <b>", path: ["Sales invoices", "Header"], snippet: "a < b" }] });
  assert.match(html, /Date &lt;b&gt;/);
  assert.match(html, /Sales invoices › Header/);
  assert.match(html, /a &lt; b/);
  assert.match(H.resultsHtml({ q: "zzz", items: [] }), /Nothing found for “zzz”/);
});

// ------------------------------------------------------------------ coverage of the help
test("every screen of the menu has its help page, or is in the pending list", () => {
  const screens = MENU.flatMap((m) => m.items || []).filter((i) => typeof i === "object").map((i) => i.k);
  const missing = screens.filter((k) => !documented[k]);
  assert.deepEqual(missing, PENDING, "update PENDING in tests/js/help.test.mjs");
});

test("a documented screen documents every field of its forms and every column of its grids", () => {
  const missing = [];
  for (const [key, R] of Object.entries(RES)) {
    const screen = U.screenOf(R);
    if (!documented[screen]) continue;
    const base = U.helpBase(R);
    const codes = [
      ...(R.sections || []).flatMap((s) => s.fields).filter((fd) => fd.f).map((fd) => `${base}.${fd.f}`),
      ...[...(R.lines ? [{ key: "lines", ...R.lines }] : []), ...(R.grids || [])].flatMap((G) => G.cols.map((c) => `${base}.${G.key}.${c.f}`)),
    ];
    missing.push(...codes.filter((c) => !documented[screen].has(c)).map((c) => `${key}: ${c}`));
  }
  assert.deepEqual(missing, [], "write these items in help/en/<screen>.md (and help/fr)");
});

test("the code of a field: the screen, the tab of a tab set, the grid", () => {
  assert.equal(U.helpBase(RES.salesinvoices), "sales.invoices");
  assert.equal(U.helpBase(RES.taxcodes), "admin.taxes");
  assert.equal(U.helpBase(RES.taxgroups), "admin.taxes.taxgroups");
  const grid = { dataset: { grid: "lines" } };
  assert.equal(U.fieldCode("sales.invoices", { dataset: { f: "cCustomer" }, closest: () => null }), "sales.invoices.cCustomer");
  assert.equal(U.fieldCode("sales.invoices", { dataset: { lf: "dQty" }, closest: () => grid }), "sales.invoices.lines.dQty");
  assert.equal(U.fieldCode("sales.invoices", { dataset: {}, closest: () => grid }), null);
});
