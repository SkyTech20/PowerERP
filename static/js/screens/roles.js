/* PowerERP: Administration > Roles: the list, and a role with its access per screen, its users and its history. */
import { $, $$, api, enc, esc, fmtDateTime, lang, t, toast } from "../core.js";
import { actionsOf, byScreen, levelOf, levelsOf, moduleSummary, toPermissions, toggleAction } from "../access.js";
import { decorateScreen, helpButtonOf } from "../helpui.js";
import { pageHead } from "../views.js";

const errText = (e) => (t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic")) + (e.detail ? " — " + e.detail : "");
const desc = (r) => (lang === "en" && r.cDescEN) || r.cDescFR || "";
const go = (path) => { location.hash = "#" + path; };
const SCREEN = "admin.roles"; // its help page: help/<lang>/admin.roles.md

// ------------------------------------------------------------------ list
export function rolesListView() {
  let rows = [];
  let q = "";
  return {
    async load() { rows = (await api("roles")).items; },
    render() {
      const shown = rows.filter((r) => !q || (r.cCode + " " + r.cDescFR + " " + r.cDescEN).toLowerCase().includes(q.toLowerCase()));
      $("#view").innerHTML = pageHead(t("rl.title"), t("rl.subtitle"), helpButtonOf(SCREEN) + `<a class="btn primary" href="#/admin/roles/new">＋ ${esc(t("common.new"))}</a>`) + `
        <div class="card"><div class="toolbar"><input type="search" id="q" placeholder="${esc(t("common.search"))}" value="${esc(q)}">
          <span class="count">${esc(t("common.records", { n: shown.length }))}</span></div>
        <div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("f.cCode"))}</th><th>${esc(t("f.cDescFR").replace(/ \(.*\)/, ""))}</th>
          <th class="num">${esc(t("rl.users"))}</th><th class="num">${esc(t("rl.screens"))}</th><th>${esc(t("opt.active"))}</th></tr></thead><tbody>
          ${shown.map((r) => `<tr class="clickable" data-href="/admin/roles/${esc(enc(r.cCode))}"><td>${esc(r.cCode)}</td><td class="wrap">${esc(desc(r))}</td>
            <td class="num">${r.iUsers}</td><td class="num">${r.lAdmin ? esc(t("rl.all")) : r.iScreens}</td>
            <td><span class="badge ${r.lActive ? "yes" : "no"}">${esc(t(r.lActive ? "opt.active" : "opt.inactive"))}</span></td></tr>`).join("")}
        </tbody></table></div></div>`;
      decorateScreen(SCREEN);
      $("#q").addEventListener("input", (e) => { q = e.target.value; this.render(); $("#q").focus(); $("#q").setSelectionRange(q.length, q.length); });
      $$("tr[data-href]").forEach((tr) => tr.addEventListener("click", () => go(tr.dataset.href)));
    },
  };
}

// ------------------------------------------------------------------ one role
export function roleFormView(code) {
  const isNew = !code;
  let role = null;
  let catalog = [];
  let others = []; // roles to copy from (new role)
  let history = null;
  let map = {}; // screen -> actions
  let tab = "access";
  let module = "";
  let open = ""; // screen whose actions are shown
  let preview = false;
  let busy = false;

  const modules = () => [...new Set(catalog.map((c) => c.cModule))];
  const screensOf = (m) => catalog.filter((c) => c.cModule === m);
  const ro = () => !!(role && role.lAdmin);

  function levelLabel(l) { return t("rl.lvl." + l); }
  function summaryBadge(m) {
    const s = moduleSummary(map, screensOf(m));
    if (s.level) return `<span class="lv lv-${s.level}">${esc(levelLabel(s.level))}</span>`;
    return `<span class="lv lv-some">${esc(t("rl.of", { open: s.open, total: s.total }))}</span>`;
  }
  function seg(levels, current, attrs) {
    return `<span class="seg" role="group">${levels.map((l) => `<button type="button" class="${l === current ? "on lv-" + l : ""}" ${attrs(l)} ${ro() ? "disabled" : ""} aria-pressed="${l === current}">${esc(levelLabel(l))}</button>`).join("")}${current === "custom" ? `<button type="button" class="on lv-custom" disabled>${esc(levelLabel("custom"))}</button>` : ""}</span>`;
  }

  function accessHtml() {
    const ms = modules();
    if (!module || !ms.includes(module)) module = ms[0];
    const rows = screensOf(module).map((c) => {
      const has = map[c.cScreen] || [];
      const lvl = levelOf(has, c.actions);
      const custom = open === c.cScreen;
      const extra = custom ? `<div class="rl-custom"><h4>${esc(t("rl.actionsOn", { screen: t("menu." + c.cScreen) }))}</h4><div class="rl-chips">
          ${c.actions.map((a) => `<label><input type="checkbox" data-act="${esc(a)}" data-screen="${esc(c.cScreen)}" ${has.includes(a) ? "checked" : ""} ${ro() ? "disabled" : ""}> ${esc(t("rl.act." + a))}</label>`).join("")}
        </div></div>` : "";
      return `<div class="rl-row"><div class="rl-name">${esc(t("menu." + c.cScreen))}</div>
        ${seg(levelsOf(c.actions), lvl, (l) => `data-screen="${esc(c.cScreen)}" data-level="${l}"`)}
        <button type="button" class="link rl-cz" data-open="${esc(c.cScreen)}">${esc(t(custom ? "rl.close" : "rl.customize"))}${custom ? " ▴" : ""}</button></div>${extra}`;
    }).join("");
    return `<div class="rl-layout">
      <div class="card rl-mods">${ms.map((m) => `<button type="button" class="${m === module ? "on" : ""}" data-module="${esc(m)}"><span>${esc(t("menu." + m))}</span>${summaryBadge(m)}</button>`).join("")}</div>
      <div class="card"><div class="rl-head"><h2>${esc(t("menu." + module))}</h2>
        ${ro() ? "" : `<div class="rl-setall"><span class="muted">${esc(t("rl.setAll"))}</span>${seg(["none", "view", "edit", "full"], "", (l) => `data-all="${l}"`)}</div>`}</div>
        ${rows}
        <p class="rl-legend">${esc(t("rl.legend"))}</p>
        <p class="rl-legend">${esc(t("rl.dashboardNote"))} ${esc(t("rl.adminOnly"))}</p></div></div>`;
  }

  function usersHtml() {
    const users = (role && role.users) || [];
    if (!users.length) return `<div class="card"><div class="empty">${esc(t("rl.noUsers"))}</div></div>`;
    return `<div class="card"><div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("f.username"))}</th><th>${esc(t("f.userName"))}</th><th>${esc(t("f.active"))}</th></tr></thead><tbody>
      ${users.map((u) => `<tr class="clickable" data-href="/admin/users/${u.id}"><td>${esc(u.username)}</td><td>${esc(u.name)}</td>
        <td><span class="badge ${u.active ? "yes" : "no"}">${esc(t(u.active ? "opt.active" : "opt.inactive"))}</span></td></tr>`).join("")}
      </tbody></table></div></div>`;
  }

  function historyHtml() {
    if (history === null) return `<div class="card"><div class="empty">${esc(t("common.loading"))}</div></div>`;
    if (!history.length) return `<div class="card"><div class="empty">${esc(t("rl.noHistory"))}</div></div>`;
    const perm = (p) => { const [s, a] = p.split(":"); const c = catalog.find((x) => x.cScreen === s); return `${t("menu." + (c ? c.cModule : ""))} › ${t("menu." + s)}: ${t("rl.act." + a)}`; };
    const details = (h) => {
      const d = h.details || {};
      if (h.cChange === "permissions" || h.cChange === "demo") {
        return [...(d.added || []).map((p) => `<div class="diff-add">+ ${esc(perm(p))}</div>`), ...(d.removed || []).map((p) => `<div class="diff-del">− ${esc(perm(p))}</div>`)].join("");
      }
      if (h.cChange === "updated") {
        return Object.entries(d).map(([k, [a, b]]) => `<div>${esc(t(k === "lActive" ? "opt.active" : "f." + k))}: “${esc(String(a))}” → “${esc(String(b))}”</div>`).join("");
      }
      if (h.cChange === "created") return esc(d.copiedFrom ? t("rl.copiedFrom", { role: d.copiedFrom }) : d.note || t("rl.nPerms", { n: d.permissions || 0 }));
      return esc(d.note || "");
    };
    return `<div class="card"><div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("rl.h.date"))}</th><th>${esc(t("rl.h.user"))}</th>
      <th>${esc(t("rl.h.change"))}</th><th>${esc(t("rl.h.details"))}</th></tr></thead><tbody>
      ${history.map((h) => `<tr><td>${esc(fmtDateTime(h.dAt))}</td><td>${esc(h.cUser)}</td><td>${esc(t("rl.ch." + h.cChange))}</td><td class="wrap">${details(h)}</td></tr>`).join("")}
      </tbody></table></div></div>`;
  }

  function previewHtml() {
    const groups = modules().map((m) => [m, screensOf(m).filter((c) => (map[c.cScreen] || []).includes("view"))]).filter(([, s]) => s.length);
    return `<div class="modal-shade" id="pvShade"></div><div class="modal rl-preview" role="dialog" aria-modal="true">
      <div class="card-head"><h2>${esc(t("rl.previewTitle", { role: role.cCode || "" }))}</h2><button type="button" class="btn small" id="pvClose">✕</button></div>
      <div class="rl-nav">${groups.length ? groups.map(([m, s]) => `<div class="rl-nav-m">${esc(t("menu." + m))}</div>${s.map((c) => `<div class="rl-nav-s">${esc(t("menu." + c.cScreen))}</div>`).join("")}`).join("")
        : `<p class="muted">${esc(t("rl.previewNone"))}</p>`}</div>
      <p class="help" style="padding:0 16px 14px">${esc(t("rl.dashboardNote"))}</p></div>`;
  }

  return {
    async load() {
      catalog = await api("permissions");
      if (isNew) {
        role = { cCode: "", cDescFR: "", cDescEN: "", lActive: true, lAdmin: false, permissions: [], users: [] };
        others = (await api("roles")).items;
      } else {
        role = await api("roles/" + enc(code));
      }
      map = byScreen(role.permissions);
    },
    render() {
      const title = isNew ? t("rl.new") : `${t("rl.one")} ${role.cCode} — ${desc(role)}`;
      const actions = helpButtonOf(SCREEN) + `<button type="button" class="btn" id="rlPreview">👁 ${esc(t("rl.preview"))}</button>
        <a class="btn" href="#/admin/roles">${esc(t("common.cancel"))}</a>
        ${!isNew && !ro() ? `<button type="button" class="btn danger" id="rlDelete">${esc(t("common.delete"))}</button>` : ""}
        ${ro() ? "" : `<button type="button" class="btn primary" id="rlSave" ${busy ? "disabled" : ""}>${esc(t("common.save"))}</button>`}`;
      // existing role: code, description FR, active on one line; new role: code, copy from, active, then the descriptions
      const active = `<div class="field"><label class="check"><input type="checkbox" id="rlActive" data-help-f="lActive" ${role.lActive ? "checked" : ""} ${ro() ? "disabled" : ""}> ${esc(t("opt.active"))}</label></div>`;
      const descFR = `<div class="field span-2"><label for="rlDescFR">${esc(t("f.cDescFR"))}<span class="req">*</span></label><input type="text" id="rlDescFR" data-help-f="cDescFR" value="${esc(role.cDescFR)}" ${ro() ? "readonly" : ""}></div>`;
      const general = `<div class="card"><div class="card-body">
        ${ro() ? `<p class="note">${esc(t("rl.adminNote"))}</p>` : ""}
        ${!role.lActive && !isNew ? `<p class="note">${esc(t("rl.inactiveWarn"))}</p>` : ""}
        <div class="form-grid">
          <div class="field"><label for="rlCode">${esc(t("f.cCode"))}${isNew ? '<span class="req">*</span>' : ""}</label>
            <input type="text" id="rlCode" data-help-f="cCode" value="${esc(role.cCode)}" ${isNew ? "" : "readonly"} maxlength="30" autocomplete="off" style="text-transform:uppercase">
            ${isNew ? `<p class="help">${esc(t("f.rl.cCode.help"))}</p>` : ""}</div>
          ${isNew ? `<div class="field"><label for="rlCopy">${esc(t("rl.copyFrom"))}</label><select id="rlCopy" data-help-f="cCopyFrom"><option value="">${esc(t("rl.copyNone"))}</option>
            ${others.map((r) => `<option value="${esc(r.cCode)}" ${role.cCopyFrom === r.cCode ? "selected" : ""}>${esc(r.cCode + " — " + desc(r))}</option>`).join("")}</select>
            <p class="help">${esc(t("rl.copyHelp"))}</p></div>` : ""}
          ${isNew ? "" : descFR}${active}${isNew ? descFR : ""}
          <div class="field span-2"><label for="rlDescEN">${esc(t("f.cDescEN"))}</label><input type="text" id="rlDescEN" data-help-f="cDescEN" value="${esc(role.cDescEN)}" ${ro() ? "readonly" : ""}></div>
        </div></div></div>`;
      const tabs = isNew ? "" : `<div class="tabs form-tabs" role="tablist">${[["access", "rl.tab.access"], ["users", "rl.tab.users"], ["history", "rl.tab.history"]]
        .map(([k, l]) => `<a href="#" role="tab" data-tab="${k}" class="${tab === k ? "active" : ""}">${esc(t(l))}${k === "users" ? ` (${(role.users || []).length})` : ""}</a>`).join("")}</div>`;
      const body = tab === "users" ? usersHtml() : tab === "history" ? historyHtml() : accessHtml();
      $("#view").innerHTML = pageHead(title, "", actions, `<a href="#/admin/roles">${esc(t("rl.title"))}</a>${isNew ? "" : " / " + esc(role.cCode)}`)
        + general + tabs + body + (preview ? previewHtml() : "");
      this.bind();
      decorateScreen(SCREEN);
    },
    keep() { // the fields typed so far survive a redraw
      if (!$("#rlDescFR")) return;
      if (isNew) role.cCode = $("#rlCode").value.trim().toUpperCase();
      role.cDescFR = $("#rlDescFR").value; role.cDescEN = $("#rlDescEN").value; role.lActive = $("#rlActive").checked;
    },
    bind() {
      const redraw = () => { this.keep(); this.render(); };
      $$("[data-tab]").forEach((a) => a.addEventListener("click", async (e) => {
        e.preventDefault(); tab = a.dataset.tab; redraw();
        if (tab === "history" && history === null) {
          try { history = await api(`roles/${enc(role.cCode)}/history`); } catch (err) { history = []; toast(errText(err), "error"); }
          if (tab === "history") redraw();
        }
      }));
      $$("tr[data-href]").forEach((tr) => tr.addEventListener("click", () => go(tr.dataset.href)));
      $$("[data-module]").forEach((b) => b.addEventListener("click", () => { module = b.dataset.module; open = ""; redraw(); }));
      $$("[data-level]").forEach((b) => b.addEventListener("click", () => {
        const c = catalog.find((x) => x.cScreen === b.dataset.screen);
        map[c.cScreen] = actionsOf(b.dataset.level, c.actions); redraw();
      }));
      $$("[data-all]").forEach((b) => b.addEventListener("click", () => {
        screensOf(module).forEach((c) => { map[c.cScreen] = actionsOf(b.dataset.all, c.actions); }); redraw();
      }));
      $$("[data-open]").forEach((b) => b.addEventListener("click", () => { open = open === b.dataset.open ? "" : b.dataset.open; redraw(); }));
      $$("input[data-act]").forEach((el) => el.addEventListener("change", () => {
        map[el.dataset.screen] = toggleAction(map[el.dataset.screen] || [], el.dataset.act, el.checked); redraw();
      }));
      const copy = $("#rlCopy");
      if (copy) copy.addEventListener("change", async () => {
        this.keep(); role.cCopyFrom = copy.value;
        if (copy.value) {
          try { map = byScreen((await api("roles/" + enc(copy.value))).permissions); } catch (err) { toast(errText(err), "error"); }
        }
        this.render();
      });
      $("#rlPreview").addEventListener("click", () => { this.keep(); preview = true; this.render(); });
      if (preview) {
        const close = () => { preview = false; this.render(); };
        $("#pvClose").addEventListener("click", close); $("#pvShade").addEventListener("click", close);
      }
      const del = $("#rlDelete");
      if (del) del.addEventListener("click", async () => {
        if (!confirm(t("rl.confirmDelete", { role: role.cCode }))) return;
        try { await api("roles/" + enc(role.cCode), { method: "DELETE" }); toast(t("rl.deleted"), "success"); go("/admin/roles"); }
        catch (err) { toast(errText(err), "error"); }
      });
      const save = $("#rlSave");
      if (save) save.addEventListener("click", async () => {
        this.keep();
        const body = { cDescFR: role.cDescFR, cDescEN: role.cDescEN, lActive: role.lActive, permissions: toPermissions(map, catalog) };
        busy = true;
        try {
          if (isNew) {
            const r = await api("roles", { method: "POST", body: { ...body, cCode: role.cCode, cCopyFrom: role.cCopyFrom || "" } });
            toast(t("rl.saved"), "success"); go("/admin/roles/" + enc(r.cCode));
          } else {
            role = await api("roles/" + enc(role.cCode), { method: "PUT", body });
            map = byScreen(role.permissions); history = null;
            toast(t("rl.saved"), "success");
          }
        } catch (err) {
          toast(errText(err), "error");
          const f = { cCode: "#rlCode", cDescFR: "#rlDescFR" }[err.field];
          if (f && $(f)) $(f).focus();
        }
        busy = false;
        if (!isNew) this.render();
      });
    },
  };
}
