/* PowerERP: Code / label lists of the select fields (/api/lookups/<kind>), cached per form. */
import { api, enc, esc, lang } from "./core.js";
import { lookupCache } from "./state.js";

// ------------------------------------------------------------------ Lookups
// Lookup fields are plain <select>s filled with the whole list (code — label); the list is fetched
// once per open form. A value missing from the list (old data) is kept as its own option.
export function lookupRows(kind, params) {
  const extra = params ? Object.entries(params).map(([k, v]) => "&" + k + "=" + enc(v == null ? "" : v)).join("") : "";
  const key = kind + extra;
  if (!lookupCache[key]) lookupCache[key] = api("lookups/" + kind + "?all=1&lang=" + lang + extra).catch(() => { delete lookupCache[key]; return []; });
  return lookupCache[key];
}
export function lookupOptions(rows, value) {
  const v = value == null ? "" : String(value);
  const known = !v || rows.some((r) => r.code === v);
  return `<option value=""></option>${known ? "" : `<option value="${esc(v)}" selected>${esc(v)}</option>`}`
    + rows.map((r) => `<option value="${esc(r.code)}" ${r.code === v ? "selected" : ""}>${esc(r.code)}${r.label ? " — " + esc(r.label) : ""}</option>`).join("");
}
// Fills the select and calls onPick(code, label) on change. Returns a refresh function that reloads the
// list when the params (e.g. the warehouse of a location) have changed.
export function bindLookup(sel, kind, onPick, params) {
  let rows = [];
  let lastKey = null;
  const fill = async () => {
    const p = params ? params() : null;
    const key = JSON.stringify(p);
    if (key === lastKey) return;
    lastKey = key;
    rows = await lookupRows(kind, p);
    const v = sel.value;
    sel.innerHTML = lookupOptions(rows, v);
    sel.value = v;
  };
  fill();
  sel.addEventListener("change", () => {
    const r = rows.find((x) => x.code === sel.value);
    if (onPick) onPick(sel.value, r ? r.label : "");
  });
  return fill;
}
