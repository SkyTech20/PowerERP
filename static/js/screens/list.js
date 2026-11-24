/* PowerERP: Generic list screen of a resource. */
import { $, $$, api, enc, esc, fmtInt, lang, t, toast } from "../core.js";
import { decorateHelp, helpButton } from "../helpui.js";
import { canOn } from "../menu.js";
import { RES } from "../registry.js";
import { canOpen } from "../router.js";
import { listState, pageHead, tabsHtml } from "../views.js";

// ---------- Generic list
export function listView(key) {
  const R = RES[key];
  const st = listState[key] = listState[key] || { q: "", page: 1, size: 25, sort: R.sort, dir: R.dir || "asc", filters: {} };
  let data = null;
  return {
    async load() {
      const params = new URLSearchParams({ q: st.q, page: st.page, size: st.size, sort: st.sort || "", dir: st.dir });
      Object.entries(st.filters).forEach(([k, v]) => { if (v !== "") params.set("f_" + k, v); });
      // Filters whose options come from a lookup (e.g. the warehouses)
      await Promise.all((R.filters || []).filter((f) => f.lookup && !f.options).map(async (f) => {
        f.options = (await api("lookups/" + f.lookup + "?lang=" + lang)).map((r) => [r.code, r.code]);
        f.raw = true;
      }));
      data = await api(R.api + "?" + params.toString());
    },
    render() {
      const pages = Math.max(1, Math.ceil(data.total / data.size));
      const head = R.columns.map((c) => {
        const arrow = st.sort === c.f ? `<span class="arrow">${st.dir === "desc" ? "▼" : "▲"}</span>` : "";
        return `<th class="sortable ${c.num ? "num" : ""}" data-sort="${c.f}">${esc(t(c.l))}${arrow}</th>`;
      }).join("");
      const ownHref = (r) => (R.rowHref ? R.rowHref(r) : R.route + "/" + String(R.id(r)).split("/").map(enc).join("/"));
      const href = (r) => { const h = ownHref(r); return R.rowHref && !canOpen(h) ? "" : h; }; // a link to a screen the role may not open: none
      const rows = data.items.map((r) => `<tr class="${R.noClick || !href(r) ? "" : "clickable"}" data-href="${esc(R.noClick ? "" : href(r))}">${R.columns.map((c) => {
        const v = r[c.f];
        const cell = c.fmt ? c.fmt(v, r) : esc(v);
        return `<td class="${c.num ? "num" : ""} ${c.wrap ? "wrap" : ""}">${cell}</td>`;
      }).join("")}</tr>`).join("");
      const filters = (R.filters || []).map((f) => `<select data-filter="${f.f}" aria-label="${esc(t(f.l))}" style="width:auto">
          <option value="">${esc(t(f.l))}: ${esc(t("common.all"))}</option>
          ${f.options.map(([v, l]) => `<option value="${esc(v)}" ${st.filters[f.f] === v ? "selected" : ""}>${esc(f.raw ? l : t(l))}</option>`).join("")}
        </select>`).join("");
      // R.listActions: buttons of the list (e.g. add the standard conversions), next to "New"
      const listActions = (R.listActions || []).filter((a) => canOn(R, a.perm || "create")).map((a) => `<button class="btn" data-list-action="${a.id}">${esc(t(a.l))}</button>`).join("");
      $("#view").innerHTML = pageHead(t(R.title), t(R.sub), helpButton(R) + listActions + (R.noNew || !canOn(R, "create") ? "" : `<a class="btn primary" href="#${R.route}/new">＋ ${esc(t("common.new"))}</a>`))
        + (R.tabset ? tabsHtml(R) : "")
        + `<div class="card"><div class="toolbar"><input type="search" id="q" placeholder="${esc(t("common.search"))}" value="${esc(st.q)}">${filters}
            <span class="count">${esc(t("common.records", { n: fmtInt(data.total) }))}</span></div>
          <div class="table-wrap">${data.items.length ? `<table class="grid"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>` : `<div class="empty">${esc(t("common.empty"))}</div>`}</div>
          ${R.footer ? R.footer(data) : ""}
          <div class="pager"><span>${esc(t("common.page", { p: data.page, n: pages }))}</span>
            <button class="btn small" id="prev" ${data.page <= 1 ? "disabled" : ""}>‹ ${esc(t("common.prev"))}</button>
            <button class="btn small" id="next" ${data.page >= pages ? "disabled" : ""}>${esc(t("common.next"))} ›</button></div></div>`;

      const reload = async () => { await this.load(); this.render(); };
      let timer = null;
      const q = $("#q");
      q.addEventListener("input", () => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          st.q = q.value; st.page = 1;
          await reload();
          const nq = $("#q"); nq.focus(); nq.setSelectionRange(nq.value.length, nq.value.length);
        }, 250);
      });
      $$("select[data-filter]").forEach((s) => s.addEventListener("change", () => { st.filters[s.dataset.filter] = s.value; st.page = 1; reload(); }));
      $$("th[data-sort]").forEach((th) => th.addEventListener("click", () => {
        const f = th.dataset.sort;
        if (st.sort === f) st.dir = st.dir === "asc" ? "desc" : "asc"; else { st.sort = f; st.dir = "asc"; }
        reload();
      }));
      $$("tr[data-href]").forEach((tr) => { if (tr.dataset.href) tr.addEventListener("click", () => { location.hash = "#" + tr.dataset.href; }); });
      $$("[data-list-action]").forEach((b) => b.addEventListener("click", async () => {
        const a = R.listActions.find((x) => x.id === b.dataset.listAction);
        b.disabled = true;
        try {
          const msg = await a.run();
          if (msg) toast(msg, "success");
          await reload();
        } catch (e) {
          toast(t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic"), "error");
          b.disabled = false;
        }
      }));
      $("#prev").addEventListener("click", () => { st.page--; reload(); });
      decorateHelp(R);
      $("#next").addEventListener("click", () => { st.page++; reload(); });
    },
  };
}
