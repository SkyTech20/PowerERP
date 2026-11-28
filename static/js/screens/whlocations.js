/* PowerERP: the Locations tab of a warehouse (Inventory > Warehouses): its locations, a new one, and
   Generate locations (every aisle x rack x level x bin of the ranges typed, coded zone-aisle-rack-level-bin). */
import { $, $$, api, enc, esc, t, toast } from "../core.js";
import { canOn } from "../menu.js";
import { RES } from "../registry.js";
import { setPrefill } from "../state.js";

export const LOCATION_TYPES = ["picking", "reserve", "receiving", "shipping", "quarantine", "staging"];
// The ranges of Generate locations: [part, label key, example from, example to]
export const GEN_PARTS = [
  ["cAisle", "f.loc.cAisle", "A", "C"],
  ["cRack", "f.loc.cRack", "01", "05"],
  ["cLevel", "f.loc.cLevel", "1", "4"],
  ["cBin", "f.loc.cBin", "", ""],
];
export const locationLink = (r) => "/inv/locations/" + enc(r.cWarehouse) + "/" + enc(r.cCode);

// The values of a range the way the server expands them (shown while typing: "A to C = 3")
export function rangeCount(first, last) {
  first = String(first || "").trim().toUpperCase();
  last = String(last || "").trim().toUpperCase();
  if (!first && !last) return 1;
  if (!first || !last || first === last) return 1;
  if (/^\d+$/.test(first) && /^\d+$/.test(last)) return +last >= +first ? +last - +first + 1 : 0;
  if (/^[A-Z]$/.test(first) && /^[A-Z]$/.test(last)) return last >= first ? last.charCodeAt(0) - first.charCodeAt(0) + 1 : 0;
  return 0;
}

const errText = (e) => {
  const k = "err." + (e.code || "generic");
  return t(k) !== k ? t(k, { n: e.detail || "" }) : t("err.generic");
};

function rowsHtml(rows) {
  if (!rows.length) return `<div class="empty">${esc(t("wh.loc.none"))}</div>`;
  const body = rows.map((r) => `<tr data-loc="${esc(locationLink(r))}" class="clickable">
      <td><b>${esc(r.cCode)}</b></td><td>${esc(r.cZone)}</td><td>${esc(r.cAisle)}</td><td>${esc(r.cRack)}</td><td>${esc(r.cLevel)}</td><td>${esc(r.cBin)}</td>
      <td>${esc(t("o.loc." + r.cType))}</td><td class="num">${esc(r.iPickSeq)}</td>
      <td>${r.lBlocked ? `<span class="badge no">${esc(t("f.loc.lBlocked"))}</span>` : ""}${r.lActive ? "" : ` <span class="badge">${esc(t("opt.inactive"))}</span>`}</td></tr>`).join("");
  return `<div class="table-wrap"><table class="grid"><thead><tr>
      <th>${esc(t("f.loc.cCode"))}</th><th>${esc(t("f.loc.cZone"))}</th><th>${esc(t("f.loc.cAisle"))}</th><th>${esc(t("f.loc.cRack"))}</th>
      <th>${esc(t("f.loc.cLevel"))}</th><th>${esc(t("f.loc.cBin"))}</th><th>${esc(t("f.loc.cType"))}</th><th class="num">${esc(t("f.loc.iPickSeq"))}</th><th></th>
    </tr></thead><tbody>${body}</tbody></table></div>`;
}

function generatorHtml() {
  const ranges = GEN_PARTS.map(([p, l, a, b]) => `<div class="field"><label for="gen-${p}From">${esc(t(l))} — ${esc(t("wh.gen.from"))}</label>
      <input type="text" id="gen-${p}From" data-gen="${p}From" data-help-f="gen.${p}From" placeholder="${esc(a)}" maxlength="6" autocomplete="off"></div>
    <div class="field"><label for="gen-${p}To">${esc(t(l))} — ${esc(t("wh.gen.to"))}</label>
      <input type="text" id="gen-${p}To" data-gen="${p}To" data-help-f="gen.${p}To" placeholder="${esc(b)}" maxlength="6" autocomplete="off"></div>`).join("");
  const types = LOCATION_TYPES.map((k) => `<option value="${k}" ${k === "reserve" ? "selected" : ""}>${esc(t("o.loc." + k))}</option>`).join("");
  return `<div class="card" id="genCard" hidden><div class="card-head"><h2>${esc(t("wh.gen.title"))}</h2></div>
    <div class="card-body"><p class="help muted section-help">${esc(t("wh.gen.help"))}</p>
      <div class="form-grid">
        <div class="field"><label for="gen-cZone">${esc(t("f.loc.cZone"))}</label><input type="text" id="gen-cZone" data-gen="cZone" data-help-f="gen.cZone" maxlength="10" autocomplete="off"></div>
        <div class="field"><label for="gen-cType">${esc(t("f.loc.cType"))}</label><select id="gen-cType" data-gen="cType" data-help-f="gen.cType">${types}</select></div>
        <div class="field span-2"><label class="check"><input type="checkbox" id="gen-lMixProducts" data-gen="lMixProducts" data-help-f="gen.lMixProducts" checked> ${esc(t("f.loc.lMixProducts"))}</label></div>
        ${ranges}
      </div>
      <div class="gen-result" id="genResult" aria-live="polite"></div>
      <div class="gen-actions"><button type="button" class="btn" id="genPreview">👁 ${esc(t("wh.gen.preview"))}</button>
        <button type="button" class="btn primary" id="genRun" disabled>${esc(t("wh.gen.run"))}</button>
        <button type="button" class="btn" id="genClose">${esc(t("common.cancel"))}</button></div>
    </div></div>`;
}

