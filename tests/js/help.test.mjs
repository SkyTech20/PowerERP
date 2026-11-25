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
const PENDING = [];

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

test("a section is a heading; its fields are one list of definitions, each with a link button", () => {
  const html = H.itemsHtml([
    { code: "sales.invoices.header", level: 2, title: "Header", html: "" },
    { code: "sales.invoices.cCustomer", level: 3, title: "Customer", html: "<p>The customer.</p>" },
    { code: "sales.invoices.dDate", level: 3, title: "Date", html: "<p>Date.</p>", untranslated: true },
    { code: "sales.invoices.post", level: 2, title: "Post", html: "<p>Posts.</p>" },
  ]);
  assert.equal((html.match(/<dl class="help-fields">/g) || []).length, 1);
  assert.match(html, /<h2 class="help-h2" id="help-sales.invoices.header">Header/);
  assert.match(html, /<div class="help-field" id="help-sales.invoices.cCustomer"><dt>Customer/);
  assert.match(html, /<dt>Date <span class="badge">Not yet translated<\/span>/);
  assert.match(html, /data-copy-help="sales.invoices.post"/);
  assert.match(html, /<\/dl><h2 class="help-h2" id="help-sales.invoices.post">/);
});

test("search results show the path, escaped, with the words marked", () => {
  const html = H.resultsHtml({ q: "date", items: [{ code: "sales.invoices.dDate", title: "Date <b>", path: ["Sales invoices", "Header"], snippet: "a < b, the date" }] });
  assert.match(html, /<mark>Date<\/mark> &lt;b&gt;/);
  assert.match(html, /Sales invoices › Header/);
  assert.match(html, /a &lt; b, the <mark>date<\/mark>/);
  assert.match(H.resultsHtml({ q: "zzz", items: [] }), /Nothing found for “zzz”/);
  assert.equal(H.mark("a.b", "."), "a.b"); // one-letter words are not marked
});

test("the home page has a card per screen, and a screen opens from its help", () => {
  const html = H.cardsHtml({ screens: [{ screen: "_intro", title: "Using" }, { screen: "sales.invoices", title: "Sales invoices", summary: "Invoices." }] });
  assert.match(html, /<h2 class="help-h2">Sales<\/h2>/);
  assert.match(html, /<a class="help-card" href="#\/help\/sales.invoices"><b>Sales invoices<\/b>/);
  assert.doesNotMatch(html, /Using/);
  assert.equal(H.screenRoute("sales.invoices"), "/sales/invoices");
  assert.equal(H.screenRoute("_intro"), "");
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

test("an input that is not a field of the record has its code in data-help-f", () => {
  assert.equal(U.fieldCode("sales.customers", { dataset: { helpF: "check.cProduct" }, closest: () => null }), "sales.customers.check.cProduct");
  assert.equal(U.fieldCode("admin.roles", { dataset: { helpF: "cCode", f: "x" }, closest: () => null }), "admin.roles.cCode");
});

const PROD_PANELS = {
  week: ["prod.calendars", "prod.workcenters", "prod.resources"], calc: ["prod.operations"], grid: ["prod.setupmatrix"],
  explode: ["prod.recipes"], preview: ["prod.recipes"], versions: ["prod.recipes"], floor: ["prod.orders"],
};

test("the inputs of the hand-written screens and panels are documented (data-help-f)", async () => {
  const { COMPANY_FIELDS } = await import(pathToFileURL(join(STATIC, "js", "screens", "settings.js")).href);
  const helpF = (file) => [...readFileSync(join(STATIC, "js", file), "utf-8").matchAll(/data-help-f="([A-Za-z.]+)"/g)].map((m) => m[1]);
  const codes = [
    ...COMPANY_FIELDS.map(([f]) => `admin.settings.${f}`), "admin.settings.scenario",
    ...helpF("screens/roles.js").map((f) => `admin.roles.${f}`),
    ...helpF("resources/sales.js").map((f) => `sales.customers.${f}`),
    ...helpF("screens/backups.js").map((f) => `admin.backups.${f}`),
    ...helpF("resources/inventory.js").map((f) => `admin.taxes.taxgroups.${f}`), // the "Try the group" panel
    // the panels of Production: the week preview is on three screens, the others on one
    ...helpF("resources/production.js").flatMap((f) => PROD_PANELS[f.split(".")[0]].map((s) => `${s}.${f}`)),
  ];
  assert.ok(codes.length > 20);
  const missing = codes.filter((c) => !documented[c.split(".").slice(0, 2).join(".")]?.has(c));
  assert.deepEqual(missing, []);
});
