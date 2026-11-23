// The screen definitions (static/js/resources): checks that need no browser.
// Run from the PowerERP folder: node --test tests/js/
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import vm from "node:vm";

const STATIC = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "static");

// The translations, loaded as the page does (i18n.js first, then the module files)
globalThis.window = { addEventListener() {} };
const files = readdirSync(STATIC).filter((f) => /^i18n.*\.js$/.test(f)).sort((a, b) => (a === "i18n.js" ? -1 : b === "i18n.js" ? 1 : a.localeCompare(b)));
for (const f of files) vm.runInThisContext(readFileSync(join(STATIC, f), "utf-8"), { filename: f });
globalThis.localStorage = { getItem: () => null, setItem() {} };
const I18N = globalThis.window.ERP_I18N;

for (const f of ["erp.js", "inventory.js", "production.js"]) await import(pathToFileURL(join(STATIC, "js", "resources", f)).href);
const { RES } = await import(pathToFileURL(join(STATIC, "js", "registry.js")).href);

const fieldsOf = (R) => (R.sections || []).flatMap((s) => s.fields);
const gridsOf = (R) => [...(R.lines ? [{ key: "lines", ...R.lines }] : []), ...(R.grids || [])];
const defaultsOf = (R) => (typeof R.defaults === "function" ? R.defaults() : { ...(R.defaults || {}) });

test("a new line proposes no code that may not exist", () => {
  // e.g. the downtime reason "PM" of a new planned stop: refused on save once the demo data is cleared
  for (const [key, R] of Object.entries(RES)) {
    for (const G of gridsOf(R)) {
      if (!G.newLine) continue;
      const model = defaultsOf(R);
      model[G.key] = model[G.key] || [];
      const line = G.newLine(model);
      for (const c of G.cols.filter((x) => x.lookup)) {
        const v = line[c.f] == null ? "" : String(line[c.f]);
        assert.ok(v === "" || v === "*", `${key}.${G.key}.${c.f} = ${v}`);
      }
    }
  }
});

test("codes listed from the values already typed can be typed freely", () => {
  // the payment terms and buyers are the values used on other suppliers: an empty database has none to pick
  const typed = ["terms", "buyers"];
  for (const [key, R] of Object.entries(RES)) {
    for (const fd of fieldsOf(R).filter((x) => typed.includes(x.lookup))) assert.ok(fd.free, `${key}.${fd.f}`);
  }
});

test("every label, title and help of the forms has an English and a French text", () => {
  const missing = new Set();
  const need = (k) => { if (k && k.includes(".")) ["en", "fr"].forEach((l) => { if (!(k in I18N[l])) missing.add(`${l}: ${k}`); }); };
  for (const R of Object.values(RES)) {
    [R.title, R.sub, R.one, R.newTitle].forEach(need);
    (R.sections || []).forEach((s) => { need(s.t); need(s.help); s.fields.forEach((fd) => { need(fd.l); need(fd.help); if (fd.options && !fd.raw) fd.options.forEach(([, l]) => need(l)); }); });
    gridsOf(R).forEach((G) => { need(G.title); need(G.help); G.cols.forEach((c) => { need(c.l); if (c.options && !c.rawOpt) c.options.forEach(([, l]) => need(l)); }); });
    (R.columns || []).forEach((c) => need(c.l));
    (R.filters || []).forEach((f) => { need(f.l); (f.options || []).forEach(([, l]) => need(l)); });
    (R.formTabs || []).forEach(([, l]) => need(l));
    (R.actions || []).forEach((a) => { need(a.l); need(a.confirm); need(a.done); });
  }
  assert.deepEqual([...missing].sort(), []);
});
