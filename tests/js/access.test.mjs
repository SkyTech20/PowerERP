// Access levels of the Roles screen (static/js/access.js). Run from the PowerERP folder: node --test tests/js/
import assert from "node:assert/strict";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const STATIC = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "static");
const A = await import(pathToFileURL(join(STATIC, "js", "access.js")).href);

const CRUD = ["view", "create", "edit", "delete"];
const INVOICES = [...CRUD, "post", "credit", "print"];

test("levels give the expected actions", () => {
  assert.deepEqual(A.actionsOf("view", INVOICES), ["view", "print"]);
  assert.deepEqual(A.actionsOf("edit", INVOICES), ["view", "create", "edit", "print"]);
  assert.deepEqual(A.actionsOf("full", INVOICES), INVOICES);
  assert.deepEqual(A.actionsOf("none", INVOICES), []);
});

test("a screen offers only the levels that differ", () => {
  assert.deepEqual(A.levelsOf(["view"]), ["none", "view"]);
  assert.deepEqual(A.levelsOf(["view", "create_po"]), ["none", "view", "full"]);
  assert.deepEqual(A.levelsOf(CRUD), ["none", "view", "edit", "full"]);
});

test("level of a set of actions", () => {
  assert.equal(A.levelOf([], CRUD), "none");
  assert.equal(A.levelOf(["view"], CRUD), "view");
  assert.equal(A.levelOf(["edit", "view", "create"], CRUD), "edit");
  assert.equal(A.levelOf(CRUD, CRUD), "full");
  assert.equal(A.levelOf(["view", "delete"], CRUD), "custom");
  assert.equal(A.levelOf([...CRUD, "post", "print"], INVOICES), "custom"); // no credit note
  assert.equal(A.levelOf(["view"], ["view"]), "view"); // view-only screen: view is also full
  assert.equal(A.levelOf(["view", "create_po"], ["view", "create_po"]), "full");
});

test("an action brings its view, no view takes every action", () => {
  assert.deepEqual(A.toggleAction([], "post", true).sort(), ["post", "view"]);
  assert.deepEqual(A.toggleAction(["view", "post"], "view", false), []);
  assert.deepEqual(A.toggleAction(["view", "post"], "post", false), ["view"]);
});

test("permissions <-> map, and the summary of a module", () => {
  const catalog = [{ cScreen: "s.a", actions: CRUD }, { cScreen: "s.b", actions: ["view"] }];
  const map = A.byScreen(["s.b:view", "s.a:edit", "s.a:view"]);
  assert.deepEqual(A.toPermissions(map, catalog), ["s.a:view", "s.a:edit", "s.b:view"]);
  assert.deepEqual(A.moduleSummary({}, catalog), { level: "none" });
  assert.deepEqual(A.moduleSummary({ "s.a": CRUD, "s.b": ["view"] }, catalog), { level: "full" });
  assert.deepEqual(A.moduleSummary(map, catalog), { open: 2, total: 2 });
});
