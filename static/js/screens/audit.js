/* PowerERP: Administration > Audit log. Who did what and when: logins, lockouts, refusals, and every change. */
import { $, $$, api, enc, esc, fmtInt, lang, t } from "../core.js";
import { decorateScreen, helpButtonOf } from "../helpui.js";
import { pageHead } from "../views.js";

const SCREEN = "admin.audit";
const ALERTS = new Set(["login_failed", "locked", "login_locked", "password_failed", "access_denied"]);
const tOr = (k, d) => (t(k) !== k ? t(k) : d);
const eventLabel = (e) => tOr("au.ev." + e, tOr("rl.act." + e, e));
const screenLabel = (s) => (s ? tOr("menu." + s, s) : "");
// local date and time, the same short form in both languages: 2026-11-25 20:41:47
const pad = (n) => String(n).padStart(2, "0");
const when = (v) => { const d = new Date(v); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; };
const isoDay = (d) => d.toISOString().slice(0, 10);

export function auditView() {
  const st = { from: isoDay(new Date(Date.now() - 6 * 86400000)), to: "", user: "", kind: "", event: "", q: "", page: 1 };
  let data = null;
  let lists = { users: [], events: { security: [], change: [] } };
  let open = null;
  const query = (extra) => Object.entries({ ...st, size: 50, ...extra }).filter(([, v]) => v !== "" && v != null).map(([k, v]) => `${k}=${enc(v)}`).join("&");
  return {
    async load() {
      [data, lists] = await Promise.all([api("audit?" + query()), api("audit/filters")]);
    },
    render() {
      const pages = Math.max(1, Math.ceil(data.total / data.size));
      const events = st.kind ? lists.events[st.kind] : [...lists.events.security, ...lists.events.change];
      const opt = (v, l, cur) => `<option value="${esc(v)}" ${v === cur ? "selected" : ""}>${esc(l)}</option>`;
      const rows = data.items.map((e) => {
        const alert = ALERTS.has(e.event);
        const details = Object.keys(e.details || {}).length;
        const reason = e.details && e.details.reason ? `<div class="muted au-small">${esc(tOr("au.reason." + e.details.reason, e.details.reason))}</div>` : "";
        return `<tr data-id="${e.id}" class="${alert ? "au-alert" : ""}"><td class="nowrap">${esc(when(e.at))}</td>
          <td><b>${esc(e.username || "—")}</b><div class="muted au-small">${esc(e.ip)}</div></td>
          <td><span class="badge ${alert ? "no" : e.event === "login_ok" ? "yes" : e.kind === "security" ? "au-sec" : "au-chg"}" title="${esc(t("au.kind." + e.kind))}">${esc(eventLabel(e.event))}</span>${reason}</td>
          <td>${esc(screenLabel(e.screen))}</td><td class="wrap">${esc(e.record)}</td><td class="muted wrap au-path">${esc(e.method)} ${esc(e.path)}</td>
          <td>${details ? `<button type="button" class="btn small" data-more="${e.id}">${esc(t(open === e.id ? "au.less" : "au.more"))}</button>` : ""}</td></tr>
          ${open === e.id ? `<tr class="au-detail"><td colspan="7"><pre>${esc(JSON.stringify(e.details, null, 2))}</pre></td></tr>` : ""}`;
      }).join("");
      const exportUrl = "api/audit/export?" + query({ page: "", size: "", lang });
      $("#view").innerHTML = pageHead(t("au.title"), t("au.subtitle"), helpButtonOf(SCREEN) + `<a class="btn" href="${exportUrl}" download>${esc(t("au.export"))}</a>`) + `
        <div class="card"><div class="toolbar au-filters">
          <label>${esc(t("au.from"))} <input type="date" id="auFrom" data-help-f="from" value="${esc(st.from)}"></label>
          <label>${esc(t("au.to"))} <input type="date" id="auTo" data-help-f="to" value="${esc(st.to)}"></label>
          <select id="auUser" data-help-f="user" aria-label="${esc(t("au.user"))}">${opt("", t("au.user") + ": " + t("common.all"), st.user)}${lists.users.map((u) => opt(u, u, st.user)).join("")}</select>
          <select id="auKind" data-help-f="kind" aria-label="${esc(t("au.kind"))}">${opt("", t("au.kind") + ": " + t("common.all"), st.kind)}${opt("security", t("au.kind.security"), st.kind)}${opt("change", t("au.kind.change"), st.kind)}</select>
          <select id="auEvent" data-help-f="event" aria-label="${esc(t("au.event"))}">${opt("", t("au.event") + ": " + t("common.all"), st.event)}${events.map((e) => opt(e, eventLabel(e), st.event)).join("")}</select>
          <input type="search" id="auQ" data-help-f="search" placeholder="${esc(t("au.search"))}" value="${esc(st.q)}">
          <span class="count">${esc(t("common.records", { n: fmtInt(data.total) }))}</span></div>
          <div class="table-wrap">${data.items.length ? `<table class="grid"><thead><tr><th>${esc(t("au.when"))}</th><th>${esc(t("au.user"))}</th><th>${esc(t("au.event"))}</th>
            <th>${esc(t("au.screen"))}</th><th>${esc(t("au.record"))}</th><th>${esc(t("au.path"))}</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
            : `<div class="empty">${esc(t("au.none"))}</div>`}</div>
          <div class="pager"><span>${esc(t("common.page", { p: data.page, n: pages }))}</span>
            <button class="btn small" id="auPrev" ${data.page <= 1 ? "disabled" : ""}>‹ ${esc(t("common.prev"))}</button>
            <button class="btn small" id="auNext" ${data.page >= pages ? "disabled" : ""}>${esc(t("common.next"))} ›</button></div></div>
        <p class="help">${esc(t("au.note"))}</p>`;
      decorateScreen(SCREEN);
      const reload = async (keepPage) => { if (!keepPage) st.page = 1; open = null; await this.load(); this.render(); };
      const on = (id, f, ev = "change") => $(id).addEventListener(ev, async (e) => { st[f] = e.target.value; if (f === "kind") st.event = ""; await reload(); });
      on("#auFrom", "from"); on("#auTo", "to"); on("#auUser", "user"); on("#auKind", "kind"); on("#auEvent", "event");
      let timer = null;
      $("#auQ").addEventListener("input", (e) => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          st.q = e.target.value;
          await reload();
          const q = $("#auQ"); q.focus(); q.setSelectionRange(q.value.length, q.value.length);
        }, 350);
      });
      $("#auPrev").addEventListener("click", async () => { st.page -= 1; await reload(true); });
      $("#auNext").addEventListener("click", async () => { st.page += 1; await reload(true); });
      $$("[data-more]").forEach((b) => b.addEventListener("click", () => { const id = Number(b.dataset.more); open = open === id ? null : id; this.render(); }));
    },
  };
}
