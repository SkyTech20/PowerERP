/* PowerERP: Production: list / form definitions. P1: the reference lists of the shop floor; P2: calendars. */
import { $, api, enc, esc, lang, t, yesNo } from "../core.js";
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
        newLine: () => ({ dStart: today(), cStartTime: "07:00", dEnd: today(), cEndTime: "11:00", cReason: "PM", cNotes: "" }) },
    ],
    panel: { tab: "time", ...weekPreview((m) => `resources/${enc(m.cCode)}/availability`, (r) => `
      <tr><td colspan="2">${esc(t("mfg.res.plannedStops"))}</td><td class="num">− ${esc(hours(r.iDowntimeMinutes))}</td></tr>
      <tr><td colspan="2">${esc(t("mfg.res.capacityTotal"))}</td><td class="num">${esc(hours(r.iCapacityMinutes))}</td></tr>`) },
  },
});

