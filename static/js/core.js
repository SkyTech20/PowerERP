/* PowerERP: Shared building blocks: i18n (t), formatting, the API client, toasts. */

export const API = "api/";  // relative: works at / and behind a prefix such as /erp/
export const I18N = window.ERP_I18N;
export const $ = (sel, root) => (root || document).querySelector(sel);
export const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

// ------------------------------------------------------------------ i18n
export let lang = "en"; // the UI language: read it anywhere, change it with setLang (login.js)
try {
  lang = localStorage.getItem("erp.lang") || ((navigator.language || "").toLowerCase().startsWith("fr") ? "fr" : "en");
} catch (e) { /* storage unavailable */ }
if (!I18N[lang]) lang = "en";

export function t(key, vars) {
  let s = (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
  if (vars) Object.keys(vars).forEach((k) => { s = s.replace("{" + k + "}", vars[k]); });
  return s;
}

export function esc(v) {
  return String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
export const num = (v) => { const n = parseFloat(String(v == null ? "" : v).replace(",", ".")); return isNaN(n) ? 0 : n; };
// Amount/quantity inputs: drop anything that is not a digit, separator or minus ("$", spaces, letters).
export const numOnly = (el) => {
  const v = el.value, c = v.replace(/[^\d.,-]/g, "");
  if (c !== v) {
    const pos = Math.max(0, (el.selectionStart || 0) - (v.length - c.length));
    el.value = c;
    try { el.setSelectionRange(pos, pos); } catch (e) { /* ignore */ }
  }
  return c;
};
export function money(v, cur) {
  try {
    return new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { style: "currency", currency: cur || "CAD" }).format(num(v));
  } catch (e) { return num(v).toFixed(2) + " " + (cur || ""); }
}
// Quebec sales taxes, charged when the supplier has the matching registration number.
export const TAX_RATES = { tps: 0.05, tvq: 0.09975 };
export const round2 = (v) => Math.round((v + Number.EPSILON) * 100) / 100;
export const fmtInt = (v) => new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA").format(v || 0);

// ------------------------------------------------------------------ API
export async function api(path, opts) {
  opts = opts || {};
  const res = await fetch(API + path, {
    method: opts.method || "GET",
    headers: opts.body ? { "Content-Type": "application/json" } : {},
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch (e) { /* empty body */ }
  if (res.status === 401 && !opts.noAuthRedirect) onUnauthorized();
  if (!res.ok) {
    const err = new Error((data && data.error) || "generic");
    err.code = (data && data.error) || "generic";
    err.field = data && data.field;
    err.status = res.status;
    err.detail = data && data.detail;
    throw err;
  }
  return data;
}

export function toast(msg, kind) {
  const el = document.createElement("div");
  el.className = "toast " + (kind || "");
  el.textContent = msg;
  $("#toasts").appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

export const yesNo = (v) => `<span class="badge ${v ? "yes" : "no"}">${esc(t(v ? "common.yes" : "common.no"))}</span>`;
export const statusBadge = (v) => `<span class="badge ${esc(v)}">${esc(t("status." + v))}</span>`;
export const sourceBadge = (v) => `<span class="badge ${esc(v)}">${esc(t("source." + v))}</span>`;
export const enc = encodeURIComponent;

export const CURRENCIES = ["CAD", "USD", "EUR"];

export function fmtDateTime(v) {
  if (!v) return "—";
  const d = new Date(v);
  if (isNaN(d)) return v;
  return d.toLocaleString(lang === "fr" ? "fr-CA" : "en-CA", { dateStyle: "short", timeStyle: "short" });
}

export function setLangValue(l) { lang = l; }

// what api() does on a 401: login.js sets it to showLogin (a callback, so core.js imports no screen)
export let onUnauthorized = () => {};
export function setUnauthorizedHandler(fn) { onUnauthorized = fn; }
