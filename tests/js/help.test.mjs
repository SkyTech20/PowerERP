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
