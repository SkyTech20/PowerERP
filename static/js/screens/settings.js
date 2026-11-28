/* PowerERP: Administration > System settings (administrators only): the company profile (with its logo) and the demo data. */
import { $, $$, api, esc, t, toast } from "../core.js";
import { decorateScreen, helpButtonOf } from "../helpui.js";
import { pageHead } from "../views.js";

// The fields of the company profile (the header of the invoices): [field, label, span]
export const COMPANY_FIELDS = [
  ["cName", "sys.company.cName", 2], ["cLegalName", "sys.company.cLegalName", 2],
  ["cAddress1", "f.cAddress1", 2], ["cAddress2", "f.cAddress2", 2],
  ["cCity", "f.cCity", 1], ["cProvince", "f.cProvince", 1], ["cZipCode", "f.cZipCode", 1], ["cCountry", "f.cCountry", 1],
  ["cPhone", "sys.company.cPhone", 1], ["cEmail", "sys.company.cEmail", 1], ["cWebsite", "sys.company.cWebsite", 1], ["cNEQ", "sys.company.cNEQ", 1], ["iInvoiceStart", "sys.company.iInvoiceStart", 1],
  ["cInvoiceNoteFR", "sys.company.cInvoiceNoteFR", 2], ["cInvoiceNoteEN", "sys.company.cInvoiceNoteEN", 2],
];

const SCREEN = "admin.settings"; // its help page: help/<lang>/admin.settings.md
export const LOGO_TYPES = ["image/png", "image/jpeg", "image/gif", "image/webp"];
export const LOGO_MAX_BYTES = 5 * 1024 * 1024; // the same limit as the server
let logoVersion = Date.now(); // a new one after each change: the browser shows the new logo, not its cached copy

// Why a file cannot be the logo ("" when it can), checked before uploading it
export function logoProblem(file) {
  if (!file) return "logo_invalid";
  if (!LOGO_TYPES.includes(file.type)) return "logo_invalid";
  return file.size > LOGO_MAX_BYTES ? "logo_too_big" : "";
}

const readDataUrl = (file) => new Promise((resolve, reject) => {
  const r = new FileReader();
  r.onload = () => resolve(r.result);
  r.onerror = () => reject(new Error("logo_invalid"));
  r.readAsDataURL(file);
});

function logoBlock(company) {
  const preview = company.lHasLogo
    ? `<img id="logoPreview" src="/api/company/logo?v=${logoVersion}" alt="${esc(t("sys.company.logo"))}">`
    : `<span class="logo-empty">${esc(t("sys.company.noLogo"))}</span>`;
  return `<div class="logo-field"><label for="logoFile">${esc(t("sys.company.logo"))}</label>
    <div class="logo-row"><div class="logo-box">${preview}</div>
      <div class="logo-actions">
        <input type="file" id="logoFile" data-help-f="cLogo" accept="${LOGO_TYPES.join(",")}" hidden>
        <button type="button" class="btn" id="logoPick">🖼 ${esc(t(company.lHasLogo ? "sys.company.logoChange" : "sys.company.logoPick"))}</button>
        ${company.lHasLogo ? `<button type="button" class="btn" id="logoRemove">✕ ${esc(t("sys.company.logoRemove"))}</button>` : ""}
      </div></div>
    <p class="help">${esc(t("sys.company.logo.help"))}</p></div>`;
}
const errorText = (err) => (t("err." + err.code) !== "err." + err.code ? t("err." + err.code) : t("err.generic"));

function companyCard(company) {
  const fields = COMPANY_FIELDS.map(([f, l, span]) => `<div class="field span-${span}"><label for="co_${f}">${esc(t(l))}${f === "cName" ? " *" : ""}</label>
    <input type="text" id="co_${f}" data-co="${f}" data-help-f="${f}" value="${esc(company[f] || "")}"></div>`).join("");
  const numbers = (company.taxNumbers || []).map((n) => `<tr><td>${esc(n.cTaxCode)}</td><td>${esc(n.cRegistrationNo)}</td></tr>`).join("");
  return `<div class="card"><div class="card-head"><h2>${esc(t("sys.company"))}</h2></div>
    <div class="card-body"><p class="help">${esc(t("sys.company.help"))}</p>
      ${logoBlock(company)}
      <form id="companyForm"><div class="form-grid">${fields}</div>
      <h3>${esc(t("sys.company.taxNumbers"))}</h3><p class="help">${esc(t("sys.company.taxNumbers.help"))}</p>
      ${numbers ? `<div class="table-wrap"><table class="grid"><tbody>${numbers}</tbody></table></div>` : `<p class="help">${esc(t("sys.company.noTaxNumbers"))}</p>`}
      <button type="submit" class="btn primary" id="companySave" style="margin-top:12px">${esc(t("common.save"))}</button></form></div></div>`;
}

