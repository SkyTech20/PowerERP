/* PowerERP: Administration > System settings (administrators only): the demo data. */
import { $, api, esc, t, toast } from "../core.js";
import { pageHead } from "../views.js";

// ------------------------------------------------------------------ Administration > System settings
export function settingsView() {
  let demo = { scenario: "", scenarios: [] };
  let busy = false;
  return {
    async load() { demo = await api("demo"); },
    render() {
      const options = demo.scenarios.map((s) => `<option value="${esc(s)}"${s === demo.scenario ? " selected" : ""}>${esc(t("dash.scenario." + s))}</option>`).join("");
      $("#view").innerHTML = pageHead(t("sys.title"), t("sys.subtitle")) + `
        <div class="card"><div class="card-head"><h2>${esc(t("dash.scenario"))}</h2></div>
          <div class="card-body"><div class="form-grid">
            <div class="field span-2"><label for="demoScenario">${esc(t("sys.scenario"))}</label>
              <select id="demoScenario">${options}</select><p class="help">${esc(t("sys.scenario.help"))}</p></div>
          </div><button type="button" class="btn primary" id="resetBtn" ${busy ? "disabled" : ""}>↺ ${esc(t("dash.reset"))}</button></div></div>
        <div class="card"><div class="card-head"><h2>${esc(t("dash.clear"))}</h2></div>
          <div class="card-body"><p class="help">${esc(t("sys.clear.help"))}</p>
          <button type="button" class="btn danger" id="clearBtn" ${busy ? "disabled" : ""}>🗑 ${esc(t("dash.clear"))}</button></div></div>`;
      const run = async (path, body, done) => {
        busy = true; this.render();
        try {
          const r = await api(path, { method: "POST", body });
          if (r && r.scenario) demo.scenario = r.scenario;
          toast(t(done), "success");
        } catch (err) { toast(t("err." + err.code) !== "err." + err.code ? t("err." + err.code) : t("err.generic"), "error"); }
        busy = false; this.render();
      };
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
