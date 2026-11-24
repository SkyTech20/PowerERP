/* PowerERP: My account (change own password). */
import { $, api, esc, roleName, t, toast } from "../core.js";
import { user } from "../state.js";
import { pageHead } from "../views.js";

export function accountView() {
  return {
    async load() {},
    render() {
      const f = (id, l, auto) => `<div class="field"><label for="${id}">${esc(t(l))}<span class="req">*</span></label><input type="password" id="${id}" autocomplete="${auto}"></div>`;
      $("#view").innerHTML = pageHead(t("acc.title"), `${user.name} (${user.username}) · ${roleName(user.role)}`) + `
        <form class="card" id="pwForm" novalidate><div class="card-head"><h2>${esc(t("acc.changePassword"))}</h2></div>
          <div class="card-body"><div class="form-grid">
            ${f("pwCurrent", "acc.current", "current-password")}${f("pwNew", "f.password", "new-password")}${f("pwConfirm", "acc.confirm", "new-password")}
          </div><p class="help">${esc(t("usr.passwordHelp"))}</p>
          <button type="submit" class="btn primary">${esc(t("common.save"))}</button></div></form>`;
      $("#pwForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const current = $("#pwCurrent").value, password = $("#pwNew").value;
        if (!current || !password) { toast(t("err.form"), "error"); return; }
        if (password !== $("#pwConfirm").value) { toast(t("err.password_mismatch"), "error"); return; }
        try {
          await api("auth/password", { method: "POST", body: { current, password } });
          toast(t("acc.passwordChanged"), "success");
          this.render();
        } catch (err) { toast(t("err." + err.code) !== "err." + err.code ? t("err." + err.code) : t("err.generic"), "error"); }
      });
    },
  };
}