// The panel of the warehouse form (tab "locations")
export const warehouseLocationsPanel = {
  tab: "locations",
  onNew: true,
  html: () => `<div class="card" id="whLoc"><div class="card-head"><h2>${esc(t("wh.tab.locations"))}</h2>
      <span class="help muted" id="whLocCount"></span>
      <div class="loc-actions" id="whLocActions" hidden>
        <button type="button" class="btn small" id="whLocNew">＋ ${esc(t("loc.new"))}</button>
        <button type="button" class="btn small" id="whLocGen">⚙ ${esc(t("wh.gen.title"))}</button></div></div>
    <div class="toolbar" id="whLocTools" hidden><input type="search" id="whLocFind" data-help-f="locFind" aria-label="${esc(t("wh.loc.find"))}" placeholder="${esc(t("wh.loc.find"))}"></div>
    <div id="whLocBody"><div class="empty">${esc(t("common.loading"))}</div></div></div>${generatorHtml()}`,
  async bind(model, ctx) {
    const body = $("#whLocBody");
    if (!ctx.path) { // a new warehouse: its locations come once it is saved
      body.innerHTML = `<div class="empty">${esc(t("wh.loc.saveFirst"))}</div>`;
      return;
    }
    const code = model.cCode;
    const mayAdd = canOn(RES.locations, "create");
    $("#whLocActions").hidden = !mayAdd;
    let all = { items: [], total: 0 };
    const show = () => {
      const q = $("#whLocFind").value.trim().toLowerCase();
      const rows = q ? all.items.filter((r) => [r.cCode, r.cZone, r.cAisle, r.cRack, r.cLevel, r.cBin, r.cDescription].some((v) => String(v || "").toLowerCase().includes(q))) : all.items;
      body.innerHTML = rowsHtml(rows) + (all.total > all.items.length ? `<p class="help">${esc(t("wh.loc.more", { n: all.total - all.items.length }))}</p>` : "");
      $$("tr[data-loc]", body).forEach((tr) => tr.addEventListener("click", () => { location.hash = "#" + tr.dataset.loc; }));
    };
    const load = async () => {
      all = await api(`locations?f_cWarehouse=${enc(code)}&sort=iPickSeq&size=500`);
      $("#whLocCount").textContent = t("wh.loc.count", { n: all.total });
      $("#whLocTools").hidden = all.total < 10; // a search only where there is something to search
      show();
    };
    $("#whLocFind").addEventListener("input", show);
    try { await load(); } catch (e) { body.innerHTML = `<div class="empty">${esc(errText(e))}</div>`; }
    if (!mayAdd) return;
    $("#whLocNew").addEventListener("click", () => {
      setPrefill({ key: "locations", values: { cWarehouse: code } });
      location.hash = "#" + RES.locations.route + "/new";
    });
    const card = $("#genCard");
    const result = $("#genResult");
    const run = $("#genRun");
    const payload = () => {
      const p = {};
      $$("[data-gen]", card).forEach((el) => { p[el.dataset.gen] = el.type === "checkbox" ? el.checked : el.value.trim(); });
      return p;
    };
    // the number of locations while typing; Create waits for a fresh preview
    const estimate = () => {
      const p = payload();
      const n = GEN_PARTS.reduce((acc, [k]) => acc * rangeCount(p[k + "From"], p[k + "To"]), 1);
      run.disabled = true;
      result.innerHTML = p.cAisleFrom ? `<span class="muted">${esc(t("wh.gen.estimate", { n }))}</span>` : "";
    };
    $$("[data-gen]", card).forEach((el) => el.addEventListener(el.tagName === "SELECT" || el.type === "checkbox" ? "change" : "input", estimate));
    $("#whLocGen").addEventListener("click", () => { card.hidden = false; $("#gen-cZone").focus(); card.scrollIntoView({ block: "nearest" }); });
    $("#genClose").addEventListener("click", () => { card.hidden = true; });
    const call = async (preview) => {
      $$(".invalid", card).forEach((x) => x.classList.remove("invalid"));
      try {
        const r = await api(`warehouses/${enc(code)}/generate-locations${preview ? "?preview=1" : ""}`, { method: "POST", body: payload() });
        return r;
      } catch (e) {
        const el = e.field && $(`[data-gen="${e.field}"]`, card);
        if (el) { el.closest(".field").classList.add("invalid"); el.focus(); }
        result.innerHTML = `<span class="err">${esc(errText(e))}</span>`;
        run.disabled = true;
        return null;
      }
    };
    $("#genPreview").addEventListener("click", async () => {
      const r = await call(true);
      if (!r) return;
      const sample = r.codes.length > 8 ? [...r.codes.slice(0, 4), "…", ...r.codes.slice(-3)] : r.codes;
      result.innerHTML = `<p><b>${esc(t("wh.gen.willCreate", { n: r.iToCreate }))}</b>${r.iSkipped ? " " + esc(t("wh.gen.skipped", { n: r.iSkipped })) : ""}</p>
        ${sample.length ? `<p class="gen-codes">${sample.map((c) => `<code>${esc(c)}</code>`).join(" ")}</p>` : ""}`;
      run.disabled = !r.iToCreate;
      run.textContent = t("wh.gen.runN", { n: r.iToCreate });
    });
    run.addEventListener("click", async () => {
      run.disabled = true;
      const r = await call(false);
      if (!r) return;
      toast(t("wh.gen.done", { n: r.iCreated }), "success");
      card.hidden = true;
      result.innerHTML = "";
      await load();
    });
  },
};
