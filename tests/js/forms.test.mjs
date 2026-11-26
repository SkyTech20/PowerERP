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

for (const f of ["erp.js", "inventory.js", "production.js", "quality.js", "sales.js"]) await import(pathToFileURL(join(STATIC, "js", "resources", f)).href);
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

// The steps of a recipe: a panel with the fields of the kind of the selected step (instead of a grid of 23 columns)
const { stepSections, STEP_KINDS, STEP_DATA_TYPES } = await import(pathToFileURL(join(STATIC, "js", "resources", "production.js")).href);
const recipe = { operations: [{ iOpSeq: 10, cOperation: "MIX" }, { iOpSeq: 20, cOperation: "BAKE" }], materials: [{ iSeq: 10, cComponent: "FLOUR", dQtyPer: "0.5", cUOM: "KG", iOpSeq: 10 }, { iSeq: 20, cComponent: "SALT", dQtyPer: "0.01", cUOM: "KG", iOpSeq: 20 }] };
const step = (over) => ({ iOpSeq: 10, iStep: 10, cKind: "instruction", cDataType: "number", cFrequency: "once", lCritical: false, ...over });
const shown = (s) => stepSections(s, recipe).flatMap((x) => x.fields).map((f) => f.f);

test("each step kind shows only the fields it uses", () => {
  const common = ["iOpSeq", "iStep", "cKind", "cTitleFR", "cTitleEN", "cInstructionFR", "cInstructionEN", "cAttachmentUrl", "cFrequency", "cCondition"];
  const own = (s) => shown(s).filter((f) => !common.includes(f));
  assert.deepEqual(own(step({ cKind: "instruction" })), ["lSecondSignature"]);
  assert.deepEqual(own(step({ cKind: "output" })), ["lSecondSignature"]);
  assert.deepEqual(own(step({ cKind: "material_add" })), ["iMaterialSeq", "lSecondSignature"]);
  assert.deepEqual(own(step({ cKind: "timer" })), ["dDurationMin", "lSecondSignature"]);
  assert.deepEqual(own(step({ cKind: "signature" })), ["cRequiredRole"]); // the second signature is the step itself
  assert.deepEqual(own(step({ cKind: "check" })), ["cParam", "lRequired", "lCritical", "lSecondSignature"]);
  assert.deepEqual(own(step({ cKind: "measure" })), ["cParam", "cDataType", "lRequired", "cUOM", "dMin", "dTarget", "dMax", "lCritical", "lSecondSignature"]);
  assert.deepEqual(own(step({ cKind: "parameter", cDataType: "list" })), ["cParam", "cDataType", "lRequired", "cOptions", "lCritical", "lSecondSignature"]);
  assert.deepEqual(own(step({ cKind: "measure", cDataType: "text", lCritical: true })), ["cParam", "cDataType", "lRequired", "lCritical", "cOnFail", "lSecondSignature"]);
  assert.ok(shown(step({ cFrequency: "every_n_units" })).includes("dFrequencyValue"));
  assert.ok(!shown(step({ cFrequency: "per_lot" })).includes("dFrequencyValue"));
});

test("every field of a step is shown for some kind", () => {
  const all = new Set();
  for (const cKind of STEP_KINDS) {
    for (const cDataType of STEP_DATA_TYPES) {
      for (const cFrequency of ["once", "every_n_min"]) shown(step({ cKind, cDataType, cFrequency, lCritical: true })).forEach((f) => all.add(f));
    }
  }
  const fields = ["iOpSeq", "iStep", "cKind", "cTitleFR", "cTitleEN", "cInstructionFR", "cInstructionEN", "cAttachmentUrl", "dDurationMin", "cParam", "cDataType", "cUOM",
    "dTarget", "dMin", "dMax", "cOptions", "lRequired", "lCritical", "cOnFail", "cFrequency", "dFrequencyValue", "iMaterialSeq", "cRequiredRole", "lSecondSignature", "cCondition"];
  assert.deepEqual(fields.filter((f) => !all.has(f)), []);
});

