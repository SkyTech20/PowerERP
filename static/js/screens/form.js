/* PowerERP: Generic form screen of a resource (create / edit). */
import { $, $$, TAX_RATES, api, enc, esc, money, num, numOnly, round2, sourceBadge, t, toast } from "../core.js";
import { bindLookup, lookupOptions } from "../lookups.js";
import { RES } from "../registry.js";
import { clearLookups, prefill, setPrefill } from "../state.js";
import { pageHead, tabLabel } from "../views.js";

// ---------- Generic form
// Field options: req, reqNew, key (read-only once saved), readonly, type (text | number | date | select | check |
// textarea | password | email), lookup (+ fill, lookupParams, onPick), show(model, isNew), rerender (redraw on change).
// Resource options: lines, totals, tax, locked(model, isNew), actions, panel { html(model), bind(model) }.
export function formView(key, id) {
  const R = RES[key];
  const isNew = id == null;
  let model = null;
  let errors = {};
  let missing = false;
  let locked = false;
  let activeTab = R.formTabs ? R.formTabs[0][0] : null; // R.formTabs: sections shown as tabs
  let refreshers = []; // lookups whose list depends on other fields
  clearLookups();
  let taxInfo = null; // { code, tps, tvq } of the supplier, when R.tax
  let taxLive = isNew; // existing records keep their stored taxes until something is changed

  const cur = () => (R.currency ? R.currency(model) : "CAD");
  const visible = (fd) => !fd.show || fd.show(model, isNew);

  // Load the supplier's TPS / TVQ numbers and recompute the taxes.
  async function loadSupplierTax(code) {
    code = String(code || "").trim();
    if (!R.tax || (taxInfo && taxInfo.code === code)) return;
    taxInfo = { code, tps: false, tvq: false };
    if (code) {
      try {
        const sup = await api("suppliers/" + enc(code));
        taxInfo = { code, tps: !!String(sup.cNoTPS || "").trim(), tvq: !!String(sup.cNoTVQ || "").trim() };
      } catch (e) { /* unknown supplier: no taxes */ }
    }
    if ($("#totals")) refreshAmounts();
  }

  function applyTaxes() {
    if (!R.tax || !taxInfo || !taxLive) return;
    const base = (model.lines || []).reduce((s, l) => s + R.lines.amount(l), 0) + num(model[R.tax.freight]);
    model[R.tax.tps] = (taxInfo.tps ? round2(base * TAX_RATES.tps) : 0).toFixed(2);
    model[R.tax.tvq] = (taxInfo.tvq ? round2(base * TAX_RATES.tvq) : 0).toFixed(2);
  }

  function fieldHtml(fd) {
    if (!visible(fd)) return "";
    const v = model[fd.f];
    const ro = locked || fd.readonly || (fd.key && !isNew);
    const required = !locked && (fd.req || (fd.reqNew && isNew));
    const label = `<label for="f-${fd.f}">${esc(t(fd.l))}${required ? '<span class="req">*</span>' : ""}</label>`;
    const err = errors[fd.f] ? `<span class="err">${esc(t("err." + errors[fd.f]))}</span>` : "";
    const help = fd.help ? `<span class="help">${esc(t(fd.help))}</span>` : "";
    const cls = `field ${fd.span === 4 ? "span-4" : fd.span >= 2 ? "span-2" : ""} ${errors[fd.f] ? "invalid" : ""}`;
    if (fd.type === "check") {
      return `<div class="${cls}"><label class="check"><input type="checkbox" id="f-${fd.f}" data-f="${fd.f}" ${v ? "checked" : ""} ${ro ? "disabled" : ""}> ${esc(t(fd.l))}</label>${help}${err}</div>`;
    }
    let input;
    const blank = (x) => (x == null ? "" : String(x));
    if (fd.lookup && !ro) {
      input = `<select id="f-${fd.f}" data-f="${fd.f}">${lookupOptions([], v)}</select>`;
    } else if (fd.suggestions && !ro) {
      const opts = ["", ...fd.suggestions, ...(blank(v) && !fd.suggestions.includes(blank(v)) ? [blank(v)] : [])];
      input = `<select id="f-${fd.f}" data-f="${fd.f}">${opts.map((o) => `<option value="${esc(o)}" ${blank(v) === o ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>`;
    } else if (fd.type === "select") {
      input = `<select id="f-${fd.f}" data-f="${fd.f}" ${ro ? "disabled" : ""}>${fd.options.map(([ov, ol]) => `<option value="${esc(ov)}" ${String(v == null ? "" : v) === ov ? "selected" : ""}>${esc(fd.raw ? ol : t(ol))}</option>`).join("")}</select>`;
    } else if (fd.type === "textarea") {
      input = `<textarea id="f-${fd.f}" data-f="${fd.f}" ${ro ? "readonly" : ""}>${esc(v)}</textarea>`;
    } else {
      const type = ["date", "time", "password", "email"].includes(fd.type) ? fd.type : "text";
      const auto = fd.type === "password" ? 'autocomplete="new-password"' : fd.autocomplete ? `autocomplete="${fd.autocomplete}"` : "";
      const mode = fd.type === "number" ? 'inputmode="decimal" style="text-align:right"' : fd.inputmode ? `inputmode="${fd.inputmode}"` : "";
      input = `<input type="${type}" id="f-${fd.f}" data-f="${fd.f}" value="${esc(v)}" ${ro ? "readonly" : ""} ${auto} ${mode}>`;
    }
    return `<div class="${cls}">${label}${input}${help}${err}</div>`;
  }

  function lineCell(c, ln) {
    const ro = locked || c.ro;
    const aria = `aria-label="${esc(c.raw ? c.l : t(c.l))}"`;
    if (c.type === "check") return `<input type="checkbox" data-lf="${c.f}" ${ln[c.f] ? "checked" : ""} ${ro ? "disabled" : ""} ${aria}>`;
    if (c.type === "select") {
      return `<select data-lf="${c.f}" ${ro ? "disabled" : ""} ${aria}>${c.options.map(([ov, ol]) => `<option value="${esc(ov)}" ${String(ln[c.f] == null ? "" : ln[c.f]) === ov ? "selected" : ""}>${esc(c.rawOpt ? ol : t(ol))}</option>`).join("")}</select>`;
    }
    if (c.lookup && !ro) return `<select data-lf="${c.f}" data-lookup="${c.lookup}" ${aria}>${lookupOptions([], ln[c.f])}</select>`;
    return `<input type="${c.type === "date" || c.type === "time" ? c.type : "text"}" data-lf="${c.f}" value="${esc(ln[c.f])}" ${c.n ? 'inputmode="decimal" data-num="1" style="text-align:right"' : ""} ${ro ? "readonly" : ""} ${aria}>`;
  }

  function linesHtml() {
    const L = R.lines;
    const head = L.cols.map((c) => `<th class="${c.n ? "num" : ""}">${esc(c.raw ? c.l : t(c.l))}</th>`).join("")
      + (L.amount ? `<th class="num">${esc(t(L.amountLabel))}</th>` : "") + (locked ? "" : "<th></th>");
    const body = (model.lines || []).map((ln, i) => `<tr data-line="${i}" class="${L.rowClass ? L.rowClass(ln) : ""}">${L.cols.map((c) => `<td class="${c.w}">${lineCell(c, ln)}</td>`).join("")}
      ${L.amount ? `<td class="num" data-amount>${esc(money(L.amount(ln), cur()))}</td>` : ""}
      ${locked ? "" : `<td><button type="button" class="link-btn" data-remove="${i}" title="${esc(t("common.removeLine"))}">✕</button></td>`}</tr>`).join("");
    const addBtn = locked ? "" : `<button type="button" class="btn small" id="addLine" style="margin-left:auto">＋ ${esc(t("common.addLine"))}</button>`;
    return `<div class="card"><div class="card-head"><h2>${esc(t(L.title || "common.lines"))}</h2>${L.help ? `<span class="help muted">${esc(t(L.help))}</span>` : ""}${addBtn}</div>
      <div class="table-wrap"><table class="grid lines"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>
      ${(model.lines || []).length ? "" : `<div class="empty">${esc(t("common.noLines"))}</div>`}</div>
      ${R.totals ? '<div class="totals" id="totals"></div>' : ""}</div>`;
  }

  function totalsHtml() {
    const T = R.totals;
    applyTaxes();
    const isTax = (f) => R.tax && (f === R.tax.tps || f === R.tax.tvq);
    const sub = (model.lines || []).reduce((s, l) => s + R.lines.amount(l), 0);
    const total = sub + T.extras.reduce((s, f) => s + num(model[f]), 0);
    return `<table><tr><td>${esc(t("f." + T.sub))}</td><td>${esc(money(sub, cur()))}</td></tr>
      ${T.extras.map((f) => `<tr><td><label for="t-${f}">${esc(t("f." + f))}</label></td><td><input type="text" id="t-${f}" data-f="${f}" inputmode="decimal" value="${esc(model[f])}" ${isTax(f) ? "readonly" : ""}></td></tr>`).join("")}
      <tr class="grand"><td>${esc(t("f." + T.total))}</td><td>${esc(money(total, cur()))}</td></tr></table>
      ${R.tax ? `<p class="help tax-note">${esc(t("common.taxAuto"))}</p>` : ""}`;
  }

  function refreshAmounts() {
    if (!R.lines) return;
    if (R.lines.amount) {
      $$("tr[data-line]").forEach((tr) => {
        const ln = model.lines[+tr.dataset.line];
        $("[data-amount]", tr).textContent = money(R.lines.amount(ln), cur());
      });
    }
    const totals = $("#totals");
    if (!totals) return;
    const focused = document.activeElement && document.activeElement.id;
    const caret = focused && document.activeElement.selectionStart;
    totals.innerHTML = totalsHtml();
    bindTotals();
    if (focused && focused.startsWith("t-")) { const el = $("#" + focused); el.focus(); try { el.setSelectionRange(caret, caret); } catch (e) { /* ignore */ } }
  }

  function bindTotals() {
    $$("#totals input[data-f]").forEach((el) => el.addEventListener("input", () => { model[el.dataset.f] = numOnly(el); taxLive = true; refreshAmounts(); }));
  }

  async function fillFromPo(po) {
    if (!po) return;
    try {
      const p = await api("purchase-orders/" + enc(po));
      if (!model.CodeFournisseur) { model.CodeFournisseur = p.cSupplierCode; model.Fournisseur = p.cSupplierName; }
      if (!(model.lines || []).some((l) => l.CodeArticle || l.Description)) {
        model.lines = p.lines.map((l) => ({ CodeArticle: l.cProductcode, Description: l.cProductDesc, QuantiteCommandee: l.dQuantity, QuantiteRecue: l.dQuantity, PrixUnitaire: l.dUnitCost }));
      }
      taxLive = true;
      render();
      if (R.tax) loadSupplierTax(model[R.tax.supplier]);
    } catch (e) { /* unknown PO: leave the form as typed */ }
  }

  function render() {
    if (missing) {
      $("#view").innerHTML = pageHead(t(R.one), "", `<a class="btn" href="#${R.route}">← ${esc(t("common.back"))}</a>`) + `<div class="card"><div class="empty">${esc(t("common.notFound"))}</div></div>`;
      return;
    }
    locked = !!(R.locked && R.locked(model, isNew));
    const title = isNew ? t(R.newTitle) : `${t(R.one)} ${R.label(model)}`;
    const crumbs = `<a href="#${R.route}">${esc(t(R.title))}</a>${R.tabset ? " / " + esc(tabLabel(R)) : ""}`;
    const extra = (R.actions || []).filter((a) => !a.show || a.show(model, isNew))
      .map((a) => `<button class="btn ${a.primary ? "primary" : ""}" data-action="${a.id}">${esc(t(a.l))}</button>`).join("");
    const actions = locked
      ? `<a class="btn" href="#${R.route}">← ${esc(t("common.back"))}</a>${extra}`
      : `<a class="btn" href="#${R.route}">${esc(t("common.cancel"))}</a>
      ${isNew || R.noDelete ? "" : `<button class="btn danger" id="deleteBtn">${esc(t("common.delete"))}</button>`}
      ${extra}<button class="btn primary" id="saveBtn">${esc(t("common.save"))}</button>`;
    const badge = R.badge ? R.badge(model, isNew) : (!isNew && model.cSource ? sourceBadge(model.cSource) : "");
    // Tabs: each section / the lines / the panel says its tab; the tab with an error is opened
    const tabOf = (x) => (R.formTabs ? x.tab || R.formTabs[0][0] : null);
    const wrap = (tab, html) => (R.formTabs && html ? `<div class="ftab" data-tab="${tab}" ${tab === activeTab ? "" : "hidden"}>${html}</div>` : html);
    const tabHasError = (k) => R.sections.some((s) => tabOf(s) === k && s.fields.some((fd) => errors[fd.f]));
    if (R.formTabs && Object.keys(errors).length) {
      const bad = R.sections.find((s) => s.fields.some((fd) => errors[fd.f]));
      if (bad) activeTab = tabOf(bad); else if (errors.lines && R.lines) activeTab = tabOf(R.lines);
    }
    const sections = R.sections.map((s, i) => {
      const fields = s.fields.map(fieldHtml).join("");
      if (!fields) return "";
      return wrap(tabOf(s), `<div class="card"><div class="card-head"><h2>${esc(t(s.t))}</h2>${i === 0 ? badge : ""}</div>
        <div class="card-body">${s.help ? `<p class="help muted section-help">${esc(t(s.help))}</p>` : ""}<div class="form-grid">${fields}</div></div></div>`);
    }).join("");
    const lines = R.lines && (!R.lines.show || R.lines.show(model, isNew)) ? wrap(tabOf(R.lines), linesHtml()) : "";
    const panel = R.panel && !isNew ? wrap(tabOf(R.panel), R.panel.html(model)) : "";
    const present = (sections + lines + panel).match(/data-tab="[^"]+"/g) || [];
    if (R.formTabs && present.length && !present.includes(`data-tab="${activeTab}"`)) activeTab = R.formTabs[0][0];
    const tabBar = R.formTabs ? `<div class="tabs form-tabs" role="tablist">${R.formTabs.filter(([k]) => present.includes(`data-tab="${k}"`))
      .map(([k, l]) => `<a href="#" role="tab" data-ftab="${k}" class="${k === activeTab ? "active" : ""}">${esc(t(l))}${tabHasError(k) ? ' <span class="req">●</span>' : ""}</a>`).join("")}</div>` : "";
    $("#view").innerHTML = pageHead(title, R.sub2 ? R.sub2(model, isNew) : "", actions, crumbs)
      + tabBar + `<form id="form" novalidate>${sections}${lines}</form>${panel}`;
    $$("[data-ftab]").forEach((a) => a.addEventListener("click", (e) => {
      e.preventDefault();
      activeTab = a.dataset.ftab;
      $$("[data-ftab]").forEach((x) => x.classList.toggle("active", x === a));
      $$(".ftab").forEach((d) => { d.hidden = d.dataset.tab !== activeTab; });
    }));
    if ($("#totals")) { $("#totals").innerHTML = totalsHtml(); bindTotals(); }
    bind();
    if (R.panel && R.panel.bind && !isNew) R.panel.bind(model);
    if (R.tax && model[R.tax.supplier]) loadSupplierTax(model[R.tax.supplier]);
  }

  function bind() {
    refreshers = [];
    const refresh = () => refreshers.forEach((f) => f());
    const allFields = R.sections.flatMap((s) => s.fields);
    allFields.forEach((fd) => {
      const el = $(`[data-f="${fd.f}"]`, $("#form"));
      if (!el) return;
      const update = () => {
        model[fd.f] = fd.type === "check" ? el.checked : fd.int ? parseInt(el.value, 10) : fd.type === "number" ? numOnly(el) : el.value;
        if (fd.f === "cDevise" || fd.f === "Devise") refreshAmounts();
        if (fd.rerender) render(); else refresh();
      };
      el.addEventListener(fd.type === "check" || el.tagName === "SELECT" ? "change" : "input", update);
      if (fd.lookup && el.tagName === "SELECT") {
        const fill = bindLookup(el, fd.lookup, (code, label) => {
          model[fd.f] = code;
          if (fd.fill && label) {
            model[fd.fill] = label;
            const target = $(`[data-f="${fd.fill}"]`);
            if (target) target.value = label;
          }
          if (fd.onPick === "fillFromPo") fillFromPo(code);
          if (R.tax && fd.f === R.tax.supplier) { taxLive = true; loadSupplierTax(code); }
        }, fd.lookupParams ? () => fd.lookupParams(model) : null);
        if (fd.lookupParams) refreshers.push(fill);
      }
    });
    if (R.lines) {
      $$("tr[data-line]").forEach((tr) => {
        const ln = model.lines[+tr.dataset.line];
        $$("[data-lf]", tr).forEach((el) => {
          const col = R.lines.cols.find((c) => c.f === el.dataset.lf) || {};
          if (el.type === "checkbox" || el.tagName === "SELECT") {
            el.addEventListener("change", () => { ln[el.dataset.lf] = el.type === "checkbox" ? el.checked : el.value; });
          } else {
            el.addEventListener("input", () => { ln[el.dataset.lf] = el.dataset.num ? numOnly(el) : el.value; taxLive = true; refreshAmounts(); });
          }
          if (el.dataset.lookup) {
            const fill = bindLookup(el, el.dataset.lookup, (code, label) => {
              ln[el.dataset.lf] = code;
              if (col.fill && label) {
                ln[col.fill] = label;
                const target = $(`[data-lf="${col.fill}"]`, tr);
                if (target) target.value = label;
              }
            }, col.lookupParams ? () => col.lookupParams(model) : null);
            if (col.lookupParams) refreshers.push(fill);
          }
        });
      });
      $$("[data-remove]").forEach((b) => b.addEventListener("click", () => { model.lines.splice(+b.dataset.remove, 1); taxLive = true; render(); }));
      const add = $("#addLine");
      if (add) {
        add.addEventListener("click", () => {
          model.lines = model.lines || [];
          model.lines.push(R.lines.newLine ? R.lines.newLine(model) : {});
          render();
          const rows = $$("tr[data-line]");
          const first = rows.length && $("input[data-lf]:not([data-lf=cUnique]):not([readonly])", rows[rows.length - 1]);
          if (first) first.focus();
        });
      }
    }
    $("#form").addEventListener("submit", (e) => { e.preventDefault(); if (!locked) save(); });
    const sv = $("#saveBtn");
    if (sv) sv.addEventListener("click", save);
    const del = $("#deleteBtn");
    if (del) del.addEventListener("click", remove);
    $$("[data-action]").forEach((b) => b.addEventListener("click", async () => {
      const a = R.actions.find((x) => x.id === b.dataset.action);
      if (a.confirm && !confirm(t(a.confirm))) return;
      b.disabled = true;
      try {
        const res = await a.run(model, { path: apiPath() });
        if (res && typeof res === "object") model = res;
        if (a.done) toast(t(a.done), "success");
        render();
      } catch (e) {
        showError(e);
        b.disabled = false;
      }
    }));
  }

  function apiPath() {
    return R.api + "/" + String(id).split("/").map(enc).join("/");
  }

  function showError(e) {
    if (e.field) { errors[e.field] = e.code; render(); }
    let msg = t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic");
    if (e.detail) msg += " (" + e.detail + ")";
    toast(msg, "error");
  }

  async function save() {
    errors = {};
    R.sections.flatMap((s) => s.fields).filter(visible).forEach((fd) => {
      if ((fd.req || (fd.reqNew && isNew)) && !String(model[fd.f] == null ? "" : model[fd.f]).trim()) errors[fd.f] = "required";
    });
    if (Object.keys(errors).length) { render(); toast(t("err.form"), "error"); return; }
    try {
      const saved = await api(isNew ? R.api : apiPath(), { method: isNew ? "POST" : "PUT", body: model });
      toast(t(isNew ? "common.created" : "common.saved"), "success");
      if (isNew) {
        location.hash = "#" + R.route + "/" + String(R.id(saved)).split("/").map(enc).join("/");
      } else {
        model = saved;
        render();
      }
    } catch (e) {
      showError(e);
    }
  }

  async function remove() {
    if (!confirm(t("common.confirmDelete"))) return;
    try {
      await api(apiPath(), { method: "DELETE" });
      toast(t("common.deleted"), "success");
      location.hash = "#" + R.route;
    } catch (e) { showError(e); }
  }

  return {
    async load() {
      if (isNew) {
        model = Object.assign({}, typeof R.defaults === "function" ? R.defaults() : R.defaults || {});
        if (prefill && prefill.key === key) { Object.assign(model, prefill.values); setPrefill(null); }
        return;
      }
      try { model = await api(apiPath()); } catch (e) { if (e.status === 404) missing = true; else throw e; }
    },
    render,
  };
}
