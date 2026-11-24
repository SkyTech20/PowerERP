/* PowerERP: Generic form screen of a resource (create / edit). */
import { $, $$, TAX_RATES, api, enc, esc, money, num, numOnly, round2, sourceBadge, t, toast } from "../core.js";
import { bindLookup, lookupOptions, lookupRows } from "../lookups.js";
import { RES } from "../registry.js";
import { clearLookups, prefill, setPrefill } from "../state.js";
import { pageHead, tabLabel } from "../views.js";

// ---------- Generic form
// Field options: req, reqNew, key (read-only once saved), readonly, type (text | number | date | select | check |
// textarea | password | email), lookup (+ fill, lookupParams, onPick), show(model, isNew), rerender (redraw on change).
// Resource options: lines, grids (other child lists: [{ key, title, help, cols, newLine, show, tab }]), totals, tax,
// locked(model, isNew), actions (a field's readonly and a line column's show can be functions of the record), panel { html(model), bind(model), tab, onNew } and panels (more of them).
// recalc(model, { path, field, line }) -> Promise of the model calculated by the server: called when a field or a
// line column marked recalc: true changes (e.g. the prices and taxes of a sales invoice); its errors are shown.
// A grid with a detail (G.detail) is shown as a list of its lines (G.cols: what a line shows, with fmt) and a panel
// to edit the selected one: detail { sections(line, model) -> [{ t, help, fields }], order(lines) -> indexes,
// group(line, model) -> heading, errorAt(detail, lines, code) -> { i, f }, focus }; fields are field options
// (rerender: redraw the panel when it changes, int).
export function formView(key, id) {
  const R = RES[key];
  const isNew = id == null;
  let model = null;
  let errors = {};
  let missing = false;
  let locked = false;
  let activeTab = R.formTabs ? R.formTabs[0][0] : null; // R.formTabs: sections shown as tabs
  let refreshers = []; // lookups whose list depends on other fields
  const picked = {}; // grid with a detail -> index of the line shown in its panel
  let lineError = null; // { key, i, f, code }: the line (and its field) refused on save
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
    const ro = locked || (typeof fd.readonly === "function" ? fd.readonly(model) : fd.readonly) || (fd.key && !isNew);
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
    if (fd.lookup && fd.free && !ro) {
      // a code typed freely, with the codes already used as suggestions (e.g. payment terms)
      input = `<input type="text" id="f-${fd.f}" data-f="${fd.f}" value="${esc(v)}" list="dl-${fd.f}" autocomplete="off"><datalist id="dl-${fd.f}"></datalist>`;
    } else if (fd.lookup && !ro) {
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

  // A field of the line shown in the panel of a grid with a detail
  function detailFieldHtml(key, fd, ln, i) {
    const v = ln[fd.f];
    const ro = locked || fd.readonly;
    const id = `d-${key}-${fd.f}`;
    const bad = lineError && lineError.key === key && lineError.i === i && lineError.f === fd.f;
    const label = `<label for="${id}">${esc(t(fd.l))}${fd.req && !locked ? '<span class="req">*</span>' : ""}</label>`;
    const err = bad ? `<span class="err">${esc(t("err." + lineError.code))}</span>` : "";
    const help = fd.help ? `<span class="help">${esc(t(fd.help))}</span>` : "";
    const cls = `field ${fd.span === 4 ? "span-4" : fd.span >= 2 ? "span-2" : ""} ${bad ? "invalid" : ""}`;
    if (fd.type === "check") {
      return `<div class="${cls}"><label class="check"><input type="checkbox" id="${id}" data-lf="${fd.f}" ${v ? "checked" : ""} ${ro ? "disabled" : ""}> ${esc(t(fd.l))}</label>${help}${err}</div>`;
    }
    let input;
    if (fd.type === "select") {
      const cur = String(v == null ? "" : v);
      const known = fd.options.some(([ov]) => ov === cur);
      const label = ([ov, ol]) => (fd.raw || !known && ov === cur ? ol : t(ol)); // a value not in the list is shown as is
      const options = known ? fd.options : [...fd.options, [cur, cur]];
      input = `<select id="${id}" data-lf="${fd.f}" ${ro ? "disabled" : ""}>${options.map((o) => `<option value="${esc(o[0])}" ${cur === o[0] ? "selected" : ""}>${esc(label(o))}</option>`).join("")}</select>`;
    } else if (fd.type === "textarea") {
      input = `<textarea id="${id}" data-lf="${fd.f}" rows="2" ${ro ? "readonly" : ""}>${esc(v)}</textarea>`;
    } else {
      const mode = fd.type === "number" ? 'inputmode="decimal" data-num="1" style="text-align:right"' : "";
      input = `<input type="text" id="${id}" data-lf="${fd.f}" value="${esc(v)}" ${ro ? "readonly" : ""} ${mode}>`;
    }
    return `<div class="${cls}">${label}${input}${help}${err}</div>`;
  }

  // What a line of a grid with a detail shows in its list
  const detailLabel = (L, ln) => L.cols.map((c) => `<span class="dl-${c.f}">${esc(c.fmt ? c.fmt(ln[c.f], ln, model) : ln[c.f])}</span>`).join(" ");

  // A grid with a detail: the list of its lines (grouped, in order) and the panel of the selected line
  function detailHtml(L, key) {
    const D = L.detail;
    const rows = model[key] || [];
    if (picked[key] == null || picked[key] >= rows.length) picked[key] = rows.length ? (D.order ? D.order(rows)[0] : 0) : -1;
    const sel = picked[key];
    const order = D.order ? D.order(rows) : rows.map((_, i) => i);
    let lastGroup = null;
    const list = order.map((i) => {
      const ln = rows[i];
      const g = D.group ? D.group(ln, model) : null;
      const head = g != null && g !== lastGroup ? `<div class="dl-group">${esc(g)}</div>` : "";
      lastGroup = g;
      const bad = lineError && lineError.key === key && lineError.i === i;
      return `${head}<div class="dl-row ${i === sel ? "active" : ""} ${bad ? "invalid" : ""}" data-pick="${i}" role="button" tabindex="0" aria-pressed="${i === sel}">
        <span class="dl-label">${detailLabel(L, ln)}</span>
        ${locked ? "" : `<button type="button" class="link-btn" data-remove="${i}" title="${esc(t("common.removeLine"))}">✕</button>`}</div>`;
    }).join("");
    const addBtn = locked ? "" : `<button type="button" class="btn small" data-add style="margin-left:auto">＋ ${esc(t(D.addLabel || "common.addLine"))}</button>`;
    const panel = sel < 0 ? "" : D.sections(rows[sel], model).filter((s) => s.fields.length || s.help).map((s) => {
      const fields = s.fields.map((fd) => detailFieldHtml(key, fd, rows[sel], sel)).join("");
      return `<div class="dl-section"><h3>${esc(t(s.t))}</h3>${s.help ? `<p class="help muted section-help">${esc(t(s.help))}</p>` : ""}${fields ? `<div class="form-grid">${fields}</div>` : ""}</div>`;
    }).join("");
    return `<div class="card" data-grid="${key}" data-detail="1"><div class="card-head"><h2>${esc(t(L.title || "common.lines"))}</h2>${L.help ? `<span class="help muted">${esc(t(L.help))}</span>` : ""}${addBtn}</div>
      ${rows.length ? `<div class="detail-grid"><div class="dl-list">${list}</div><div class="dl-panel" data-panel>${panel}</div></div>` : `<div class="empty">${esc(t("common.noLines"))}</div>`}</div>`;
  }

  // A grid of child lines: R.lines (model.lines, with amounts and totals) or one of R.grids (model[G.key]).
  function linesHtml(L = R.lines, key = "lines") {
    if (L.detail) return detailHtml(L, key);
    const rows = model[key] || [];
    const amount = key === "lines" && L.amount;
    const cols = L.cols.filter((c) => !c.show || c.show(model)); // a column can depend on the record (show)
    const head = cols.map((c) => `<th class="${c.n ? "num" : ""}">${esc(c.raw ? c.l : t(c.l))}</th>`).join("")
      + (amount ? `<th class="num">${esc(t(L.amountLabel))}</th>` : "") + (locked ? "" : "<th></th>");
    const body = rows.map((ln, i) => `<tr data-line="${i}" class="${L.rowClass ? L.rowClass(ln) : ""}">${cols.map((c) => `<td class="${c.w}">${lineCell(c, ln)}</td>`).join("")}
      ${amount ? `<td class="num" data-amount>${esc(money(L.amount(ln), cur()))}</td>` : ""}
      ${locked ? "" : `<td><button type="button" class="link-btn" data-remove="${i}" title="${esc(t("common.removeLine"))}">✕</button></td>`}</tr>`).join("");
    const addBtn = locked ? "" : `<button type="button" class="btn small" ${key === "lines" ? 'id="addLine"' : ""} data-add style="margin-left:auto">＋ ${esc(t("common.addLine"))}</button>`;
    const help = L.helpOf ? L.helpOf(model) : L.help;
    return `<div class="card" data-grid="${key}"><div class="card-head"><h2>${esc(t(L.title || "common.lines"))}</h2>${help ? `<span class="help muted">${esc(t(help))}</span>` : ""}${addBtn}</div>
      <div class="table-wrap"><table class="grid lines" ${cols.length > 8 ? `style="min-width:${cols.length * 115}px"` : ""}><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>
      ${rows.length ? "" : `<div class="empty">${esc(t("common.noLines"))}</div>`}</div>
      ${key === "lines" && R.totals ? '<div class="totals" id="totals"></div>' : ""}</div>`;
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
      $$('[data-grid="lines"] tr[data-line]').forEach((tr) => {
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
    const title = isNew ? t(R.newTitle) : `${t(R.oneOf ? R.oneOf(model) : R.one)} ${R.label(model)}`;
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
      const badGrid = (R.grids || []).find((G) => errors[G.key]);
      if (bad) activeTab = tabOf(bad); else if (errors.lines && R.lines) activeTab = tabOf(R.lines); else if (badGrid) activeTab = tabOf(badGrid);
    }
    const sections = R.sections.map((s, i) => {
      const fields = s.fields.map(fieldHtml).join("");
      if (!fields) return "";
      return wrap(tabOf(s), `<div class="card"><div class="card-head"><h2>${esc(t(s.t))}</h2>${i === 0 ? badge : ""}</div>
        <div class="card-body">${s.help ? `<p class="help muted section-help">${esc(t(s.help))}</p>` : ""}<div class="form-grid">${fields}</div></div></div>`);
    }).join("");
    const lines = (R.lines && (!R.lines.show || R.lines.show(model, isNew)) ? wrap(tabOf(R.lines), linesHtml()) : "")
      + (R.grids || []).filter((G) => !G.show || G.show(model, isNew)).map((G) => wrap(tabOf(G), linesHtml(G, G.key))).join("");
    const panelList = [R.panel, ...(R.panels || [])].filter(Boolean);
    const shownPanels = panelList.filter((P) => !isNew || P.onNew);
    const panel = shownPanels.map((P) => wrap(tabOf(P), P.html(model))).join("");
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
    shownPanels.forEach((P) => P.bind && P.bind(model));
    if (R.tax && model[R.tax.supplier]) loadSupplierTax(model[R.tax.supplier]);
  }

  function bind() {
    refreshers = [];
    const refresh = () => refreshers.forEach((f) => f());
    const allFields = R.sections.flatMap((s) => s.fields);
    allFields.forEach((fd) => {
      if (!visible(fd)) return; // a hidden field may share its name with a visible one (e.g. a lookup per type)
      const el = $(`[data-f="${fd.f}"]`, $("#form"));
      if (!el) return;
      const update = () => {
        model[fd.f] = fd.type === "check" ? el.checked : fd.int ? parseInt(el.value, 10) : fd.type === "number" ? numOnly(el) : el.value;
        if (fd.f === "cDevise" || fd.f === "Devise") refreshAmounts();
        if (fd.rerender) render(); else refresh();
      };
      el.addEventListener(fd.type === "check" || el.tagName === "SELECT" ? "change" : "input", update);
      if (fd.recalc && !(fd.lookup && !fd.free && el.tagName === "SELECT")) el.addEventListener("change", () => recalc(fd.f, null));
      if (fd.lookup && fd.free) {
        let rows = [];
        lookupRows(fd.lookup).then((r) => {
          rows = r;
          const dl = $(`#dl-${fd.f}`);
          if (dl) dl.innerHTML = rows.map((x) => `<option value="${esc(x.code)}">${esc(x.label || "")}</option>`).join("");
        });
        el.addEventListener("input", () => {
          const r = rows.find((x) => x.code === el.value);
          const target = fd.fill && $(`[data-f="${fd.fill}"]`);
          if (r && r.label && target) { model[fd.fill] = r.label; target.value = r.label; }
        });
      }
      if (fd.lookup && !fd.free && el.tagName === "SELECT") {
        const fill = bindLookup(el, fd.lookup, (code, label) => {
          model[fd.f] = code;
          if (fd.fill && label) {
            model[fd.fill] = label;
            const target = $(`[data-f="${fd.fill}"]`);
            if (target) target.value = label;
          }
          if (fd.onPick === "fillFromPo") fillFromPo(code);
          if (fd.recalc) recalc(fd.f, null);
          if (R.tax && fd.f === R.tax.supplier) { taxLive = true; loadSupplierTax(code); }
        }, fd.lookupParams ? () => fd.lookupParams(model) : null);
        if (fd.lookupParams) refreshers.push(fill);
      }
    });
    if (R.lines) bindGrid(R.lines, "lines");
    (R.grids || []).forEach((G) => bindGrid(G, G.key));
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

  // Events of a grid with a detail: pick a line, edit the fields of its panel, remove a line, add a line
  function bindDetail(L, key, card) {
    const D = L.detail;
    $$("[data-pick]", card).forEach((row) => {
      const pick = () => { picked[key] = +row.dataset.pick; render(); };
      row.addEventListener("click", (e) => { if (!e.target.closest("[data-remove]")) pick(); });
      row.addEventListener("keydown", (e) => { if (e.target === row && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); pick(); } });
    });
    const panel = $("[data-panel]", card);
    const i = picked[key];
    if (panel && i >= 0) {
      const ln = model[key][i];
      const fields = D.sections(ln, model).flatMap((s) => s.fields);
      const relabel = () => { const el = $(`[data-pick="${i}"] .dl-label`, card); if (el) el.innerHTML = detailLabel(L, ln); };
      $$("[data-lf]", panel).forEach((el) => {
        const fd = fields.find((x) => x.f === el.dataset.lf) || {};
        if (el.type === "checkbox" || el.tagName === "SELECT") {
          el.addEventListener("change", () => {
            ln[fd.f] = el.type === "checkbox" ? el.checked : fd.int ? parseInt(el.value, 10) || 0 : el.value;
            if (fd.rerender) render(); else relabel();
          });
        } else {
          el.addEventListener("input", () => { ln[fd.f] = el.dataset.num ? numOnly(el) : el.value; relabel(); });
          if (fd.rerender) el.addEventListener("change", render);
        }
      });
    }
    $$("[data-remove]", card).forEach((b) => b.addEventListener("click", () => {
      const r = +b.dataset.remove;
      model[key].splice(r, 1);
      if (picked[key] > r || picked[key] >= model[key].length) picked[key] -= 1;
      if (lineError && lineError.key === key) lineError = null;
      render();
    }));
    const add = $("[data-add]", card);
    if (add) {
      add.addEventListener("click", () => {
        model[key] = model[key] || [];
        model[key].push(L.newLine ? L.newLine(model, model[key][picked[key]]) : {});
        picked[key] = model[key].length - 1;
        render();
        const first = $(`[data-grid="${key}"] [data-panel] ${D.focus ? `[data-lf="${D.focus}"]` : "input[data-lf]:not([readonly])"}`);
        if (first) first.focus();
      });
    }
  }

  // Events of one grid of child lines (edit a cell, lookups, remove a line, add a line)
  function bindGrid(L, key) {
    const card = $(`[data-grid="${key}"]`);
    if (!card) return;
    if (L.detail) { bindDetail(L, key, card); return; }
    $$("tr[data-line]", card).forEach((tr) => {
      const ln = model[key][+tr.dataset.line];
      $$("[data-lf]", tr).forEach((el) => {
        const col = L.cols.find((c) => c.f === el.dataset.lf) || {};
        if (el.type === "checkbox" || el.tagName === "SELECT") {
          el.addEventListener("change", () => { ln[el.dataset.lf] = el.type === "checkbox" ? el.checked : el.value; });
        } else {
          el.addEventListener("input", () => { ln[el.dataset.lf] = el.dataset.num ? numOnly(el) : el.value; taxLive = true; refreshAmounts(); });
        }
        if (col.recalc && !el.dataset.lookup) el.addEventListener("change", () => recalc(el.dataset.lf, ln));
        if (el.dataset.lookup) {
          const fill = bindLookup(el, el.dataset.lookup, (code, label) => {
            ln[el.dataset.lf] = code;
            if (col.fill && label) {
              ln[col.fill] = label;
              const target = $(`[data-lf="${col.fill}"]`, tr);
              if (target) target.value = label;
            }
            if (col.recalc) recalc(el.dataset.lf, ln);
          }, col.lookupParams ? () => col.lookupParams(model) : null);
          if (col.lookupParams) refreshers.push(fill);
        }
      });
    });
    $$("[data-remove]", card).forEach((b) => b.addEventListener("click", () => { model[key].splice(+b.dataset.remove, 1); taxLive = true; render(); }));
    const add = $("[data-add]", card);
    if (add) {
      add.addEventListener("click", () => {
        model[key] = model[key] || [];
        model[key].push(L.newLine ? L.newLine(model) : {});
        render();
        const rows = $$("tr[data-line]", $(`[data-grid="${key}"]`));
        const first = rows.length && $("input[data-lf]:not([data-lf=cUnique]):not([readonly])", rows[rows.length - 1]);
        if (first) first.focus();
      });
    }
  }

  // The server recalculates the record (R.recalc) after a change of a field or line column marked recalc
  let recalcToken = 0;
  async function recalc(field, line) {
    if (!R.recalc || locked) return;
    const token = ++recalcToken;
    try {
      const res = await R.recalc(model, { path: isNew ? null : apiPath(), field, line });
      if (token !== recalcToken || !res) return;
      model = res;
      errors = {};
      lineError = null;
      render();
    } catch (e) {
      if (token === recalcToken) showError(e);
    }
  }

  function apiPath() {
    return R.api + "/" + String(id).split("/").map(enc).join("/");
  }

  function showError(e) {
    // a line of a grid with a detail refused on save: its panel is opened, on the field named in the detail
    const G = e.field && (R.grids || []).find((g) => g.key === e.field && g.detail && g.detail.errorAt);
    const at = G && e.detail ? G.detail.errorAt(e.detail, model[G.key] || [], e.code) : null;
    if (at && at.i >= 0) { picked[G.key] = at.i; lineError = { key: G.key, i: at.i, f: at.f, code: e.code }; }
    if (e.field) { errors[e.field] = e.code; render(); }
    let msg = t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic");
    if (e.detail) msg += " (" + e.detail + ")";
    toast(msg, "error");
  }

  async function save() {
    errors = {};
    lineError = null;
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

  // A default of a new record that is not in its list (e.g. the tax group QC after "Clear all data") is left
  // empty, rather than shown and refused on save. Values given by the screen that opened the form are kept.
  async function dropUnknownDefaults(given) {
    const fields = R.sections.flatMap((s) => s.fields).filter((fd) => fd.lookup && !fd.free && !fd.lookupParams && !(fd.f in given));
    await Promise.all(fields.map(async (fd) => {
      const v = model[fd.f] == null ? "" : String(model[fd.f]);
      if (!v) return;
      const rows = await lookupRows(fd.lookup);
      if (!rows.some((r) => r.code === v)) model[fd.f] = "";
    }));
  }

  return {
    async load() {
      if (isNew) {
        model = Object.assign({}, typeof R.defaults === "function" ? R.defaults() : R.defaults || {});
        const given = prefill && prefill.key === key ? prefill.values : {};
        if (prefill && prefill.key === key) { Object.assign(model, prefill.values); setPrefill(null); }
        await dropUnknownDefaults(given);
        return;
      }
      try { model = await api(apiPath()); } catch (e) { if (e.status === 404) missing = true; else throw e; }
    },
    render,
  };
}