test("an added material lists the materials of the operation of the step", () => {
  const mat = (s) => stepSections(s, recipe).flatMap((x) => x.fields).find((f) => f.f === "iMaterialSeq").options.map(([v]) => v);
  assert.deepEqual(mat(step({ cKind: "material_add", iOpSeq: 10 })), ["0", "10"]);
  assert.deepEqual(mat(step({ cKind: "material_add", iOpSeq: 20 })), ["0", "20"]);
});

test("a step refused on save opens on its field", () => {
  const { detail } = RES.recipes.grids.find((G) => G.key === "steps");
  const rows = [step({ iOpSeq: 20, iStep: 10 }), step({ iOpSeq: 10, iStep: 20 })];
  assert.deepEqual(detail.errorAt("op 10 step 20: cParam", rows, "required"), { i: 1, f: "cParam" });
  assert.deepEqual(detail.errorAt("op 20 step 10", rows, "max_below_min"), { i: 0, f: "dMax" });
  assert.deepEqual(detail.errorAt("op 10 step 20: TEMP", rows, "invalid_condition"), { i: 1, f: "cCondition" });
  assert.deepEqual(detail.errorAt("op 10 step 20: material 30", rows, "unknown_ref"), { i: 1, f: "iMaterialSeq" });
  assert.deepEqual(detail.errorAt("op 10 step 20: TEMP", rows, "duplicate"), { i: 1, f: "cParam" });
  assert.equal(detail.errorAt("something else", rows, "required"), null);
  assert.deepEqual(detail.order(rows), [1, 0]);
});

test("the labels and helps of the step panel have an English and a French text", () => {
  const missing = new Set();
  for (const cKind of STEP_KINDS) {
    for (const cFrequency of ["once", "every_n_units", "every_n_min"]) {
      for (const s of stepSections(step({ cKind, cFrequency, cDataType: "list", lCritical: true }), recipe)) {
        const keys = [s.t, s.help, ...s.fields.flatMap((f) => [f.l, f.help, ...(f.options && !f.raw ? f.options.map(([, l]) => l) : [])])];
        keys.filter(Boolean).forEach((k) => ["en", "fr"].forEach((l) => { if (!(k in I18N[l])) missing.add(`${l}: ${k}`); }));
      }
    }
  }
  assert.deepEqual([...missing].sort(), []);
});

test("every screen opens from a menu entry (its permissions are the entry's)", async () => {
  const { menuItemOf } = await import(pathToFileURL(join(STATIC, "js", "menu.js")).href);
  for (const [key, R] of Object.entries(RES)) {
    const item = menuItemOf(R);
    assert.ok(item, `${key}: no menu entry for ${R.menu || R.route}`);
  }
  assert.equal(menuItemOf(RES.taxgroups).k, "admin.taxes");
  assert.equal(menuItemOf(RES.locations).k, "inv.warehouses");
  assert.equal(menuItemOf(RES.calexceptions).k, "prod.calendars");
  assert.equal(menuItemOf(RES.users).admin, true);
});

test("a production order: another product takes its own recipe and warehouse; every status has its texts", async () => {
  const P = await import(pathToFileURL(join(STATIC, "js", "resources", "production.js")).href);
  const m = { cProduct: "B", cRevision: "A", cWarehouse: "W1", dQty: "5" };
  assert.deepEqual(P.prepareOrderRecalc({ ...m }, "dQty"), m);
  assert.deepEqual(P.prepareOrderRecalc({ ...m }, "cProduct"), { ...m, cRevision: "", cWarehouse: "" });
  const keys = [...P.ORDER_STATUS.map((s) => "prod.ord.status." + s), ...["created", "release", "unrelease", "cancel", "start", "complete", "reopen", "close"].map((a) => "prod.ord.a." + a),
    ...["issue", "backflush", "return"].map((k) => "prod.fl.k." + k)];
  for (const l of ["en", "fr"]) assert.deepEqual(keys.filter((k) => !I18N[l][k]), [], l);
  assert.equal(RES.prodorders.locked({ cStatus: "draft" }, false), false);
  assert.equal(RES.prodorders.locked({ cStatus: "released" }, false), true);
});
