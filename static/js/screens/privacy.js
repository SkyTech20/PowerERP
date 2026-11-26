/* PowerERP: Administration > Personal data (Quebec Law 25). Find what the ERP keeps on a person, give it to them,
   anonymize it; the person in charge, where the data is hosted and the retention rule. */
import { $, $$, api, enc, esc, fmtDateTime, fmtInt, lang, t, toast } from "../core.js";
import { decorateScreen, helpButtonOf } from "../helpui.js";
import { pageHead } from "../views.js";

const SCREEN = "admin.privacy";
const POLICY = [
  ["cOfficerName", 1], ["cOfficerTitle", 1], ["cOfficerEmail", 1],
  ["cHosting", 1], ["cRegion", 1], ["iRetentionMonths", 1],
];
const tOr = (k, d) => (t(k) !== k ? t(k) : d);
const errorText = (err) => tOr("err." + err.code, t("err.generic"));
const kindBadge = (k) => `<span class="badge pv-${esc(k)}">${esc(t("pv.kind." + k))}</span>`;
const statusOf = (p) => (p.anonymized ? `<span class="badge">${esc(t("pv.anonymized"))}</span>`
  : `<span class="badge ${p.active ? "yes" : "no"}">${esc(t(p.active ? "opt.active" : "opt.inactive"))}</span>`);
const contact = (p) => [p.email, p.phone].filter(Boolean).map(esc).join("<br>") || "—";
const docLabel = (d) => tOr(`pv.doc.${d.table}.${d.column}`, `${d.table}.${d.column}`);
const fieldLabel = (k) => tOr("pv.f." + k, k);
// the order of the fields kept on a person (the server answers them in any order)
const ORDER = ["name", "username", "email", "title", "phone", "role", "lang", "active", "created", "lastLogin",
  "customer", "customer_name", "address", "address_name", "address1", "city", "invoices", "warehouse"];
const byOrder = ([a], [b]) => (ORDER.indexOf(a) + 1 || 99) - (ORDER.indexOf(b) + 1 || 99);
const show = (v) => (v === true ? t("common.yes") : v === false ? t("common.no") : v == null || v === "" ? "—" : String(v));

