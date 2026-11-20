/* PowerERP: Administration > Backups. */
import { $, api, enc, esc, fmtDateTime, t, toast } from "../core.js";
import { pageHead } from "../views.js";

// ------------------------------------------------------------------ Administration > Backups
export function backupView() {
  let st = null;
  let busy = false;
  const errText = (e) => (t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic")) + (e.detail ? " — " + e.detail : "");
  const size = (n) => n >= 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB";
  return {
    async load() { st = await api("admin/backup"); },
    render() {
      const s = st.settings, last = st.status || {};
      const num = (id, l, v, help) => `<div class="field"><label for="${id}">${esc(t(l))}<span class="req">*</span></label>
          <input type="text" id="${id}" value="${esc(v)}" inputmode="numeric"><p class="help">${esc(t(help))}</p></div>`;
      const files = st.files.length ? `<table class="grid"><thead><tr><th>${esc(t("bk.files"))}</th><th>${esc(t("bk.date"))}</th>
            <th class="num">${esc(t("bk.size"))}</th><th></th></tr></thead><tbody>
          ${st.files.map((f) => `<tr><td>${esc(f.name)}</td><td>${esc(fmtDateTime(f.date))}</td><td class="num">${esc(size(f.size))}</td>
            <td><a class="btn small" href="api/admin/backup/files/${enc(f.name)}" download>${esc(t("bk.download"))}</a></td></tr>`).join("")}
          </tbody></table>` : `<div class="empty">${esc(t("bk.none"))}</div>`;
      $("#view").innerHTML = pageHead(t("bk.title"), t("bk.subtitle"),
        `<button class="btn primary" id="bkRun" ${busy ? "disabled" : ""}>${esc(t(busy ? "bk.running" : "bk.runNow"))}</button>`) + `
        <div class="card"><div class="card-body">
          <p><strong>${esc(t("bk.last"))}:</strong> ${last.lastSuccess ? esc(fmtDateTime(last.lastSuccess) + " — " + (last.lastFile || "")) : esc(t("bk.never"))}
          &nbsp;·&nbsp; <strong>${esc(t("bk.next"))}:</strong> ${st.nextRun ? esc(fmtDateTime(st.nextRun)) : esc(t("bk.off"))}</p>
          ${last.lastError ? `<p class="badge no">${esc(t("bk.lastError"))} (${esc(fmtDateTime(last.lastRun))}): ${esc(last.lastError)}</p>` : ""}
        </div></div>
        <form class="card" id="bkForm" novalidate><div class="card-head"><h2>${esc(t("bk.settings"))}</h2></div>
          <div class="card-body"><div class="form-grid">
            <div class="field"><label class="check"><input type="checkbox" id="bkEnabled" ${s.enabled ? "checked" : ""}> ${esc(t("bk.enabled"))}</label></div>
            ${num("bkInterval", "bk.interval", s.intervalHours, "bk.interval.help")}
            ${num("bkKeep", "bk.keep", s.keep, "bk.keep.help")}
            <div class="field"><label for="bkPath">${esc(t("bk.path"))}<span class="req">*</span></label>
              <input type="text" id="bkPath" value="${esc(s.path)}"><p class="help">${esc(t("bk.path.help"))}</p></div>
          </div><button type="submit" class="btn primary">${esc(t("common.save"))}</button></div></form>
        <div class="card"><div class="table-wrap">${files}</div><div class="card-body"><p class="help">${esc(t("bk.restore"))}</p></div></div>`;
      $("#bkForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          st = await api("admin/backup", { method: "PUT", body: { enabled: $("#bkEnabled").checked,
            intervalHours: $("#bkInterval").value, keep: $("#bkKeep").value, path: $("#bkPath").value } });
          toast(t("bk.saved"), "success");
          this.render();
        } catch (err) { toast(errText(err), "error"); }
      });
      $("#bkRun").addEventListener("click", async () => {
        busy = true; this.render();
        try {
          st = await api("admin/backup/run", { method: "POST", body: {} });
          toast(t("bk.done", { name: st.status.lastFile }), "success");
        } catch (err) { toast(errText(err), "error"); await this.load(); }
        busy = false; this.render();
      });
    },
  };
}
