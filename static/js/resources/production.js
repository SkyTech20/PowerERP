/* PowerERP: Production: list / form definitions. P1: the reference lists of the shop floor; P2: calendars. */
import { $, api, enc, esc, lang, t, yesNo } from "../core.js";
import { RES } from "../registry.js";
import { descCol, dl, optBadge, opts, today } from "./inventory.js";

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
    panel: {
      html: () => `<div class="card"><div class="card-head"><h2>${esc(t("mfg.cal.preview"))}</h2><span class="help muted">${esc(t("mfg.cal.preview.help"))}</span></div>
        <div class="card-body"><div class="form-grid"><div class="field"><label for="calWeek">${esc(t("mfg.cal.weekOf"))}</label><input type="date" id="calWeek" value="${monday(today())}"></div></div>
        <div id="calPreview"></div></div></div>`,
      bind: (m) => {
        const run = async () => {
          const from = monday($("#calWeek").value || today());
          const to = new Date(from + "T12:00:00"); to.setDate(to.getDate() + 6);
          try {
            const r = await api(`calendars/${enc(m.cCode)}/availability?from=${from}&to=${to.toISOString().slice(0, 10)}`);
            $("#calPreview").innerHTML = `<table class="grid"><thead><tr><th>${esc(t("mfg.cal.day"))}</th><th>${esc(t("mfg.cal.shifts"))}</th><th class="num">${esc(t("mfg.cal.available"))}</th></tr></thead><tbody>
              ${r.days.map((d) => `<tr><td>${esc(dayName(d.dDate))}</td><td>${d.shifts.map((s) => `${s.cShift === "*" ? "" : esc(s.cShift) + " "}${esc(s.cStart)}–${esc(s.cEnd)}`).join(" · ")}
                ${d.cException ? ` <span class="badge ${d.lClosed ? "no" : ""}">${esc(lang === "fr" ? d.cException : d.cExceptionEN)}</span>` : ""}</td><td class="num">${esc(hours(d.iMinutes))}</td></tr>`).join("")}
              <tr class="total-row"><td colspan="2">${esc(t("mfg.cal.total"))}</td><td class="num">${esc(hours(r.iMinutes))}</td></tr></tbody></table>`;
          } catch (e) { $("#calPreview").innerHTML = ""; }
        };
        $("#calWeek").addEventListener("change", run);
        run();
      },
    },
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