export function privacyView() {
  const st = { q: "", items: null, open: null, file: null };
  let policy = {};
  let due = { months: 0, before: "", items: [] };
  let busy = false;
  const loadDue = async () => { due = await api("privacy/retention"); };
  return {
    async load() { [policy, due] = await Promise.all([api("privacy/policy"), api("privacy/retention")]); },
    render() {
      const results = st.items == null ? `<p class="help">${esc(t("pv.search.help"))}</p>`
        : !st.items.length ? `<div class="empty">${esc(t("pv.none"))}</div>`
        : `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("pv.name"))}</th><th>${esc(t("pv.kind"))}</th>
            <th>${esc(t("pv.where"))}</th><th>${esc(t("pv.contact"))}</th><th>${esc(t("pv.status"))}</th><th></th></tr></thead><tbody>
            ${st.items.map((p, i) => `<tr class="${st.open === i ? "pv-open" : ""}"><td><b>${esc(p.name || "—")}</b></td><td>${kindBadge(p.kind)}</td>
              <td>${esc(p.where)}</td><td class="wrap">${contact(p)}</td><td>${statusOf(p)}</td>
              <td><button type="button" class="btn small" data-open="${i}">${esc(t("pv.openFile"))}</button></td></tr>`).join("")}
            </tbody></table></div>`;
      const policyFields = POLICY.map(([f]) => `<div class="field"><label for="pv_${f}">${esc(t("pv.f." + f))}</label>
        <input type="${f === "iRetentionMonths" ? "number" : f === "cOfficerEmail" ? "email" : "text"}" id="pv_${f}" data-pv="${f}" data-help-f="${f}"
          ${f === "iRetentionMonths" ? 'min="1" max="600"' : ""} value="${esc(policy[f] ?? "")}"></div>`).join("");
      const dueRows = due.items.map((p) => `<tr><td><b>${esc(p.name || "—")}</b></td><td>${kindBadge(p.kind)}</td><td>${esc(p.where)}</td>
        <td>${p.kind === "user" ? esc(p.lastLogin ? fmtDateTime(p.lastLogin) : t("pv.never")) : esc(t("pv.noInvoice"))}</td></tr>`).join("");
      $("#view").innerHTML = pageHead(t("pv.title"), t("pv.subtitle"), helpButtonOf(SCREEN)) + `
        <div class="card"><div class="card-head"><h2>${esc(t("pv.find"))}</h2></div>
          <div class="toolbar"><input type="search" id="pvQ" data-help-f="search" placeholder="${esc(t("pv.search"))}" value="${esc(st.q)}" autocomplete="off">
            ${st.items ? `<span class="count">${esc(t("common.records", { n: fmtInt(st.items.length) }))}</span>` : ""}</div>
          ${results}</div>
        ${st.file ? this.fileCard() : ""}
        <div class="card"><div class="card-head"><h2>${esc(t("pv.retention"))}</h2></div><div class="card-body">
          <p class="help">${esc(t("pv.retention.help", { m: due.months, d: due.before }))}</p>
          ${due.items.length ? `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("pv.name"))}</th><th>${esc(t("pv.kind"))}</th>
            <th>${esc(t("pv.where"))}</th><th>${esc(t("pv.lastActivity"))}</th></tr></thead><tbody>${dueRows}</tbody></table></div>
            <button type="button" class="btn danger" id="pvApply" data-help-f="apply" ${busy ? "disabled" : ""} style="margin-top:12px">${esc(t("pv.applyAll", { n: due.items.length }))}</button>`
            : `<div class="empty">${esc(t("pv.noneDue"))}</div>`}</div></div>
        <div class="card"><div class="card-head"><h2>${esc(t("pv.policy"))}</h2></div><div class="card-body">
          <p class="help">${esc(t("pv.policy.help"))}</p>
          <form id="pvPolicy"><div class="form-grid">${policyFields}</div>
          <button type="submit" class="btn primary" style="margin-top:12px">${esc(t("common.save"))}</button></form></div></div>`;
      decorateScreen(SCREEN);
      this.bind();
    },
    fileCard() {
      const f = st.file;
      const p = st.items[st.open];
      const identity = Object.entries(f.identity).sort(byOrder).map(([k, v]) => `<tr><th>${esc(fieldLabel(k))}</th><td>${esc(k === "created" || k === "lastLogin" ? (v ? fmtDateTime(v) : "—") : k === "lang" ? show(v).toUpperCase() : show(v))}</td></tr>`).join("");
      const docs = f.documents.map((d) => `<tr><td>${esc(docLabel(d))}</td><td class="num">${fmtInt(d.count)}</td><td class="wrap">${esc(d.records.join(", "))}${d.count > d.records.length && d.records.length ? " …" : ""}</td></tr>`).join("");
      const events = f.recentEvents.map((e) => `<tr><td class="nowrap">${esc(fmtDateTime(e.at))}</td><td>${esc(e.username || "—")}</td>
        <td>${esc(tOr("au.ev." + e.event, tOr("rl.act." + e.event, e.event)))}</td><td class="wrap">${esc(e.record)}</td><td class="muted">${esc(e.ip)}</td></tr>`).join("");
      const exp = (fmt) => `api/privacy/${enc(f.kind)}/${enc(f.ref)}/export?format=${fmt}&lang=${lang}`;
      const refusal = f.refusal ? `<div class="alert warn">${esc(t("pv.refusal." + f.refusal))}</div>` : "";
      return `<div class="card" id="pvFile"><div class="card-head"><h2>${esc(t("pv.fileOf", { n: p.name || f.ref }))}</h2>${kindBadge(f.kind)}</div><div class="card-body">
        <div class="pv-actions">
          <a class="btn primary" href="${exp("xlsx")}" download data-help-f="export">⬇ ${esc(t("pv.exportXlsx"))}</a>
          <a class="btn" href="${exp("json")}" download data-help-f="exportJson">⬇ ${esc(t("pv.exportJson"))}</a>
          <button type="button" class="btn danger" id="pvAnon" data-help-f="anonymize" ${f.canAnonymize && !busy ? "" : "disabled"}>${esc(t("pv.anonymize"))}</button>
        </div>${refusal}
        <div class="pv-grid">
          <div><h3>${esc(t("pv.kept"))}</h3><div class="table-wrap"><table class="grid kv">${identity}</table></div></div>
          <div><h3>${esc(t("pv.documents"))}</h3>${docs ? `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("pv.docWhere"))}</th><th class="num">${esc(t("pv.count"))}</th><th>${esc(t("pv.records"))}</th></tr></thead><tbody>${docs}</tbody></table></div>`
            : `<p class="help">${esc(t(f.kind === "user" || f.kind === "former" ? "pv.noDocuments" : "pv.contactDocs"))}</p>`}</div>
        </div>
        <h3>${esc(t("pv.events", { n: fmtInt(f.events) }))}</h3>
        ${events ? `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("au.when"))}</th><th>${esc(t("au.user"))}</th><th>${esc(t("au.event"))}</th>
          <th>${esc(t("au.record"))}</th><th>IP</th></tr></thead><tbody>${events}</tbody></table></div>
          ${f.events > f.recentEvents.length ? `<p class="help">${esc(t("pv.moreEvents"))}</p>` : ""}` : `<p class="help">${esc(t("pv.noEvents"))}</p>`}
      </div></div>`;
    },
    bind() {
      let timer = null;
      $("#pvQ").addEventListener("input", (e) => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          st.q = e.target.value.trim();
          st.open = null; st.file = null;
          st.items = st.q.length >= 2 ? (await api("privacy/search?q=" + enc(st.q))).items : null;
          this.render();
          const q = $("#pvQ"); q.focus(); q.setSelectionRange(q.value.length, q.value.length);
        }, 300);
      });
      $$("[data-open]").forEach((b) => b.addEventListener("click", async () => {
        const i = Number(b.dataset.open);
        const p = st.items[i];
        try {
          st.file = await api(`privacy/${enc(p.kind)}/${enc(p.ref)}`);
          st.open = i;
          this.render();
          $("#pvFile").scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (err) { toast(errorText(err), "error"); }
      }));
      const anon = $("#pvAnon");
      if (anon) anon.addEventListener("click", async () => {
        const p = st.items[st.open];
        if (!confirm(t("pv.anonymize.confirm", { n: p.name || p.ref }))) return;
        busy = true; this.render();
        try {
          const r = await api(`privacy/${enc(p.kind)}/${enc(p.ref)}/anonymize`, { method: "POST", body: {} });
          toast(t("pv.anonymized.done", { n: fmtInt(r.changed) }), "success");
          st.file = null; st.open = null;
          st.items = st.q.length >= 2 ? (await api("privacy/search?q=" + enc(st.q))).items : null;
          await loadDue();
        } catch (err) { toast(errorText(err), "error"); }
        busy = false; this.render();
      });
      const apply = $("#pvApply");
      if (apply) apply.addEventListener("click", async () => {
        if (!confirm(t("pv.apply.confirm", { n: due.items.length }))) return;
        busy = true; this.render();
        try {
          const r = await api("privacy/retention/apply", { method: "POST", body: {} });
          toast(t("pv.apply.done", { n: r.anonymized }), "success");
          st.file = null; st.open = null; st.items = null; st.q = "";
          await loadDue();
        } catch (err) { toast(errorText(err), "error"); }
        busy = false; this.render();
      });
      $("#pvPolicy").addEventListener("submit", async (e) => {
        e.preventDefault();
        const body = {};
        $$("[data-pv]").forEach((el) => { body[el.dataset.pv] = el.value; });
        try {
          policy = await api("privacy/policy", { method: "PUT", body });
          await loadDue();
          toast(t("pv.policy.saved"), "success");
          this.render();
        } catch (err) {
          toast(errorText(err), "error");
          const el = err.field && $("#pv_" + err.field);
          if (el) el.focus();
        }
      });
    },
  };
}
