/* PowerERP: Production: list / form definitions. P1: the reference lists of the shop floor; P2: calendars. */
import { $, api, enc, esc, fmtDateTime, lang, numOnly, t, yesNo } from "../core.js";
import { RES } from "../registry.js";
import { descCol, dl, newWith, optBadge, opts, today } from "./inventory.js";

export const DOWNTIME_GROUPS = ["breakdown", "setup", "minor_stop", "reduced_speed", "no_material", "no_operator", "quality", "planned", "other"];
export const SCRAP_GROUPS = ["material", "process", "machine", "operator", "startup", "other"];

// A code list with descriptions FR / EN (and the extra columns / fields of each list)
function referenceList(key, api, route, extra = {}) {
  return {
    api, route, menu: "/prod/capabilities", tabset: "mfgsetup", title: "mfg.setup.title", sub: "mfg.setup.subtitle",
    one: `mfg.${key}.one`, newTitle: `mfg.${key}.new`, id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [{ f: "cCode", l: "f.cCode" }, descCol("cDesc"), ...(extra.columns || []), { f: "lActive", l: "opt.active", fmt: yesNo }],
    ...(extra.filters ? { filters: extra.filters } : {}),
    defaults: { lActive: true, ...(extra.defaults || {}) },
    sections: [{ t: "common.general", fields: [
      { f: "cCode", l: "f.cCode", req: true, key: true, help: "mfg.code.help" }, ...(extra.fields || []), { f: "lActive", l: "opt.active", type: "check" },
      { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
    ] }],
  };
}

const groupCol = (prefix) => ({ f: "cGroup", l: "mfg.f.cGroup", fmt: optBadge(prefix) });
const groupFilter = (prefix, values) => ({ f: "cGroup", l: "mfg.f.cGroup", options: opts(prefix, values) });

Object.assign(RES, {
  capabilities: referenceList("cap", "capabilities", "/prod/capabilities"),
  setupfamilies: referenceList("fam", "setup-families", "/prod/setup-families"),
  downtimereasons: referenceList("down", "downtime-reasons", "/prod/downtime-reasons", {
    columns: [groupCol("mfg.o.down."), { f: "lAffectsOEE", l: "mfg.f.lAffectsOEE", fmt: yesNo }],
    filters: [groupFilter("mfg.o.down.", DOWNTIME_GROUPS)],
    defaults: { cGroup: "breakdown", lAffectsOEE: true },
    fields: [
      { f: "cGroup", l: "mfg.f.cGroup", type: "select", options: opts("mfg.o.down.", DOWNTIME_GROUPS) },
      { f: "lAffectsOEE", l: "mfg.f.lAffectsOEE", type: "check", help: "mfg.f.lAffectsOEE.help" },
    ],
  }),
  scrapreasons: referenceList("scrap", "scrap-reasons", "/prod/scrap-reasons", {
    columns: [groupCol("mfg.o.scrap.")],
    filters: [groupFilter("mfg.o.scrap.", SCRAP_GROUPS)],
    defaults: { cGroup: "process" },
    fields: [{ f: "cGroup", l: "mfg.f.cGroup", type: "select", options: opts("mfg.o.scrap.", SCRAP_GROUPS) }],
  }),
});

// ------------------------------------------------------------------ P2: calendars
export const WEEKDAYS = [1, 2, 3, 4, 5, 6, 7];
const weekdayOpts = WEEKDAYS.map((d) => [String(d), "mfg.wd." + d]);
// 2250 -> "37.5 h" / "37,5 h"
export const hours = (min) => `${new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { maximumFractionDigits: 2 }).format((Number(min) || 0) / 60)} h`;
const monday = (iso) => { const d = new Date(iso + "T12:00:00"); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d.toISOString().slice(0, 10); };
const dayName = (iso) => new Date(iso + "T12:00:00").toLocaleDateString(lang === "fr" ? "fr-CA" : "en-CA", { weekday: "long", day: "numeric", month: "long" });

// The available time of a week, day by day (calendar, work center and resource screens). extra(r) adds rows after the total.
function weekPreview(url, extra = () => "") {
  return {
    html: () => `<div class="card"><div class="card-head"><h2>${esc(t("mfg.cal.preview"))}</h2><span class="help muted">${esc(t("mfg.cal.preview.help"))}</span></div>
      <div class="card-body"><div class="form-grid"><div class="field"><label for="calWeek">${esc(t("mfg.cal.weekOf"))}</label><input type="date" id="calWeek" value="${monday(today())}"></div></div>
      <div id="calPreview"></div></div></div>`,
    bind: (m) => {
      const run = async () => {
        const from = monday($("#calWeek").value || today());
        const to = new Date(from + "T12:00:00"); to.setDate(to.getDate() + 6);
        try {
          const r = await api(`${url(m)}?from=${from}&to=${to.toISOString().slice(0, 10)}`);
          $("#calPreview").innerHTML = `<table class="grid"><thead><tr><th>${esc(t("mfg.cal.day"))}</th><th>${esc(t("mfg.cal.shifts"))}</th><th class="num">${esc(t("mfg.cal.available"))}</th></tr></thead><tbody>
            ${r.days.map((d) => `<tr><td>${esc(dayName(d.dDate))}</td><td>${d.shifts.map((s) => `${s.cShift === "*" ? "" : esc(s.cShift) + " "}${esc(s.cStart)}–${esc(s.cEnd)}`).join(" · ")}
              ${d.cException ? ` <span class="badge ${d.lClosed ? "no" : ""}">${esc(lang === "fr" ? d.cException : d.cExceptionEN)}</span>` : ""}
              ${d.iDowntimeMinutes ? ` <span class="badge no">− ${esc(hours(d.iDowntimeMinutes))} ${esc(t("mfg.res.plannedStop"))}</span>` : ""}</td><td class="num">${esc(hours(d.iMinutes))}</td></tr>`).join("")}
            <tr class="total-row"><td colspan="2">${esc(t("mfg.cal.total"))}</td><td class="num">${esc(hours(r.iMinutes))}</td></tr>${extra(r)}</tbody></table>`;
        } catch (e) { $("#calPreview").innerHTML = ""; }
      };
      $("#calWeek").addEventListener("change", run);
      run();
    },
  };
}

Object.assign(RES, {
  calendars: {
    api: "calendars", route: "/prod/calendars", tabset: "mfgcal", title: "mfg.cal.title", sub: "mfg.cal.subtitle",
    one: "mfg.cal.one", newTitle: "mfg.cal.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [
      { f: "cCode", l: "f.cCode" }, descCol("cDesc"), { f: "iShifts", l: "mfg.cal.shifts", n: true },
      { f: "iWeekMinutes", l: "mfg.cal.week", n: true, fmt: (v) => esc(hours(v)) }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    defaults: () => ({ lActive: true, lines: [1, 2, 3, 4, 5].map((d) => ({ iWeekday: d, cShift: "", cStart: "07:00", cEnd: "15:30", iBreakMin: 30 })) }),
    sections: [{ t: "common.general", fields: [
      { f: "cCode", l: "f.cCode", req: true, key: true, help: "mfg.code.help" }, { f: "lActive", l: "opt.active", type: "check" },
      { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
    ] }],
    lines: {
      title: "mfg.cal.shifts", help: "mfg.cal.shifts.help",
      cols: [
        { f: "iWeekday", l: "mfg.f.iWeekday", w: "w-md", type: "select", options: weekdayOpts },
        { f: "cShift", l: "mfg.f.cShift", w: "w-md" },
        { f: "cStart", l: "mfg.f.cStart", w: "w-sm", type: "time" }, { f: "cEnd", l: "mfg.f.cEnd", w: "w-sm", type: "time" },
        { f: "iBreakMin", l: "mfg.f.iBreakMin", w: "w-sm", n: true },
      ],
      newLine: (m) => {
        const last = (m.lines || [])[(m.lines || []).length - 1];
        return last ? { ...last, iWeekday: (Number(last.iWeekday) % 7) + 1 } : { iWeekday: 1, cShift: "", cStart: "07:00", cEnd: "15:30", iBreakMin: 30 };
      },
    },
    panel: weekPreview((m) => `calendars/${enc(m.cCode)}/availability`),
  },
  calexceptions: {
    api: "calendar-exceptions", route: "/prod/calendar-exceptions", menu: "/prod/calendars", tabset: "mfgcal", title: "mfg.cal.title", sub: "mfg.cal.subtitle",
    one: "mfg.exc.one", newTitle: "mfg.exc.new", id: (r) => `${r.cCalendar}/${r.dDate}`, label: (r) => `${r.dDate} — ${dl(r, "cDesc")}`, sort: "dDate",
    columns: [
      { f: "dDate", l: "mfg.f.dDate" }, { f: "cCalendar", l: "mfg.f.cCalendar", fmt: (v) => esc(v === "*" ? t("mfg.exc.all") : v) }, descCol("cDesc"),
      { f: "lClosed", l: "mfg.f.lClosed", fmt: (v, r) => (v ? `<span class="badge no">${esc(t("mfg.exc.closed"))}</span>` : `${esc(r.cStart)}–${esc(r.cEnd)}`) },
    ],
    filters: [{ f: "cCalendar", l: "mfg.f.cCalendar", lookup: "calendars" }],
    defaults: () => ({ cCalendar: "", dDate: today(), lClosed: true, cStart: "", cEnd: "", iBreakMin: 0 }),
    sections: [{ t: "common.general", fields: [
      { f: "cCalendar", l: "mfg.f.cCalendar", key: true, lookup: "calendars", help: "mfg.exc.all.help" },
      { f: "dDate", l: "mfg.f.dDate", req: true, key: true, type: "date" },
      { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
      { f: "lClosed", l: "mfg.f.lClosed", type: "check", rerender: true, help: "mfg.f.lClosed.help" },
      { f: "cStart", l: "mfg.f.cStart", type: "time", show: (m) => !m.lClosed }, { f: "cEnd", l: "mfg.f.cEnd", type: "time", show: (m) => !m.lClosed },
      { f: "iBreakMin", l: "mfg.f.iBreakMin", type: "number", show: (m) => !m.lClosed },
    ] }],
  },
});

// ------------------------------------------------------------------ P3: work centers
export const WORK_CENTER_TYPES = ["machine", "line", "labor", "subcontract"];
const notSub = (m) => m.cType !== "subcontract";

Object.assign(RES, {
  workcenters: {
    api: "work-centers", route: "/prod/work-centers", title: "mfg.wc.title", sub: "mfg.wc.subtitle",
    one: "mfg.wc.one", newTitle: "mfg.wc.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [
      { f: "cCode", l: "f.cCode" }, descCol("cDesc"), { f: "cType", l: "mfg.f.cType", fmt: optBadge("mfg.o.wc.") },
      { f: "cCalendar", l: "mfg.f.cCalendar" }, { f: "lFinite", l: "mfg.f.lFinite", fmt: yesNo },
      { f: "dRunRateHr", l: "mfg.f.dRunRateHr", n: true }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    filters: [{ f: "cType", l: "mfg.f.cType", options: opts("mfg.o.wc.", WORK_CENTER_TYPES) }, { f: "cCalendar", l: "mfg.f.cCalendar", lookup: "calendars" }],
    defaults: { cType: "machine", lFinite: true, dEfficiencyPct: "100", dUtilizationPct: "100", iQueueMin: 0, iMoveMin: 0, lActive: true },
    sections: [
      { t: "common.general", fields: [
        { f: "cCode", l: "f.cCode", req: true, key: true, help: "mfg.code.help" },
        { f: "cType", l: "mfg.f.cType", type: "select", options: opts("mfg.o.wc.", WORK_CENTER_TYPES), rerender: true },
        { f: "lActive", l: "opt.active", type: "check" },
        { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
        { f: "cSupplier", l: "mfg.f.cSupplier", lookup: "suppliers", req: true, show: (m) => m.cType === "subcontract", help: "mfg.f.cSupplier.help" },
      ] },
      { t: "mfg.wc.capacity", help: "mfg.wc.capacity.help", fields: [
        { f: "cCalendar", l: "mfg.f.cCalendar", lookup: "calendars", req: true, show: notSub },
        { f: "lFinite", l: "mfg.f.lFinite", type: "check", help: "mfg.f.lFinite.help", show: notSub },
        { f: "dEfficiencyPct", l: "mfg.f.dEfficiencyPct", type: "number", help: "mfg.f.dEfficiencyPct.help" },
        { f: "dUtilizationPct", l: "mfg.f.dUtilizationPct", type: "number", help: "mfg.f.dUtilizationPct.help", show: notSub },
        { f: "iQueueMin", l: "mfg.f.iQueueMin", type: "number", help: "mfg.f.iQueueMin.help" },
        { f: "iMoveMin", l: "mfg.f.iMoveMin", type: "number", help: "mfg.f.iMoveMin.help" },
      ] },
      { t: "mfg.wc.costs", help: "mfg.wc.costs.help", fields: [
        { f: "dSetupRateHr", l: "mfg.f.dSetupRateHr", type: "number" }, { f: "dRunRateHr", l: "mfg.f.dRunRateHr", type: "number" },
        { f: "dBurdenRateHr", l: "mfg.f.dBurdenRateHr", type: "number" }, { f: "cCostCenter", l: "f.prod.cCostCenter", lookup: "cc" },
      ] },
      { t: "mfg.wc.stock", help: "mfg.wc.stock.help", fields: [
        { f: "cWarehouse", l: "f.inv.cWarehouse", lookup: "warehouses", rerender: true },
        { f: "cInLocation", l: "mfg.f.cInLocation", lookup: "locations", lookupParams: (m) => ({ wh: m.cWarehouse }) },
        { f: "cOutLocation", l: "mfg.f.cOutLocation", lookup: "locations", lookupParams: (m) => ({ wh: m.cWarehouse }) },
      ] },
      { t: "mfg.wc.notes", fields: [{ f: "cNotes", l: "mfg.f.cNotes", type: "textarea", span: 4 }] },
    ],
    panel: withResources(weekPreview((m) => `work-centers/${enc(m.cCode)}/availability`, (r) => `<tr><td colspan="2">${esc(t("mfg.wc.capacityTotal"))}</td><td class="num">${esc(hours(r.iCapacityMinutes))}</td></tr>`)),
  },
});

// ------------------------------------------------------------------ P4: resources
// The resources of a work center, listed above another panel (the week preview)
function withResources(panel) {
  return {
    html: (m) => `<div class="card"><div class="card-head"><h2>${esc(t("mfg.res.title"))}</h2>
        <a class="btn small" style="margin-left:auto" href="#/prod/resources/new" id="wcNewRes">＋ ${esc(t("mfg.res.new"))}</a></div>
      <div id="wcResources"></div></div>` + panel.html(m),
    bind: (m) => {
      api(`resources?f_cWorkCenter=${enc(m.cCode)}&sort=cCode&size=200`).then((r) => {
        $("#wcResources").innerHTML = r.items.length
          ? `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("f.cCode"))}</th><th>${esc(t("f.cDescription"))}</th><th>${esc(t("mfg.res.caps"))}</th><th class="num">${esc(t("mfg.f.dSpeedFactor"))}</th><th class="num">${esc(t("mfg.f.iParallel"))}</th></tr></thead><tbody>
            ${r.items.map((x) => `<tr><td><a href="#/prod/resources/${enc(x.cCode)}">${esc(x.cCode)}</a></td><td>${esc(dl(x, "cDesc"))}</td><td>${esc(x.cCapabilities)}</td><td class="num">${esc(x.dSpeedFactor)}</td><td class="num">${esc(x.iParallel)}</td></tr>`).join("")}</tbody></table></div>`
          : `<div class="empty">${esc(t("mfg.res.none"))}</div>`;
      }).catch(() => {});
      const add = $("#wcNewRes");
      if (add) add.addEventListener("click", (e) => { e.preventDefault(); newWith("resources", { cWorkCenter: m.cCode }); });
      panel.bind(m);
    },
  };
}

Object.assign(RES, {
  resources: {
    api: "resources", route: "/prod/resources", title: "mfg.res.title", sub: "mfg.res.subtitle",
    one: "mfg.res.one", newTitle: "mfg.res.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [
      { f: "cCode", l: "f.cCode" }, descCol("cDesc"), { f: "cWorkCenter", l: "mfg.f.cWorkCenter" },
      { f: "cCapabilities", l: "mfg.res.caps" }, { f: "dSpeedFactor", l: "mfg.f.dSpeedFactor", n: true },
      { f: "iParallel", l: "mfg.f.iParallel", n: true }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    filters: [{ f: "cWorkCenter", l: "mfg.f.cWorkCenter", lookup: "work_centers" }],
    defaults: () => ({ dSpeedFactor: "1", iParallel: 1, lActive: true, capabilities: [], attributes: [], subresources: [], downtime: [] }),
    formTabs: [["gen", "common.general"], ["caps", "mfg.res.tab.caps"], ["parts", "mfg.res.tab.parts"], ["down", "mfg.res.tab.downtime"], ["time", "mfg.cal.preview"]],
    sections: [
      { tab: "gen", t: "common.general", fields: [
        { f: "cCode", l: "f.cCode", req: true, key: true, help: "mfg.code.help" },
        { f: "cWorkCenter", l: "mfg.f.cWorkCenter", req: true, lookup: "work_centers" },
        { f: "lActive", l: "opt.active", type: "check" },
        { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
      ] },
      { tab: "gen", t: "mfg.wc.capacity", help: "mfg.res.capacity.help", fields: [
        { f: "cCalendar", l: "mfg.f.cCalendar", lookup: "calendars", help: "mfg.f.cCalendarRes.help" },
        { f: "dSpeedFactor", l: "mfg.f.dSpeedFactor", type: "number", help: "mfg.f.dSpeedFactor.help" },
        { f: "iParallel", l: "mfg.f.iParallel", type: "number", help: "mfg.f.iParallel.help" },
      ] },
      { tab: "gen", t: "mfg.res.machine", fields: [
        { f: "cManufacturer", l: "mfg.f.cManufacturer" }, { f: "cModel", l: "mfg.f.cModel" }, { f: "cSerialNo", l: "mfg.f.cSerialNo" },
        { f: "cNotes", l: "mfg.f.cNotes", type: "textarea", span: 4 },
      ] },
    ],
    grids: [
      { key: "capabilities", tab: "caps", title: "mfg.res.caps", help: "mfg.res.caps.help",
        cols: [{ f: "cCapability", l: "mfg.res.cap", w: "w-lg", lookup: "capabilities" }, { f: "iPreference", l: "mfg.f.iPreference", w: "w-sm", n: true }],
        newLine: (m) => ({ cCapability: "", iPreference: (m.capabilities || []).length + 1 }) },
      { key: "attributes", tab: "caps", title: "mfg.res.attrs", help: "mfg.res.attrs.help",
        cols: [{ f: "cAttribute", l: "mfg.f.cAttribute", w: "w-md" }, { f: "cUOM", l: "mfg.f.cUOM", w: "w-sm" },
          { f: "dMin", l: "mfg.f.dMin", w: "w-sm", n: true }, { f: "dMax", l: "mfg.f.dMax", w: "w-sm", n: true }, { f: "cValue", l: "mfg.f.cValue", w: "w-md" }],
        newLine: () => ({ cAttribute: "", cUOM: "", dMin: "", dMax: "", cValue: "" }) },
      { key: "subresources", tab: "parts", title: "mfg.res.parts", help: "mfg.res.parts.help",
        cols: [{ f: "cCode", l: "f.cCode", w: "w-sm" }, { f: "cDescFR", l: "f.cDescFR", w: "w-lg" }, { f: "cDescEN", l: "f.cDescEN", w: "w-lg" }],
        newLine: () => ({ cCode: "", cDescFR: "", cDescEN: "" }) },
      { key: "downtime", tab: "down", title: "mfg.res.tab.downtime", help: "mfg.res.downtime.help",
        cols: [{ f: "dStart", l: "mfg.f.dStart", w: "w-md", type: "date" }, { f: "cStartTime", l: "mfg.f.cStart", w: "w-sm", type: "time" },
          { f: "dEnd", l: "mfg.f.dEnd", w: "w-md", type: "date" }, { f: "cEndTime", l: "mfg.f.cEnd", w: "w-sm", type: "time" },
          { f: "cReason", l: "mfg.f.cReason", w: "w-md", lookup: "downtime_reasons" }, { f: "cNotes", l: "mfg.f.cNotes", w: "w-lg" }],
        newLine: () => ({ dStart: today(), cStartTime: "07:00", dEnd: today(), cEndTime: "11:00", cReason: "", cNotes: "" }) },
    ],
    panel: { tab: "time", ...weekPreview((m) => `resources/${enc(m.cCode)}/availability`, (r) => `
      <tr><td colspan="2">${esc(t("mfg.res.plannedStops"))}</td><td class="num">− ${esc(hours(r.iDowntimeMinutes))}</td></tr>
      <tr><td colspan="2">${esc(t("mfg.res.capacityTotal"))}</td><td class="num">${esc(hours(r.iCapacityMinutes))}</td></tr>`) },
  },
});

// ------------------------------------------------------------------ P5: standard operations
export const RUN_FORMATS = ["min_per_unit", "units_per_hour", "min_per_lot"];
const fmtNum = (v) => new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { maximumFractionDigits: 2 }).format(Number(v) || 0);
const minutesText = (m) => `${fmtNum(m)} min${Number(m) >= 60 ? ` (${hours(m)})` : ""}`;

// Time of a quantity, at the standard or on a resource (its speed and the efficiency of its work center)
const timeCalculator = {
  html: (m) => `<div class="card"><div class="card-head"><h2>${esc(t("mfg.op.calc"))}</h2><span class="help muted">${esc(t("mfg.op.calc.help"))}</span></div>
    <div class="card-body"><div class="form-grid">
      <div class="field"><label for="opQty">${esc(t("mfg.op.qty"))}</label><input type="text" id="opQty" inputmode="decimal" value="100" style="text-align:right"></div>
      ${m.cRunFormat === "min_per_lot" ? `<div class="field"><label for="opLot">${esc(t("mfg.op.lot"))}</label><input type="text" id="opLot" inputmode="decimal" value="" style="text-align:right"><span class="help">${esc(t("mfg.op.lot.help"))}</span></div>` : ""}
      <div class="field"><label for="opRes">${esc(t("mfg.res.one"))}</label><select id="opRes"><option value="">${esc(t("mfg.op.standard"))}</option></select></div>
    </div><div id="opTime"></div></div></div>`,
  bind: (m) => {
    const run = async () => {
      const lot = $("#opLot") ? `&lot=${enc($("#opLot").value)}` : "";
      try {
        const r = await api(`operations/${enc(m.cCode)}/time?qty=${enc($("#opQty").value || "0")}${lot}&resource=${enc($("#opRes").value)}`);
        $("#opTime").innerHTML = `<table class="grid"><tbody>
          <tr><td>${esc(t("mfg.f.dSetupMin"))}</td><td class="num">${esc(minutesText(r.dSetupMin))}</td></tr>
          <tr><td>${esc(t("mfg.op.run"))}</td><td class="num">${esc(minutesText(r.dRunMin))}</td></tr>
          <tr class="total-row"><td>${esc(t("mfg.op.total"))}</td><td class="num">${esc(minutesText(r.dTotalMin))}</td></tr>
          <tr><td>${esc(t("mfg.op.labor"))}</td><td class="num">${esc(minutesText(r.dLaborMin))}</td></tr></tbody></table>`;
      } catch (e) { $("#opTime").innerHTML = ""; }
    };
    // the resources that can run it: those with the capability, else those of the work center
    const fill = (rows) => { $("#opRes").innerHTML += rows.map((x) => `<option value="${esc(x.cCode)}">${esc(x.cCode)} — ${esc(dl(x, "cDesc"))}</option>`).join(""); };
    if (m.cCapability) api(`capabilities/${enc(m.cCapability)}/resources`).then(fill).catch(() => {});
    else if (m.cWorkCenter) api(`resources?f_cWorkCenter=${enc(m.cWorkCenter)}&size=200`).then((r) => fill(r.items)).catch(() => {});
    ["#opQty", "#opLot"].forEach((id) => { if ($(id)) $(id).addEventListener("input", (e) => { numOnly(e.target); run(); }); });
    $("#opRes").addEventListener("change", run);
    run();
  },
};
const sub = (m) => !!m.lSubcontract;
const inHouse = (m) => !m.lSubcontract;

Object.assign(RES, {
  operations: {
    api: "operations", route: "/prod/operations", title: "mfg.op.title", sub: "mfg.op.subtitle",
    one: "mfg.op.one", newTitle: "mfg.op.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [
      { f: "cCode", l: "f.cCode" }, descCol("cDesc"),
      { f: "cWorkCenter", l: "mfg.op.where", fmt: (v, r) => esc(r.lSubcontract ? `${t("mfg.o.wc.subcontract")} ${r.cSupplier}` : v || `${t("mfg.res.cap")} ${r.cCapability}`) },
      { f: "dRunValue", l: "mfg.f.dRunValue", n: true, fmt: (v, r) => `${esc(fmtNum(v))} <span class="muted">${esc(t("mfg.o.run." + r.cRunFormat))}</span>` },
      { f: "dSetupMin", l: "mfg.f.dSetupMin", n: true, fmt: (v) => esc(fmtNum(v)) }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    filters: [{ f: "cWorkCenter", l: "mfg.f.cWorkCenter", lookup: "work_centers" }, { f: "cCapability", l: "mfg.res.cap", lookup: "capabilities" }],
    defaults: { cRunFormat: "min_per_unit", iCrew: 1, lReportingPoint: true, lSubcontract: false, lActive: true },
    sections: [
      { t: "common.general", fields: [
        { f: "cCode", l: "f.cCode", req: true, key: true, help: "mfg.code.help" }, { f: "lActive", l: "opt.active", type: "check" },
        { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
      ] },
      { t: "mfg.op.where", help: "mfg.op.where.help", fields: [
        { f: "lSubcontract", l: "mfg.f.lSubcontract", type: "check", rerender: true },
        { f: "cWorkCenter", l: "mfg.f.cWorkCenter", lookup: "work_centers", show: inHouse },
        { f: "cCapability", l: "mfg.res.cap", lookup: "capabilities", show: inHouse },
        { f: "cSupplier", l: "mfg.f.cSupplier", lookup: "suppliers", req: true, show: sub },
        { f: "dSubcontractCost", l: "mfg.f.dSubcontractCost", type: "number", show: sub },
        { f: "iSubcontractDays", l: "mfg.f.iSubcontractDays", type: "number", show: sub },
      ] },
      { t: "mfg.op.time", help: "mfg.op.time.help", fields: [
        { f: "cRunFormat", l: "mfg.f.cRunFormat", type: "select", options: opts("mfg.o.run.", RUN_FORMATS), rerender: true },
        { f: "dRunValue", l: "mfg.f.dRunValue", type: "number", help: "mfg.f.dRunValue.help" },
        { f: "dSetupMin", l: "mfg.f.dSetupMin", type: "number" },
        { f: "iCrew", l: "mfg.f.iCrew", type: "number", help: "mfg.f.iCrew.help" },
        { f: "lReportingPoint", l: "mfg.f.lReportingPoint", type: "check", help: "mfg.f.lReportingPoint.help" },
      ] },
      { t: "mfg.op.instruction", help: "mfg.op.instruction.help", fields: [
        { f: "cInstructionFR", l: "mfg.f.cInstructionFR", type: "textarea", span: 2 }, { f: "cInstructionEN", l: "mfg.f.cInstructionEN", type: "textarea", span: 2 },
      ] },
    ],
    panel: timeCalculator,
  },
});

// ------------------------------------------------------------------ P6: setup matrix
export const SETUP_SCOPES = ["work_center", "resource"];
const cellTitle = (c) => (c.cRule === "matrix" ? `${t("mfg.sm.rule.matrix")} ${c.cFromFamily} → ${c.cToFamily}` : t("mfg.sm.rule." + c.cRule));

// The family x family grid of a matrix, and a test of one changeover
const setupGrid = {
  html: () => `<div class="card"><div class="card-head"><h2>${esc(t("mfg.sm.grid"))}</h2><span class="help muted">${esc(t("mfg.sm.grid.help"))}</span></div>
    <div class="card-body"><div class="form-grid">
      <div class="field"><label for="smDefault">${esc(t("mfg.sm.default"))}</label><input type="text" id="smDefault" inputmode="decimal" value="30" style="text-align:right"><span class="help">${esc(t("mfg.sm.default.help"))}</span></div>
    </div><div id="smGrid" class="table-wrap"></div></div></div>`,
  bind: (m) => {
    const run = async () => {
      try {
        const g = await api(`setup-matrices/${enc(m.cScope)}/${enc(m.cScopeCode)}/grid?default=${enc($("#smDefault").value || "0")}`);
        $("#smGrid").innerHTML = `<table class="grid"><thead><tr><th>${esc(t("mfg.sm.fromTo"))}</th>${g.families.map((f) => `<th class="num">${esc(f)}</th>`).join("")}</tr></thead><tbody>
          ${g.families.map((a, i) => `<tr><th>${esc(a)}</th>${g.cells[i].map((c) => `<td class="num ${c.cRule === "matrix" ? "" : "muted"}" title="${esc(cellTitle(c))}">${esc(fmtNum(c.dSetupMin))}${c.cRule === "matrix" && (c.cFromFamily === "*" || c.cToFamily === "*") ? "*" : ""}</td>`).join("")}</tr>`).join("")}
          </tbody></table><p class="help muted">${esc(t("mfg.sm.grid.legend"))}</p>`;
      } catch (e) { $("#smGrid").innerHTML = ""; }
    };
    $("#smDefault").addEventListener("input", (e) => { numOnly(e.target); run(); });
    run();
  },
};
const isWc = (m) => m.cScope !== "resource";

Object.assign(RES, {
  setupmatrices: {
    api: "setup-matrices", route: "/prod/setup-matrix", title: "mfg.sm.title", sub: "mfg.sm.subtitle",
    one: "mfg.sm.one", newTitle: "mfg.sm.new", id: (r) => `${r.cScope}/${r.cScopeCode}`, label: (r) => `${t("mfg.o.scope." + r.cScope)} ${r.cScopeCode}`, sort: "cScopeCode",
    columns: [
      { f: "cScope", l: "mfg.f.cScope", fmt: optBadge("mfg.o.scope.") }, { f: "cScopeCode", l: "f.cCode" },
      { f: "cNotes", l: "mfg.f.cNotes", wrap: true }, { f: "iPairs", l: "mfg.sm.pairs", n: true }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    filters: [{ f: "cScope", l: "mfg.f.cScope", options: opts("mfg.o.scope.", SETUP_SCOPES) }],
    defaults: () => ({ cScope: "work_center", cScopeCode: "", lActive: true, lines: [{ cFromFamily: "*", cToFamily: "*", dSetupMin: "30", dSetupCost: "", dScrapQty: "" }] }),
    sections: [{ t: "common.general", help: "mfg.sm.help", fields: [
      { f: "cScope", l: "mfg.f.cScope", key: true, type: "select", options: opts("mfg.o.scope.", SETUP_SCOPES), rerender: true },
      { f: "cScopeCode", l: "mfg.f.cWorkCenter", key: true, req: true, lookup: "work_centers", show: isWc },
      { f: "cScopeCode", l: "mfg.res.one", key: true, req: true, lookup: "resources", show: (m) => !isWc(m) },
      { f: "lActive", l: "opt.active", type: "check" },
      { f: "cNotes", l: "mfg.f.cNotes", type: "textarea", span: 4 },
    ] }],
    lines: {
      title: "mfg.sm.pairs", help: "mfg.sm.pairs.help",
      cols: [
        { f: "cFromFamily", l: "mfg.f.cFromFamily", w: "w-md", lookup: "setup_families" }, { f: "cToFamily", l: "mfg.f.cToFamily", w: "w-md", lookup: "setup_families" },
        { f: "dSetupMin", l: "mfg.f.dSetupMin", w: "w-sm", n: true }, { f: "dSetupCost", l: "mfg.f.dSetupCost", w: "w-sm", n: true },
        { f: "dScrapQty", l: "mfg.f.dScrapQty", w: "w-sm", n: true },
      ],
      newLine: () => ({ cFromFamily: "", cToFamily: "", dSetupMin: "", dSetupCost: "", dScrapQty: "" }),
    },
    panel: setupGrid,
  },
});

// ------------------------------------------------------------------ P7: manufacturing data of the products
export const MAKE_BUY = ["make", "buy", "both"];
export const TRACE_LEVELS = ["none", "lot", "serial"];

Object.assign(RES, {
  productmfg: {
    api: "product-mfg", route: "/prod/items", title: "mfg.pm.title", sub: "mfg.pm.subtitle",
    one: "mfg.pm.one", newTitle: "mfg.pm.new", id: (r) => r.cProduct, label: (r) => `${r.cProduct} — ${dl(r, "cDesc")}`, sort: "cProduct",
    columns: [
      { f: "cProduct", l: "mfg.f.cProduct" }, descCol("cDesc"), { f: "cMakeBuy", l: "mfg.f.cMakeBuy", fmt: optBadge("mfg.o.mb.") },
      { f: "cSetupFamily", l: "mfg.f.cSetupFamily" }, { f: "dMfgLotMin", l: "mfg.f.dMfgLotMin", n: true, fmt: (v) => esc(v ? fmtNum(v) : "") },
      { f: "iMfgLeadDays", l: "mfg.f.iMfgLeadDays", n: true }, { f: "cTraceLevel", l: "mfg.f.cTraceLevel", fmt: (v) => esc(t("mfg.o.trace." + v)) },
    ],
    filters: [{ f: "cMakeBuy", l: "mfg.f.cMakeBuy", options: opts("mfg.o.mb.", MAKE_BUY) }, { f: "cSetupFamily", l: "mfg.f.cSetupFamily", lookup: "setup_families" }],
    defaults: () => ({ cMakeBuy: "make", cTraceLevel: "lot", lPhantom: false, iMfgLeadDays: 0, attributes: [] }),
    sections: [
      { t: "mfg.pm.mfg", fields: [
        { f: "cProduct", l: "mfg.f.cProduct", req: true, key: true, lookup: "products" },
        { f: "cMakeBuy", l: "mfg.f.cMakeBuy", type: "select", options: opts("mfg.o.mb.", MAKE_BUY) },
        { f: "lPhantom", l: "mfg.f.lPhantom", type: "check", help: "mfg.f.lPhantom.help" },
        { f: "cSetupFamily", l: "mfg.f.cSetupFamily", lookup: "setup_families", help: "mfg.f.cSetupFamily.help" },
      ] },
      { t: "mfg.pm.lots", help: "mfg.pm.lots.help", fields: [
        { f: "dMfgLotMin", l: "mfg.f.dMfgLotMin", type: "number" }, { f: "dMfgLotMultiple", l: "mfg.f.dMfgLotMultiple", type: "number" },
        { f: "iMfgLeadDays", l: "mfg.f.iMfgLeadDays", type: "number" },
      ] },
      { t: "mfg.pm.trace", help: "mfg.pm.trace.help", fields: [
        { f: "cTraceLevel", l: "mfg.f.cTraceLevel", type: "select", options: opts("mfg.o.trace.", TRACE_LEVELS) },
        { f: "cNotes", l: "mfg.f.cNotes", type: "textarea", span: 4 },
      ] },
    ],
    grids: [
      { key: "attributes", title: "mfg.res.attrs", help: "mfg.pm.attrs.help",
        cols: [{ f: "cAttribute", l: "mfg.f.cAttribute", w: "w-md" }, { f: "cUOM", l: "mfg.f.cUOM", w: "w-sm" },
          { f: "dNumber", l: "mfg.f.dNumber", w: "w-sm", n: true }, { f: "cValue", l: "mfg.f.cValueText", w: "w-md" }],
        newLine: () => ({ cAttribute: "", cUOM: "", dNumber: "", cValue: "" }) },
    ],
  },
});

// The "Manufacturing" tab of the product screen (Inventory > Products): a summary and a link to the data above
if (RES.products) {
  RES.products.formTabs = [...RES.products.formTabs, ["mfg", "mfg.pm.tab"]];
  RES.products.panels = [...(RES.products.panels || []), {
    tab: "mfg",
    html: () => `<div class="card"><div class="card-head"><h2>${esc(t("mfg.pm.tab"))}</h2><span class="help muted">${esc(t("mfg.pm.tab.help"))}</span><span id="pmAction" style="margin-left:auto"></span></div>
      <div class="card-body" id="pmSummary"><div class="empty">…</div></div></div>`,
    bind: (m) => {
      api(`product-mfg/${enc(m.cCode)}`).then((r) => {
        $("#pmAction").innerHTML = `<a class="btn small" href="#/prod/items/${enc(m.cCode)}">${esc(t("mfg.pm.edit"))} →</a>`;
        const row = (l, v) => `<tr><td>${esc(t(l))}</td><td>${v}</td></tr>`;
        $("#pmSummary").innerHTML = `<table class="grid"><tbody>
          ${row("mfg.f.cMakeBuy", esc(t("mfg.o.mb." + r.cMakeBuy)) + (r.lPhantom ? ` <span class="badge">${esc(t("mfg.f.lPhantom"))}</span>` : ""))}
          ${row("mfg.f.cSetupFamily", esc(r.cSetupFamily))}
          ${row("mfg.pm.lots", esc(`${r.dMfgLotMin ? fmtNum(r.dMfgLotMin) : "—"} / ${r.dMfgLotMultiple ? fmtNum(r.dMfgLotMultiple) : "—"} ${r.cStockUOM} · ${r.iMfgLeadDays} ${t("mfg.pm.days")}`))}
          ${row("mfg.f.cTraceLevel", esc(t("mfg.o.trace." + r.cTraceLevel)))}
          ${row("mfg.res.attrs", esc((r.attributes || []).map((a) => `${a.cAttribute} ${a.dNumber ? fmtNum(a.dNumber) : ""}${a.cUOM ? " " + a.cUOM : ""}${a.cValue ? " " + a.cValue : ""}`.trim()).join(" · ")))}
          </tbody></table>`;
      }).catch(() => {
        $("#pmSummary").innerHTML = `<div class="empty">${esc(t("mfg.pm.none"))}</div>`;
        $("#pmAction").innerHTML = `<button class="btn small" id="pmAdd">＋ ${esc(t("mfg.pm.add"))}</button>`;
        $("#pmAdd").addEventListener("click", () => newWith("productmfg", { cProduct: m.cCode }));
      });
    },
  }];
}

// ------------------------------------------------------------------ P8: recipes
export const RECIPE_STATUS = ["draft", "in_review", "approved", "obsolete"];
export const PROCESS_TYPES = ["discrete", "batch", "continuous"];
export const ISSUE_METHODS = ["manual", "backflush", "pick"];
export const OUTPUT_KINDS = ["coproduct", "byproduct"];
const statusBadge = (v) => `<span class="badge ${v === "approved" ? "yes" : v === "obsolete" ? "no" : ""}">${esc(t("mfg.o.rs." + v))}</span>`;

export const STEP_KINDS = ["instruction", "material_add", "parameter", "measure", "check", "timer", "output", "signature"];
export const STEP_DATA_TYPES = ["number", "text", "yes_no", "list", "photo"];
export const STEP_ON_FAIL = ["block", "warn", "hold_lot"];
export const STEP_FREQUENCIES = ["once", "every_n_units", "every_n_min", "per_lot"];
const STEP_ICON = { instruction: "📄", material_add: "⚖️", parameter: "🎛️", measure: "📏", check: "☑️", timer: "⏱️", output: "🏷️", signature: "✍️" };

// The steps tab: a list of the steps (by operation) and a panel with the fields of the kind of the selected step.
// The fields a kind does not use are hidden (the server clears the material and the critical flag where unused).
const VALUED_KINDS = ["parameter", "measure", "check"];
const stepOps = (m) => (m.operations || []).map((o) => [String(o.iOpSeq), `${o.iOpSeq} — ${dl(o, "cDesc") || o.cOperation || ""}`]);
const stepMaterials = (s, m) => {
  const ops = (m.operations || []).map((o) => Number(o.iOpSeq) || 0);
  const first = ops.length ? Math.min(...ops) : 0;
  return [["0", ""], ...(m.materials || []).filter((x) => String(Number(x.iOpSeq) || first) === String(s.iOpSeq))
    .map((x) => [String(x.iSeq), `${x.iSeq} · ${x.cComponent} ${fmtNum(x.dQtyPer)} ${x.cUOM || ""}`.trim()])];
};
export const stepSections = (s, m) => {
  const kind = s.cKind;
  const valued = VALUED_KINDS.includes(kind);
  const dtype = kind === "check" ? "yes_no" : s.cDataType;
  const sections = [{ t: "common.general", fields: [
    { f: "iOpSeq", l: "mfg.st.op", type: "select", raw: true, options: stepOps(m), int: true, rerender: true, span: 2 },
    { f: "iStep", l: "mfg.f.iStep", type: "number", rerender: true },
    { f: "cKind", l: "mfg.f.cStepKind", type: "select", options: opts("mfg.o.sk.", STEP_KINDS), rerender: true },
    { f: "cTitleFR", l: "mfg.f.cTitleFR", req: true, span: 2 }, { f: "cTitleEN", l: "mfg.f.cTitleEN", span: 2 },
    { f: "cInstructionFR", l: "mfg.f.cInstructionFR", type: "textarea", span: 2 }, { f: "cInstructionEN", l: "mfg.f.cInstructionEN", type: "textarea", span: 2 },
    { f: "cAttachmentUrl", l: "mfg.f.cAttachmentUrl", span: 4, help: "mfg.f.cAttachmentUrl.help" },
  ] }];
  const own = [];
  if (kind === "material_add") own.push({ f: "iMaterialSeq", l: "mfg.f.iMaterialSeq", type: "select", raw: true, options: stepMaterials(s, m), req: true, span: 2, help: "mfg.f.iMaterialSeq.help" });
  if (valued) {
    // rows of 4: code, type, required / unit, min, target, max (number) or the list values / critical, if out
    own.push({ f: "cParam", l: "mfg.f.cParam", req: kind !== "check", span: 2, help: "mfg.f.cParam.help" });
    if (kind !== "check") own.push({ f: "cDataType", l: "mfg.f.cDataType", type: "select", options: opts("mfg.o.dt.", STEP_DATA_TYPES), rerender: true });
    own.push({ f: "lRequired", l: "mfg.f.lRequired", type: "check" });
    if (kind !== "check" && dtype === "number") {
      own.push({ f: "cUOM", l: "mfg.f.cUOM" }, { f: "dMin", l: "mfg.f.dMin", type: "number" }, { f: "dTarget", l: "mfg.f.dTarget", type: "number" }, { f: "dMax", l: "mfg.f.dMax", type: "number" });
    }
    if (kind !== "check" && dtype === "list") own.push({ f: "cOptions", l: "mfg.f.cOptions", req: true, span: 2, help: "mfg.f.cOptions.help" });
    own.push({ f: "lCritical", l: "mfg.f.lCritical", type: "check", rerender: true, help: "mfg.f.lCritical.help" });
    if (s.lCritical) own.push({ f: "cOnFail", l: "mfg.f.cOnFail", type: "select", options: opts("mfg.o.of.", STEP_ON_FAIL) });
  }
  if (kind === "timer") own.push({ f: "dDurationMin", l: "mfg.f.dDurationMin", type: "number", req: true });
  if (kind === "signature") own.push({ f: "cRequiredRole", l: "mfg.f.cRequiredRole", span: 2, help: "mfg.f.cRequiredRole.help" });
  sections.push({ t: "mfg.o.sk." + kind, help: "mfg.st.k." + kind, fields: own });
  const every = ["every_n_units", "every_n_min"].includes(s.cFrequency);
  sections.push({ t: "mfg.st.when", fields: [
    { f: "cFrequency", l: "mfg.f.cFrequency", type: "select", options: opts("mfg.o.fq.", STEP_FREQUENCIES), rerender: true },
    ...(every ? [{ f: "dFrequencyValue", l: s.cFrequency === "every_n_min" ? "mfg.f.dFrequencyValue.min" : "mfg.f.dFrequencyValue.units", type: "number", req: true }] : []),
    { f: "cCondition", l: "mfg.f.cCondition", span: 2, help: "mfg.f.cCondition.help" },
    ...(kind === "signature" ? [] : [{ f: "lSecondSignature", l: "mfg.f.lSecondSignature", type: "check" }]),
  ] });
  return sections;
};
const stepDetail = {
  sections: stepSections,
  addLabel: "mfg.st.add",
  focus: "cTitleFR",
  order: (rows) => rows.map((_, i) => i).sort((a, b) => (Number(rows[a].iOpSeq) - Number(rows[b].iOpSeq)) || (Number(rows[a].iStep) - Number(rows[b].iStep)) || a - b),
  group: (s, m) => { const o = (m.operations || []).find((x) => String(x.iOpSeq) === String(s.iOpSeq)); return `${t("mfg.st.op")} ${s.iOpSeq}${o ? " — " + (dl(o, "cDesc") || o.cOperation || "") : ""}`; },
  // "op 10 step 20: cParam" (a message of the server) -> the step and its field
  errorAt: (detail, rows, code) => {
    const x = /^op (\d+) step (\d+)(?::\s*(\w+))?/.exec(detail);
    if (!x) return null;
    const i = rows.findIndex((s) => String(Number(s.iOpSeq)) === x[1] && String(Number(s.iStep)) === x[2]);
    const byCode = { max_below_min: "dMax", target_out_of_limits: "dTarget", material_other_operation: "iMaterialSeq", duplicate: "iStep", invalid_condition: "cCondition" };
    const f = !x[3] ? byCode[code] || null : /^[cdil][A-Z]/.test(x[3]) ? x[3] : x[3] === "material" ? "iMaterialSeq" : x[3] === "op" ? "iOpSeq" : code === "invalid_condition" ? "cCondition" : "cParam";
    return { i, f };
  },
};

// How the operator will see the steps of an operation (the shop floor screen, M4), with a value test
const operatorPreview = {
  tab: "preview",
  html: (m) => `<div class="card"><div class="card-head"><h2>${esc(t("mfg.st.preview"))}</h2><span class="help muted">${esc(t("mfg.st.preview.help"))}</span></div>
    <div class="card-body"><div class="form-grid"><div class="field"><label for="stOp">${esc(t("mfg.op.one"))}</label><select id="stOp">
      ${(m.operations || []).map((o) => `<option value="${esc(o.iOpSeq)}">${esc(o.iOpSeq)} — ${esc(dl(o, "cDesc"))}</option>`).join("")}</select></div></div>
    <div id="stCards" class="step-cards"></div></div></div>`,
  bind: (m) => {
    const limits = (s) => [s.dMin && `min ${fmtNum(s.dMin)}`, s.dTarget && `${t("mfg.f.dTarget").toLowerCase()} ${fmtNum(s.dTarget)}`, s.dMax && `max ${fmtNum(s.dMax)}`].filter(Boolean).join(" · ");
    const render = () => {
      const op = $("#stOp").value;
      const steps = (m.steps || []).filter((s) => String(s.iOpSeq) === String(op));
      $("#stCards").innerHTML = steps.length ? steps.map((s, i) => {
        const mat = s.cKind === "material_add" ? (m.materials || []).find((x) => String(x.iSeq) === String(s.iMaterialSeq)) : null;
        const valued = ["parameter", "measure", "check"].includes(s.cKind);
        const input = !valued ? "" : s.cKind === "check" || s.cDataType === "yes_no"
          ? `<select data-check="${i}"><option value=""></option><option value="oui">${esc(t("common.yes"))}</option><option value="non">${esc(t("common.no"))}</option></select>`
          : s.cDataType === "list" ? `<select data-check="${i}"><option value=""></option>${s.cOptions.split(",").map((o) => `<option>${esc(o.trim())}</option>`).join("")}</select>`
            : `<input type="text" data-check="${i}" inputmode="decimal" placeholder="${esc(s.cUOM)}">`;
        return `<div class="step-card ${s.lCritical ? "critical" : ""}">
          <div class="step-head"><span class="step-no">${esc(s.iStep)}</span><span class="step-icon">${STEP_ICON[s.cKind] || ""}</span><strong>${esc(lang === "fr" ? s.cTitleFR : s.cTitleEN || s.cTitleFR)}</strong>
            ${s.lCritical ? `<span class="badge no">${esc(t("mfg.f.lCritical"))}</span>` : ""}${s.lSecondSignature ? `<span class="badge">${esc(t("mfg.f.lSecondSignature"))}</span>` : ""}</div>
          ${s.cCondition ? `<div class="muted">${esc(t("mfg.st.onlyIf", { c: s.cCondition }))}</div>` : ""}
          ${(lang === "fr" ? s.cInstructionFR : s.cInstructionEN || s.cInstructionFR) ? `<p>${esc(lang === "fr" ? s.cInstructionFR : s.cInstructionEN || s.cInstructionFR)}</p>` : ""}
          ${mat ? `<p>⚖️ ${esc(mat.cComponent)} — ${esc(fmtNum(mat.dQtyPer))} ${esc(mat.cUOM)} / ${esc(fmtNum(m.dBaseQty))} ${esc(m.cUOM)}</p>` : ""}
          ${s.cKind === "timer" ? `<p>⏱️ ${esc(minutesText(s.dDurationMin))}</p>` : ""}
          ${valued ? `<div class="step-value"><span>${esc(s.cParam)}${s.cUOM ? ` (${esc(s.cUOM)})` : ""}</span>${input}<span class="muted">${esc(limits(s))}</span><span data-result="${i}"></span></div>` : ""}
          ${s.cFrequency !== "once" ? `<div class="muted">${esc(t("mfg.o.fq." + s.cFrequency))}${s.dFrequencyValue ? " " + esc(fmtNum(s.dFrequencyValue)) : ""}</div>` : ""}
          ${s.cAttachmentUrl ? `<a href="${esc(s.cAttachmentUrl)}" target="_blank" rel="noopener">📎 ${esc(t("mfg.f.cAttachmentUrl"))}</a>` : ""}
        </div>`;
      }).join("") : `<div class="empty">${esc(t("mfg.st.none"))}</div>`;
      steps.forEach((s, i) => {
        const el = $(`[data-check="${i}"]`);
        if (!el) return;
        el.addEventListener("change", async () => {
          try {
            const r = await api(`recipes/${enc(m.cProduct)}/${enc(m.cRevision)}/steps/check`, { method: "POST", body: { iOpSeq: s.iOpSeq, iStep: s.iStep, value: el.value } });
            $(`[data-result="${i}"]`).innerHTML = r.ok ? `<span class="badge yes">✓</span>`
              : `<span class="badge no">${esc(t("mfg.st.r." + r.reason))} → ${esc(t("mfg.st.a." + r.action))}</span>`;
          } catch (e) { /* ignore */ }
        });
      });
    };
    $("#stOp").addEventListener("change", render);
    render();
  },
};

// "approved" -> "Approuvée"; "B (approved)" -> "B (Approuvée)"
const rsLabel = (v) => String(v || "").replace(/(draft|in_review|approved|obsolete)/g, (x) => t("mfg.o.rs." + x));

// The versions of the product, the history of this one, and a comparison with another version
const versionsPanel = {
  tab: "versions",
  html: (m) => `<div class="card"><div class="card-head"><h2>${esc(t("mfg.ap.versions"))}</h2></div><div id="apVersions" class="table-wrap"></div></div>
    <div class="card"><div class="card-head"><h2>${esc(t("mfg.ap.history"))}</h2></div><div class="table-wrap"><table class="grid"><thead><tr>
      <th>${esc(t("mfg.ap.when"))}</th><th>${esc(t("mfg.ap.who"))}</th><th>${esc(t("mfg.ap.action"))}</th><th>${esc(t("mfg.ap.fromTo"))}</th><th>${esc(t("mfg.ap.comment"))}</th></tr></thead><tbody>
      ${(m.history || []).map((h) => `<tr><td>${esc(fmtDateTime(h.dAt))}</td><td>${esc(h.cUser)}</td><td>${esc(t("mfg.ap.a." + h.cAction))}</td><td>${esc(rsLabel(h.cFrom))} → ${esc(rsLabel(h.cTo))}</td><td>${esc(h.cComment)}</td></tr>`).join("")
        || `<tr><td colspan="5" class="muted">${esc(t("mfg.ap.noHistory"))}</td></tr>`}</tbody></table></div></div>
    <div class="card"><div class="card-head"><h2>${esc(t("mfg.ap.compare"))}</h2><span class="help muted">${esc(t("mfg.ap.compare.help"))}</span></div>
      <div class="card-body"><div class="form-grid"><div class="field"><label for="apOther">${esc(t("mfg.ap.compareWith"))}</label><select id="apOther"></select></div></div><div id="apDiff"></div></div></div>`,
  bind: (m) => {
    const base = `#/prod/recipes/${enc(m.cProduct)}/`;
    api(`recipes?f_cProduct=${enc(m.cProduct)}&sort=cRevision&size=100`).then((r) => {
      $("#apVersions").innerHTML = `<table class="grid"><thead><tr><th>${esc(t("mfg.f.cRevision"))}</th><th>${esc(t("mfg.f.cStatus"))}</th><th>${esc(t("mfg.f.cChangeReason"))}</th><th>${esc(t("mfg.f.dEffectiveFrom"))}</th><th>${esc(t("mfg.f.dEffectiveTo"))}</th></tr></thead><tbody>
        ${r.items.map((v) => `<tr class="${v.cRevision === m.cRevision ? "selected" : ""}"><td><a href="${base}${enc(v.cRevision)}">${esc(v.cRevision)}</a></td><td>${statusBadge(v.cStatus)}${v.lDefault ? " ★" : ""}</td><td>${esc(v.cChangeReason)}</td><td>${esc(v.dEffectiveFrom)}</td><td>${esc(v.dEffectiveTo)}</td></tr>`).join("")}</tbody></table>`;
      const others = r.items.filter((v) => v.cRevision !== m.cRevision);
      $("#apOther").innerHTML = `<option value=""></option>` + others.map((v) => `<option value="${esc(v.cRevision)}">${esc(v.cRevision)} — ${esc(t("mfg.o.rs." + v.cStatus))}</option>`).join("");
    }).catch(() => {});
    $("#apOther").addEventListener("change", async () => {
      const other = $("#apOther").value;
      if (!other) { $("#apDiff").innerHTML = ""; return; }
      try {
        const d = await api(`recipes/${enc(m.cProduct)}/compare?a=${enc(other)}&b=${enc(m.cRevision)}`);
        const label = (f) => ["mfg.f." + f, "f." + f].map((k) => t(k)).find((v, i) => v !== ["mfg.f." + f, "f." + f][i]) || f;
        const fields = (fs) => fs.map((f) => `<div>${esc(label(f.cField))} : ${esc(f.cFrom || "—")} → <strong>${esc(f.cTo || "—")}</strong></div>`).join("");
        const block = (key, title) => (d[key].length ? `<h3>${esc(t(title))}</h3><table class="grid"><tbody>${d[key].map((x) =>
          `<tr><td style="width:140px">${esc(x.cKey)}</td><td style="width:120px"><span class="badge ${x.cChange === "added" ? "yes" : x.cChange === "removed" ? "no" : ""}">${esc(t("mfg.ap.c." + x.cChange))}</span></td><td>${fields(x.fields)}</td></tr>`).join("")}</tbody></table>` : "");
        const html = (d.header.length ? `<h3>${esc(t("common.general"))}</h3>${fields(d.header)}` : "")
          + block("materials", "mfg.rc.materials") + block("operations", "mfg.rc.operations") + block("steps", "mfg.st.tab") + block("outputs", "mfg.rc.outputs");
        $("#apDiff").innerHTML = `<p class="muted">${esc(t("mfg.ap.fromRev", { a: d.cFrom, b: d.cTo }))}</p>` + (html || `<div class="empty">${esc(t("mfg.ap.same"))}</div>`);
      } catch (e) { $("#apDiff").innerHTML = ""; }
    });
  },
};

// The recipe for a quantity: materials, operations (time and cost), total, attribute warnings
const explosion = {
  tab: "explode",
  html: (m) => `<div class="card"><div class="card-head"><h2>${esc(t("mfg.rc.explode"))}</h2><span class="help muted">${esc(t("mfg.rc.explode.help"))}</span></div>
    <div class="card-body"><div class="form-grid">
      <div class="field"><label for="rcQty">${esc(t("mfg.op.qty"))} (${esc(m.cUOM)})</label><input type="text" id="rcQty" inputmode="decimal" value="${esc(m.dBaseQty)}" style="text-align:right"></div>
    </div><div id="rcExplode"></div></div></div>`,
  bind: (m) => {
    const run = async () => {
      try {
        const e = await api(`recipes/${enc(m.cProduct)}/${enc(m.cRevision)}/explode?qty=${enc($("#rcQty").value || "0")}`);
        const money2 = (v) => fmtNum(v);
        const warn = e.warnings.length ? `<div class="card" style="border-color:#e3b341"><div class="card-body">${e.warnings.map((w) =>
          `<div>⚠ ${esc(t("mfg.rc.warn", { op: w.iOpSeq, res: w.cResource, attr: w.cAttribute, v: fmtNum(w.dValue), min: w.dMin || "—", max: w.dMax || "—" }))}</div>`).join("")}</div></div>` : "";
        $("#rcExplode").innerHTML = warn + `<h3>${esc(t("mfg.rc.materials"))}</h3><div class="table-wrap"><table class="grid"><thead><tr>
            <th>${esc(t("mfg.f.cComponent"))}</th><th>${esc(t("f.cDescription"))}</th><th class="num">${esc(t("mfg.f.iOpSeq"))}</th><th class="num">${esc(t("mfg.op.qty"))}</th><th class="num">${esc(t("mfg.rc.unitCost"))}</th><th class="num">${esc(t("mfg.rc.cost"))}</th></tr></thead><tbody>
          ${e.materials.map((x) => `<tr><td>${esc(x.cComponent)}</td><td>${esc(dl(x, "cDesc"))}</td><td class="num">${esc(x.iOpSeq || "")}</td><td class="num">${esc(fmtNum(x.dQty))} ${esc(x.cUOM)}${x.cStockUOM && x.cStockUOM !== x.cUOM ? `<div class="muted">= ${esc(fmtNum(x.dStockQty))} ${esc(x.cStockUOM)}</div>` : ""}</td><td class="num">${x.cStockUOM && x.cStockUOM !== x.cUOM ? `${esc(money2(x.dStockUnitCost))} <span class="muted">/ ${esc(x.cStockUOM)}</span>` : esc(money2(x.dUnitCost))}</td><td class="num">${esc(money2(x.dCost))}</td></tr>`).join("")}
          </tbody></table></div>
          <h3>${esc(t("mfg.rc.operations"))}</h3><div class="table-wrap"><table class="grid"><thead><tr>
            <th class="num">${esc(t("mfg.f.iOpSeq"))}</th><th>${esc(t("mfg.op.one"))}</th><th>${esc(t("mfg.op.where"))}</th><th class="num">${esc(t("mfg.f.dSetupMin"))}</th><th class="num">${esc(t("mfg.op.run"))}</th><th class="num">${esc(t("mfg.f.dMinWaitMin"))}</th><th class="num">${esc(t("mfg.rc.cost"))}</th></tr></thead><tbody>
          ${e.operations.map((x) => `<tr><td class="num">${esc(x.iOpSeq)}</td><td>${esc(dl(x, "cDesc"))}</td><td>${esc(x.cWhere)}</td><td class="num">${esc(minutesText(x.dSetupMin))}</td><td class="num">${esc(minutesText(x.dRunMin))}</td><td class="num">${x.dWaitMin ? esc(minutesText(x.dWaitMin)) : ""}</td><td class="num">${esc(money2(x.dCost))}</td></tr>`).join("")}
          </tbody></table></div>
          ${e.outputs.length ? `<h3>${esc(t("mfg.rc.outputs"))}</h3><div>${e.outputs.map((o) => `${esc(o.cProduct)} ${esc(fmtNum(o.dQty))} ${esc(o.cUOM)}`).join(" · ")}</div>` : ""}
          <table class="grid" style="margin-top:12px"><tbody>
            <tr><td>${esc(t("mfg.rc.batches"))}</td><td class="num">${esc(e.iBatches)}</td></tr>
            <tr><td>${esc(t("mfg.rc.time"))}</td><td class="num">${esc(minutesText(e.dTotalMin))}</td></tr>
            <tr><td>${esc(t("mfg.rc.materialCost"))}</td><td class="num">${esc(money2(e.dMaterialCost))}</td></tr>
            <tr><td>${esc(t("mfg.rc.operationCost"))}</td><td class="num">${esc(money2(e.dOperationCost))}</td></tr>
            <tr class="total-row"><td>${esc(t("mfg.rc.totalCost"))}</td><td class="num">${esc(money2(e.dTotalCost))}</td></tr>
            <tr><td>${esc(t("mfg.rc.unitCostTotal"))}</td><td class="num">${esc(fmtNum(e.dUnitCost))} / ${esc(e.cUOM)}</td></tr>
          </tbody></table>`;
      } catch (err) { $("#rcExplode").innerHTML = ""; }
    };
    $("#rcQty").addEventListener("input", (ev) => { numOnly(ev.target); run(); });
    run();
  },
};

Object.assign(RES, {
  recipes: {
    api: "recipes", route: "/prod/recipes", title: "mfg.rc.title", sub: "mfg.rc.subtitle",
    one: "mfg.rc.one", newTitle: "mfg.rc.new", id: (r) => `${r.cProduct}/${r.cRevision}`, label: (r) => `${r.cProduct} ${t("mfg.f.cRevision")} ${r.cRevision} — ${dl(r, "cDesc")}`, sort: "cProduct",
    columns: [
      { f: "cProduct", l: "mfg.f.cProduct" }, { f: "cRevision", l: "mfg.f.cRevision" }, descCol("cDesc"),
      { f: "cProcessType", l: "mfg.f.cProcessType", fmt: (v) => esc(t("mfg.o.pt." + v)) },
      { f: "dBaseQty", l: "mfg.f.dBaseQty", n: true, fmt: (v, r) => `${esc(fmtNum(v))} ${esc(r.cUOM)}` },
      { f: "iMaterials", l: "mfg.rc.materials", n: true }, { f: "iOperations", l: "mfg.rc.operations", n: true }, { f: "iSteps", l: "mfg.st.tab", n: true },
      { f: "cStatus", l: "mfg.f.cStatus", fmt: (v, r) => statusBadge(v) + (r.lDefault ? ` <span title="${esc(t("mfg.f.lDefault"))}">★</span>` : "") },
    ],
    filters: [{ f: "cStatus", l: "mfg.f.cStatus", options: opts("mfg.o.rs.", RECIPE_STATUS) }, { f: "cProcessType", l: "mfg.f.cProcessType", options: opts("mfg.o.pt.", PROCESS_TYPES) }],
    defaults: () => ({ cRevision: "A", cProcessType: "discrete", dBaseQty: "1", dYieldPct: "100", cStatus: "draft", materials: [], outputs: [], operations: [], steps: [] }),
    badge: (m, isNew) => (isNew ? "" : statusBadge(m.cStatus) + (m.lDefault ? ` <span class="badge yes">★ ${esc(t("mfg.f.lDefault"))}</span>` : "")),
    // only a draft is edited; the other versions are read, and changed through their actions
    locked: (m, isNew) => !isNew && m.cStatus !== "draft",
    actions: [
      { id: "submit", l: "mfg.ap.submit", perm: "edit", primary: true, show: (m, isNew) => !isNew && m.cStatus === "draft", confirm: "mfg.ap.submit.confirm", done: "mfg.ap.submitted",
        run: async (m, ctx) => { await api(ctx.path, { method: "PUT", body: m }); return api(ctx.path + "/submit", { method: "POST", body: {} }); } },
      { id: "approve", l: "mfg.ap.approve", perm: "approve", primary: true, show: (m, isNew) => !isNew && m.cStatus === "in_review", done: "mfg.ap.approved",
        run: (m, ctx) => api(ctx.path + "/approve", { method: "POST", body: { cComment: prompt(t("mfg.ap.comment")) || "" } }) },
      { id: "reject", l: "mfg.ap.reject", perm: "approve", show: (m, isNew) => !isNew && m.cStatus === "in_review", done: "mfg.ap.rejected",
        run: (m, ctx) => { const c = prompt(t("mfg.ap.rejectWhy")); if (!c) return null; return api(ctx.path + "/reject", { method: "POST", body: { cComment: c } }); } },
      { id: "default", l: "mfg.ap.default", perm: "approve", show: (m, isNew) => !isNew && m.cStatus === "approved" && !m.lDefault,
        run: (m, ctx) => api(ctx.path + "/default", { method: "POST", body: {} }) },
      { id: "obsolete", l: "mfg.ap.obsolete", perm: "approve", show: (m, isNew) => !isNew && m.cStatus === "approved", confirm: "mfg.ap.obsolete.confirm",
        run: (m, ctx) => api(ctx.path + "/obsolete", { method: "POST", body: {} }) },
      { id: "copy", l: "mfg.ap.copy", perm: "create", show: (m, isNew) => !isNew,
        run: async (m, ctx) => {
          const why = prompt(t("mfg.ap.copyWhy"));
          if (why === null) return null;
          const r = await api(ctx.path + "/copy", { method: "POST", body: { cComment: why } });
          location.hash = `#/prod/recipes/${enc(r.cProduct)}/${enc(r.cRevision)}`;
          return null;
        } },
    ],
    formTabs: [["gen", "common.general"], ["ops", "mfg.rc.operations"], ["mat", "mfg.rc.materials"], ["steps", "mfg.st.tab"], ["out", "mfg.rc.outputs"],
      ["explode", "mfg.rc.explode"], ["preview", "mfg.st.preview"], ["versions", "mfg.ap.tab"]],
    sections: [
      { tab: "gen", t: "common.general", fields: [
        { f: "cProduct", l: "mfg.f.cProduct", req: true, key: true, lookup: "products" },
        { f: "cRevision", l: "mfg.f.cRevision", req: true, key: true, help: "mfg.f.cRevision.help" },
        { f: "cProcessType", l: "mfg.f.cProcessType", type: "select", options: opts("mfg.o.pt.", PROCESS_TYPES) },
        { f: "cDescFR", l: "f.cDescFR", span: 2, help: "mfg.rc.desc.help" }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
        { f: "cChangeReason", l: "mfg.f.cChangeReason", span: 2 },
        { f: "dEffectiveFrom", l: "mfg.f.dEffectiveFrom", type: "date" }, { f: "dEffectiveTo", l: "mfg.f.dEffectiveTo", type: "date" },
      ] },
      { tab: "gen", t: "mfg.rc.quantities", help: "mfg.rc.quantities.help", fields: [
        { f: "dBaseQty", l: "mfg.f.dBaseQty", type: "number", req: true }, { f: "cUOM", l: "mfg.f.cUOM", lookup: "uom" },
        { f: "dMinBatch", l: "mfg.f.dMinBatch", type: "number" }, { f: "dMaxBatch", l: "mfg.f.dMaxBatch", type: "number", help: "mfg.f.dMaxBatch.help" },
        { f: "dYieldPct", l: "mfg.f.dYieldPct", type: "number", help: "mfg.f.dYieldPct.help" },
      ] },
      { tab: "gen", t: "mfg.f.cNotes", fields: [{ f: "cNotes", l: "mfg.f.cNotes", type: "textarea", span: 4 }] },
    ],
    grids: [
      { key: "operations", tab: "ops", title: "mfg.rc.operations", help: "mfg.rc.operations.help",
        cols: [
          { f: "iOpSeq", l: "mfg.f.iOpSeq", w: "w-xs", n: true }, { f: "cOperation", l: "mfg.op.one", w: "w-md", lookup: "operations" },
          { f: "cDescFR", l: "f.cDescFR", w: "w-md" },
          { f: "cWorkCenter", l: "mfg.f.cWorkCenter", w: "w-md", lookup: "work_centers" }, { f: "cResource", l: "mfg.res.one", w: "w-md", lookup: "resources" },
          { f: "cCapability", l: "mfg.res.cap", w: "w-md", lookup: "capabilities" },
          { f: "dSetupMin", l: "mfg.f.dSetupMin", w: "w-sm", n: true },
          { f: "cRunFormat", l: "mfg.f.cRunFormat", w: "w-md", type: "select", options: opts("mfg.o.run.", RUN_FORMATS) },
          { f: "dRunValue", l: "mfg.f.dRunValue", w: "w-sm", n: true }, { f: "iCrew", l: "mfg.f.iCrew", w: "w-xs", n: true },
          { f: "dMinWaitMin", l: "mfg.f.dMinWaitMin", w: "w-sm", n: true }, { f: "dMaxWaitMin", l: "mfg.f.dMaxWaitMin", w: "w-sm", n: true },
          { f: "cPredecessors", l: "mfg.f.cPredecessors", w: "w-sm" },
        ],
        newLine: (m) => ({ iOpSeq: ((m.operations || []).reduce((a, o) => Math.max(a, Number(o.iOpSeq) || 0), 0) + 10), cOperation: "", cRunFormat: "min_per_unit", iCrew: 0, lReportingPoint: true }) },
      { key: "materials", tab: "mat", title: "mfg.rc.materials", help: "mfg.rc.materials.help",
        cols: [
          { f: "iSeq", l: "mfg.f.iSeq", w: "w-xs", n: true }, { f: "cComponent", l: "mfg.f.cComponent", w: "w-lg", lookup: "products" },
          { f: "dQtyPer", l: "mfg.f.dQtyPer", w: "w-sm", n: true }, { f: "cUOM", l: "mfg.f.cUOM", w: "w-sm", lookup: "uom" },
          { f: "dScrapPct", l: "mfg.f.dScrapPct", w: "w-xs", n: true }, { f: "lFixedQty", l: "mfg.f.lFixedQty", w: "w-xs", type: "check" },
          { f: "iOpSeq", l: "mfg.f.iOpSeq", w: "w-xs", n: true },
          { f: "cIssueMethod", l: "mfg.f.cIssueMethod", w: "w-md", type: "select", options: opts("mfg.o.issue.", ISSUE_METHODS) },
        ],
        newLine: (m) => ({ iSeq: ((m.materials || []).length + 1) * 10, cComponent: "", dQtyPer: "", cUOM: "", dScrapPct: "", lFixedQty: false, iOpSeq: (m.operations || [])[0] ? m.operations[0].iOpSeq : 0, cIssueMethod: "manual" }) },
      { key: "steps", tab: "steps", title: "mfg.st.tab", help: "mfg.st.help",
        cols: [
          { f: "iStep", l: "mfg.f.iStep", n: true },
          { f: "cKind", l: "mfg.f.cStepKind", type: "select", options: opts("mfg.o.sk.", STEP_KINDS), fmt: (v) => STEP_ICON[v] || "" },
          { f: "cTitleFR", l: "mfg.f.cTitleFR", fmt: (v, s) => (lang === "fr" ? s.cTitleFR : s.cTitleEN || s.cTitleFR) || t("mfg.o.sk." + s.cKind) },
        ],
        detail: stepDetail,
        newLine: (m, after) => {
          const op = after ? after.iOpSeq : ((m.operations || [])[0] || {}).iOpSeq || 10;
          const next = (m.steps || []).filter((x) => String(x.iOpSeq) === String(op)).reduce((a, x) => Math.max(a, Number(x.iStep) || 0), 0) + 10;
          return { iOpSeq: op, iStep: next, cKind: "instruction", cTitleFR: "", cDataType: "number", cOnFail: "block", cFrequency: "once", lRequired: false, lCritical: false, lSecondSignature: false };
        } },
      { key: "outputs", tab: "out", title: "mfg.rc.outputs", help: "mfg.rc.outputs.help",
        cols: [
          { f: "cProduct", l: "mfg.f.cProduct", w: "w-lg", lookup: "products" },
          { f: "cKind", l: "mfg.f.cKind", w: "w-md", type: "select", options: opts("mfg.o.out.", OUTPUT_KINDS) },
          { f: "dQtyPer", l: "mfg.f.dQtyPer", w: "w-sm", n: true }, { f: "cUOM", l: "mfg.f.cUOM", w: "w-sm", lookup: "uom" }, { f: "dCostPct", l: "mfg.f.dCostPct", w: "w-sm", n: true },
        ],
        newLine: () => ({ cProduct: "", cKind: "byproduct", dQtyPer: "", cUOM: "", dCostPct: "" }) },
    ],
    panel: explosion,
    panels: [operatorPreview, versionsPanel],
  },
});