// ------------------------------------------------------------------ Administration > System settings
export function settingsView() {
  let demo = { scenario: "", scenarios: [] };
  let company = {};
  let busy = false;
  return {
    async load() { [demo, company] = await Promise.all([api("demo"), api("company")]); },
    render() {
      const options = demo.scenarios.map((s) => `<option value="${esc(s)}"${s === demo.scenario ? " selected" : ""}>${esc(t("dash.scenario." + s))}</option>`).join("");
      $("#view").innerHTML = pageHead(t("sys.title"), t("sys.subtitle"), helpButtonOf(SCREEN)) + companyCard(company) + `
        <div class="card"><div class="card-head"><h2>${esc(t("dash.scenario"))}</h2></div>
          <div class="card-body"><div class="form-grid">
            <div class="field span-2"><label for="demoScenario">${esc(t("sys.scenario"))}</label>
              <select id="demoScenario" data-help-f="scenario">${options}</select><p class="help">${esc(t("sys.scenario.help"))}</p></div>
          </div><button type="button" class="btn primary" id="resetBtn" ${busy ? "disabled" : ""}>↺ ${esc(t("dash.reset"))}</button></div></div>
        <div class="card"><div class="card-head"><h2>${esc(t("dash.clear"))}</h2></div>
          <div class="card-body"><p class="help">${esc(t("sys.clear.help"))}</p>
          <button type="button" class="btn danger" id="clearBtn" ${busy ? "disabled" : ""}>🗑 ${esc(t("dash.clear"))}</button></div></div>`;
      const run = async (path, body, done) => {
        busy = true; this.render();
        try {
          const r = await api(path, { method: "POST", body });
          if (r && r.scenario) demo.scenario = r.scenario;
          company = await api("company"); // each demo scenario has its own company profile
          toast(t(done), "success");
        } catch (err) { toast(errorText(err), "error"); }
        busy = false; this.render();
      };
      decorateScreen(SCREEN);
      $("#companyForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const body = {};
        $$("[data-co]").forEach((el) => { body[el.dataset.co] = el.value; });
        try {
          company = await api("admin/company", { method: "PUT", body });
          toast(t("sys.company.saved"), "success");
          this.render();
        } catch (err) {
          toast(errorText(err), "error");
          const el = err.field && $("#co_" + err.field);
          if (el) el.focus();
        }
      });
      $("#logoPick").addEventListener("click", () => $("#logoFile").click());
      $("#logoFile").addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const problem = logoProblem(file);
        if (problem) { toast(t("err." + problem), "error"); e.target.value = ""; return; }
        try {
          company = await api("admin/company/logo", { method: "PUT", body: { cLogo: await readDataUrl(file) } });
          logoVersion = Date.now();
          toast(t("sys.company.logoSaved"), "success");
          this.render();
        } catch (err) { toast(errorText(err), "error"); e.target.value = ""; }
      });
      const remove = $("#logoRemove");
      if (remove) remove.addEventListener("click", async () => {
        if (!confirm(t("sys.company.logoRemoveConfirm"))) return;
        try {
          company = await api("admin/company/logo", { method: "DELETE" });
          logoVersion = Date.now();
          toast(t("sys.company.logoRemoved"), "success");
          this.render();
        } catch (err) { toast(errorText(err), "error"); }
      });
      $("#resetBtn").addEventListener("click", () => {
        const scenario = $("#demoScenario").value;
        if (confirm(t("dash.resetConfirm", { s: t("dash.scenario." + scenario) }))) run("reset", { scenario }, "dash.resetDone");
      });
      $("#clearBtn").addEventListener("click", () => {
        if (confirm(t("dash.clearConfirm"))) run("clear", {}, "dash.clearDone");
      });
    },
  };
}
