/* PowerERP: Products, taxes and inventory: list / form definitions. */
import { $, CURRENCIES, api, enc, esc, fmtDateTime, lang, money, num, numOnly, statusBadge, t, yesNo } from "../core.js";
import { RES } from "../registry.js";
import { route } from "../router.js";
import { setPrefill } from "../state.js";

// ------------------------------------------------------------------ Products, taxes and inventory
export const today = () => new Date().toISOString().slice(0, 10);
export const opts = (prefix, values) => values.map((v) => [v, prefix + v]);
// FR / EN text of a record (cDescFR / cDescEN, cNameFR / cNameEN): the UI language, else French
export const dl = (r, base) => (lang === "fr" ? r[base + "FR"] : r[base + "EN"] || r[base + "FR"]) || "";
export const qtyFmt = (v) => (v === "" || v == null ? "" : new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { maximumFractionDigits: 4 }).format(num(v)));
export const optBadge = (prefix, cls) => (v) => (v ? `<span class="badge ${cls ? cls(v) : ""}">${esc(t(prefix + v))}</span>` : "");
export const descCol = (base) => ({ f: base + "FR", l: "f.cDescription", wrap: true, fmt: (v, r) => esc(dl(r, base)) });
export const productLink = (r) => "/inv/items/" + enc(r.cProduct);
export const whFilter = { f: "cWarehouse", l: "f.inv.cWarehouse", lookup: "warehouses" };
export const isPhysical = (m) => m.cNature !== "service" && m.cStockType === "physical";
export const isProduct = (m) => m.cNature !== "service";
export function newWith(key, values) { setPrefill({ key, values }); location.hash = "#" + RES[key].route + "/new"; }

export const PRODUCT_STOCK_TYPES = ["physical", "nonphysical"];
export const PRODUCT_NATURES = ["product", "service"];
export const PRODUCT_CLASSES = ["", "raw", "kit", "finished", "consumable", "asset"];
export const MOVE_TYPES = ["IN", "OUT", "TRF", "ADJ", "CNT", "RSV"];
export const DOC_TYPES = ["MAN", "PO", "REC", "INV", "SO", "CNT", "PROD"];
export const LOCATION_TYPES = ["picking", "reserve", "receiving", "shipping", "quarantine", "staging"];
export const MV_IN = (m) => m.cType === "IN" || ((m.cType === "ADJ" || m.cType === "CNT") && num(m.dQty) > 0);

Object.assign(RES, {
  taxcodes: {
    api: "tax-codes", route: "/admin/taxes/codes", menu: "/admin/taxes", tabset: "tax", title: "tax.title", sub: "tax.subtitle",
    one: "tax.code.one", newTitle: "tax.code.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [
      { f: "cCode", l: "f.cCode" }, descCol("cDesc"), { f: "cKind", l: "f.tax.cKind", fmt: optBadge("o.kind.") },
      { f: "cJurisdiction", l: "f.tax.cJurisdiction" },
      { f: "dCurrentRate", l: "f.tax.dCurrentRate", num: true, fmt: (v) => (v === "" ? "—" : esc(qtyFmt(v) + " %")) },
      { f: "cRegistrationNo", l: "f.tax.cRegistrationNo" }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    defaults: () => ({ cKind: "gst", dRecoverablePct: "100", lActive: true, lines: [{ dStartDate: today(), dEndDate: "", dRate: "" }] }),
    sections: [
      { t: "common.general", fields: [
        { f: "cCode", l: "f.cCode", req: true, key: true }, { f: "cKind", l: "f.tax.cKind", type: "select", options: opts("o.kind.", ["gst", "pst", "hst", "other"]) },
        { f: "cJurisdiction", l: "f.tax.cJurisdiction", suggestions: ["CA", "QC", "ON", "NS", "NB", "NL", "PE", "BC", "MB", "SK", "AB"] },
        { f: "lActive", l: "opt.active", type: "check" },
        { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
        { f: "cRegistrationNo", l: "f.tax.cRegistrationNo", span: 2, help: "f.tax.cRegistrationNo.help" },
      ] },
      { t: "tax.accounting", fields: [
        { f: "cGLCollected", l: "f.tax.cGLCollected", lookup: "gl" }, { f: "cGLRecoverable", l: "f.tax.cGLRecoverable", lookup: "gl" },
        { f: "dRecoverablePct", l: "f.tax.dRecoverablePct", type: "number", help: "f.tax.dRecoverablePct.help" },
      ] },
    ],
    lines: {
      title: "tax.rates", help: "tax.rates.help",
      cols: [{ f: "dStartDate", l: "f.tax.dStartDate", w: "w-md", type: "date" }, { f: "dEndDate", l: "f.tax.dEndDate", w: "w-md", type: "date" },
        { f: "dRate", l: "f.tax.dRate", w: "w-sm", n: true }],
      newLine: () => ({ dStartDate: today(), dEndDate: "", dRate: "" }),
    },
  },
  taxgroups: {
    api: "tax-groups", route: "/admin/taxes/groups", tabset: "tax", title: "tax.title", sub: "tax.subtitle",
    one: "tax.group.one", newTitle: "tax.group.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [
      { f: "cCode", l: "f.cCode" }, descCol("cDesc"), { f: "cProvince", l: "f.cProvince" },
      { f: "cTreatment", l: "f.tax.cTreatment", fmt: optBadge("o.treat.") }, { f: "cTaxList", l: "tax.groupLines" },
      { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    defaults: () => ({ cTreatment: "taxable", cProvince: "QC", lActive: true, lines: [{ iSeq: 1, cTaxCode: "", lCompound: false }] }),
    sections: [{ t: "common.general", help: "tax.group.help", fields: [
      { f: "cCode", l: "f.cCode", req: true, key: true },
      { f: "cTreatment", l: "f.tax.cTreatment", type: "select", options: opts("o.treat.", ["taxable", "zero", "exempt"]), rerender: true },
      { f: "cProvince", l: "f.cProvince" }, { f: "lActive", l: "opt.active", type: "check" },
      { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
    ] }],
    lines: {
      title: "tax.groupLines", help: "tax.groupLines.help", show: (m) => m.cTreatment === "taxable",
      cols: [{ f: "iSeq", l: "f.tax.iSeq", w: "w-xs", n: true }, { f: "cTaxCode", l: "f.tax.cTaxCode", w: "w-md", lookup: "taxcodes" },
        { f: "lCompound", l: "f.tax.lCompound", w: "w-sm", type: "check" }],
      newLine: (m) => ({ iSeq: (m.lines || []).length + 1, cTaxCode: "", lCompound: false }),
    },
    panel: {
      html: () => `<div class="card"><div class="card-head"><h2>${esc(t("tax.sim"))}</h2><span class="help muted">${esc(t("tax.sim.help"))}</span></div>
        <div class="card-body"><div class="form-grid">
          <div class="field"><label for="simAmount">${esc(t("tax.sim.amount"))}</label><input type="text" id="simAmount" inputmode="decimal" value="100.00" style="text-align:right"></div>
          <div class="field"><label for="simDate">${esc(t("tax.sim.date"))}</label><input type="date" id="simDate" value="${today()}"></div>
        </div><div id="simResult" class="sim-result"></div></div></div>`,
      bind: (m) => {
        const run = async () => {
          try {
            const r = await api(`tax-groups/${enc(m.cCode)}/calc?amount=${enc(num($("#simAmount").value))}&date=${enc($("#simDate").value)}`);
            $("#simResult").innerHTML = `<table class="grid"><thead><tr><th>${esc(t("f.tax.cTaxCode"))}</th><th class="num">${esc(t("f.tax.dRate"))}</th><th class="num">${esc(t("tax.sim.base"))}</th><th class="num">${esc(t("tax.sim.tax"))}</th><th>${esc(t("f.tax.cGLCollected"))}</th><th>${esc(t("f.tax.cGLRecoverable"))}</th></tr></thead><tbody>
              ${r.taxes.map((x) => `<tr><td>${esc(x.cTaxCode)}</td><td class="num">${esc(qtyFmt(x.dRate))} %</td><td class="num">${esc(money(x.dBase))}</td><td class="num">${esc(money(x.dTax))}</td><td>${esc(x.cGLCollected)}</td><td>${esc(x.cGLRecoverable)}</td></tr>`).join("")
                || `<tr><td colspan="6" class="muted">${esc(t("o.treat." + r.cTreatment))}</td></tr>`}
              <tr class="total-row"><td colspan="3">${esc(t("tax.sim.total"))}</td><td class="num">${esc(money(r.dTotalTax))}</td><td colspan="2" class="num">${esc(money(r.dTotal))}</td></tr></tbody></table>`;
          } catch (e) { $("#simResult").innerHTML = ""; }
        };
        $("#simAmount").addEventListener("input", (e) => { numOnly(e.target); run(); });
        $("#simDate").addEventListener("change", run);
        run();
      },
    },
  },
  categories: {
    api: "categories", route: "/inv/categories", tabset: "setup", title: "setup.title", sub: "setup.subtitle",
    one: "cat.one", newTitle: "cat.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [{ f: "cCode", l: "f.cCode" }, descCol("cDesc"), { f: "cParent", l: "f.cat.cParent" }, { f: "lActive", l: "opt.active", fmt: yesNo }],
    defaults: { lActive: true },
    sections: [{ t: "common.general", fields: [
      { f: "cCode", l: "f.cCode", req: true, key: true }, { f: "cParent", l: "f.cat.cParent", lookup: "categories", help: "f.cat.cParent.help" },
      { f: "lActive", l: "opt.active", type: "check" },
      { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
    ] }],
  },
  uom: {
    api: "uom", route: "/inv/uom", tabset: "setup", title: "setup.title", sub: "setup.subtitle",
    one: "uom.one", newTitle: "uom.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [{ f: "cCode", l: "f.cCode" }, descCol("cDesc"), { f: "cType", l: "f.uom.cType", fmt: (v) => esc(t("o.uom." + v)) }, { f: "lActive", l: "opt.active", fmt: yesNo }],
    defaults: { cType: "count", lActive: true },
    sections: [{ t: "common.general", fields: [
      { f: "cCode", l: "f.cCode", req: true, key: true },
      { f: "cType", l: "f.uom.cType", type: "select", options: opts("o.uom.", ["count", "weight", "length", "area", "volume", "time"]) },
      { f: "lActive", l: "opt.active", type: "check" },
      { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
    ] }],
  },
  uomconv: {
    api: "uom-conversions", route: "/inv/uom-conversions", menu: "/inv/categories", tabset: "setup", title: "setup.title", sub: "setup.subtitle",
    one: "conv.one", newTitle: "conv.new", id: (r) => `${r.cFromUOM}/${r.cToUOM}`, label: (r) => `1 ${r.cFromUOM} = ${qtyFmt(r.dFactor)} ${r.cToUOM}`, sort: "cFromUOM",
    columns: [
      { f: "cFromUOM", l: "f.conv.cFromUOM", fmt: (v) => esc("1 " + v) }, { f: "dFactor", l: "f.conv.dFactor", num: true, fmt: (v) => esc(qtyFmt(v)) },
      { f: "cToUOM", l: "f.conv.cToUOM" }, { f: "cNotes", l: "f.conv.cNotes", wrap: true }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    listActions: [{ id: "standard", l: "conv.standard", run: async () => {
      const r = await api("uom-conversions/standard", { method: "POST" });
      return t("conv.standard.done", { u: r.iUnits, c: r.iConversions });
    } }],
    defaults: { lActive: true },
    sections: [{ t: "common.general", help: "conv.help", fields: [
      { f: "cFromUOM", l: "f.conv.cFromUOM", req: true, key: true, lookup: "uom" },
      { f: "dFactor", l: "f.conv.dFactor", type: "number", req: true, help: "f.conv.dFactor.help" },
      { f: "cToUOM", l: "f.conv.cToUOM", req: true, key: true, lookup: "uom" },
      { f: "lActive", l: "opt.active", type: "check" },
      { f: "cNotes", l: "f.conv.cNotes", span: 4 },
    ] }],
  },
  products: {
    api: "products", route: "/inv/items", title: "prod.title", sub: "prod.subtitle", one: "prod.one", newTitle: "prod.new",
    id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    formTabs: [["gen", "prod.tab.general"], ["units", "prod.units"], ["prices", "prod.costs"], ["tax", "prod.tab.taxes"],
      ["inv", "prod.inventory"], ["log", "prod.tab.logistics"], ["sup", "prod.suppliers"], ["stock", "prod.stock"]],
    filters: [
      { f: "cStatus", l: "f.prod.cStatus", options: opts("o.status.", ["active", "inactive", "discontinued"]) },
      { f: "cNature", l: "f.prod.cNature", options: opts("o.pnature.", PRODUCT_NATURES) },
      { f: "cStockType", l: "f.prod.cStockType", options: opts("o.pstock.", PRODUCT_STOCK_TYPES) },
      { f: "cClass", l: "f.prod.cClass", options: opts("o.pclass.", PRODUCT_CLASSES.slice(1)) },
      { f: "cCategory", l: "f.prod.cCategory", lookup: "categories" },
    ],
    columns: [
      { f: "cCode", l: "f.prod.cCode" }, descCol("cDesc"), { f: "cCategory", l: "f.prod.cCategory" },
      { f: "cNature", l: "f.prod.cNature", fmt: (v) => esc(t("o.pnature." + v)) },
      { f: "cClass", l: "f.prod.cClass", fmt: (v) => (v ? esc(t("o.pclass." + v)) : "") }, { f: "cStockUOM", l: "f.prod.unit" },
      { f: "dQtyOnHand", l: "f.inv.dQtyOnHand", num: true, fmt: (v, r) => (r.lStocked ? esc(qtyFmt(v)) : "—") },
      { f: "dQtyAvailable", l: "f.inv.dQtyAvailable", num: true, fmt: (v, r) => (r.lStocked ? esc(qtyFmt(v)) : "—") },
      { f: "dPrice1", l: "f.prod.dPrice1", num: true, fmt: (v, r) => (v ? esc(money(v, r.cCurrency)) : "") },
      { f: "cStatus", l: "f.prod.cStatus", fmt: optBadge("o.status.", (v) => (v === "active" ? "yes" : "no")) },
    ],
    defaults: () => ({ cStatus: "active", cStockType: "physical", cNature: "product", cClass: "", cCostMethod: "avg", cCurrency: "CAD", cStockUOM: "UN", cPurchaseUOM: "UN",
      cSalesUOM: "UN", cSalesTaxGroup: "QC", cPurchaseTaxGroup: "QC", lStocked: true,
      lSellable: true, lPurchasable: true, lPORequired: true, cWeightUOM: "kg", cDimUOM: "cm", cCountryOrigin: "CA", cABCClass: "", lines: [], conversions: [] }),
    sections: [
      { t: "prod.ident", fields: [
        { f: "cCode", l: "f.prod.cCode", req: true, key: true },
        { f: "cStatus", l: "f.prod.cStatus", type: "select", options: opts("o.status.", ["active", "inactive", "discontinued"]) },
        { f: "cCategory", l: "f.prod.cCategory", lookup: "categories", span: 2 },
        { f: "cNature", l: "f.prod.cNature", type: "select", options: opts("o.pnature.", PRODUCT_NATURES), rerender: true },
        { f: "cStockType", l: "f.prod.cStockType", type: "select", options: opts("o.pstock.", PRODUCT_STOCK_TYPES), rerender: true, show: isProduct, help: "f.prod.cStockType.help" },
        { f: "cClass", l: "f.prod.cClass", type: "select", options: opts("o.pclass.", PRODUCT_CLASSES), show: isProduct, help: "f.prod.cClass.help" },
        { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
        { f: "cLongDescFR", l: "f.prod.cLongDescFR", type: "textarea", span: 2 }, { f: "cLongDescEN", l: "f.prod.cLongDescEN", type: "textarea", span: 2 },
        { f: "cBrand", l: "f.prod.cBrand" }, { f: "cModel", l: "f.prod.cModel" },
        { f: "cManufacturer", l: "f.prod.cManufacturer" }, { f: "cMfrPartNo", l: "f.prod.cMfrPartNo" },
        { f: "cUPC", l: "f.prod.cUPC", help: "f.prod.cUPC.help" }, { f: "cImageUrl", l: "f.prod.cImageUrl" },
        { f: "cSpecUrl", l: "f.prod.cSpecUrl" }, { f: "cSdsUrl", l: "f.prod.cSdsUrl", help: "f.prod.cSdsUrl.help" },
      ] },
      { tab: "units", t: "prod.units", fields: [
        { f: "cStockUOM", l: "f.prod.cStockUOM", req: true, lookup: "uom" },
        { f: "cPurchaseUOM", l: "f.prod.cPurchaseUOM", lookup: "uom", help: "f.prod.unitConv.help" },
        { f: "cSalesUOM", l: "f.prod.cSalesUOM", lookup: "uom" },
        { f: "dWeight", l: "f.prod.dWeight", type: "number" },
        { f: "cWeightUOM", l: "f.prod.cWeightUOM", type: "select", options: [["kg", "kg"], ["lb", "lb"]], raw: true },
        { f: "dVolume", l: "f.prod.dVolume", type: "number" },
        { f: "dLength", l: "f.prod.dLength", type: "number" }, { f: "dWidth", l: "f.prod.dWidth", type: "number" },
        { f: "dHeight", l: "f.prod.dHeight", type: "number" },
        { f: "cDimUOM", l: "f.prod.cDimUOM", type: "select", options: [["cm", "cm"], ["in", "po / in"]], raw: true },
      ] },
      { tab: "prices", t: "prod.costs", fields: [
        { f: "cCostMethod", l: "f.prod.cCostMethod", type: "select", options: opts("o.cost.", ["avg", "std"]) },
        { f: "dStdCost", l: "f.prod.dStdCost", type: "number" },
        { f: "dAvgCost", l: "f.prod.dAvgCost", readonly: true, help: "f.prod.dAvgCost.help" }, { f: "dLastCost", l: "f.prod.dLastCost", readonly: true },
        { f: "cCurrency", l: "f.cDevise", type: "select", options: CURRENCIES.map((c) => [c, c]), raw: true },
        { f: "dPrice1", l: "f.prod.dPrice1", type: "number" }, { f: "dPrice2", l: "f.prod.dPrice2", type: "number" },
        { f: "dPrice3", l: "f.prod.dPrice3", type: "number" }, { f: "dPrice4", l: "f.prod.dPrice4", type: "number" },
        { f: "dPrice5", l: "f.prod.dPrice5", type: "number" }, { f: "dMinPrice", l: "f.prod.dMinPrice", type: "number" },
        { f: "dMarginPct", l: "f.prod.dMarginPct", readonly: true, show: (m, n) => !n },
      ] },
      { tab: "tax", t: "prod.taxes", help: "prod.taxes.help", fields: [
        { f: "cSalesTaxGroup", l: "f.prod.cSalesTaxGroup", lookup: "taxgroups" }, { f: "cPurchaseTaxGroup", l: "f.prod.cPurchaseTaxGroup", lookup: "taxgroups" },
        { f: "dEcoFee", l: "f.prod.dEcoFee", type: "number", help: "f.prod.dEcoFee.help" }, { f: "cEcoFeeCode", l: "f.prod.cEcoFeeCode" },
      ] },
      { tab: "tax", t: "prod.accounting", fields: [
        { f: "cGLSales", l: "f.prod.cGLSales", lookup: "gl" }, { f: "cGLPurchase", l: "f.prod.cGLPurchase", lookup: "gl" },
        { f: "cGLInventory", l: "f.prod.cGLInventory", lookup: "gl" }, { f: "cGLCOGS", l: "f.prod.cGLCOGS", lookup: "gl" },
        { f: "cCostCenter", l: "f.prod.cCostCenter", lookup: "cc" }, { f: "cProject", l: "f.prod.cProject" },
      ] },
      { tab: "inv", t: "prod.inventory", fields: [
        { f: "lStocked", l: "f.prod.lStocked", type: "check", show: isPhysical, help: "f.prod.lStocked.help" },
        { f: "cDefaultWarehouse", l: "f.prod.cDefaultWarehouse", lookup: "warehouses", show: isPhysical },
        { f: "cABCClass", l: "f.prod.cABCClass", type: "select", options: [["", "—"], ["A", "A"], ["B", "B"], ["C", "C"]], raw: true, show: isPhysical },
        { f: "iShelfLifeDays", l: "f.prod.iShelfLifeDays", type: "number", show: isPhysical },
        { f: "lLotControl", l: "f.prod.lLotControl", type: "check", show: isPhysical },
        { f: "lSerialControl", l: "f.prod.lSerialControl", type: "check", show: isPhysical },
        { f: "lExpiryControl", l: "f.prod.lExpiryControl", type: "check", show: isPhysical },
        { f: "cPickPolicy", l: "f.prod.cPickPolicy", type: "select", show: isPhysical, help: "f.prod.cPickPolicy.help",
          options: [["", "o.pick.auto"], ["FEFO", "o.pick.FEFO"], ["FIFO", "o.pick.FIFO"], ["LIFO", "o.pick.LIFO"]] },
      ] },
      { tab: "log", t: "prod.logistics", fields: [
        { f: "lSellable", l: "f.prod.lSellable", type: "check" }, { f: "lPurchasable", l: "f.prod.lPurchasable", type: "check" },
        { f: "lPORequired", l: "f.prod.lPORequired", type: "check" }, { f: "lHazardous", l: "f.prod.lHazardous", type: "check" },
        { f: "iWarrantyMonths", l: "f.prod.iWarrantyMonths", type: "number" }, { f: "cCountryOrigin", l: "f.prod.cCountryOrigin" },
        { f: "cHSCode", l: "f.prod.cHSCode", help: "f.prod.cHSCode.help" }, { f: "cFreightClass", l: "f.prod.cFreightClass" },
        { f: "cNotes", l: "f.prod.cNotes", type: "textarea", span: 4 },
      ] },
    ],
    grids: [
      { key: "conversions", tab: "units", title: "prod.conversions", help: "prod.conversions.help",
        cols: [{ f: "cUOM", l: "f.prod.convUOM", w: "w-md", lookup: "uom" }, { f: "dFactor", l: "f.prod.convFactor", w: "w-sm", n: true },
          { f: "cNotes", l: "f.conv.cNotes", w: "w-lg" }],
        newLine: () => ({ cUOM: "", dFactor: "", cNotes: "" }) },
    ],
    // A purchase / sales unit with no conversion to the stock unit: the user is asked to add one (saving refuses it)
    warnings: (m) => (m.cStockUOM && (m.cPurchaseUOM || m.cSalesUOM)
      ? api("/products/unit-check", { method: "POST", body: { cStockUOM: m.cStockUOM, cPurchaseUOM: m.cPurchaseUOM,
        cSalesUOM: m.cSalesUOM, conversions: m.conversions || [] } })
        .then((r) => Object.fromEntries((r.missing || []).map((f) => [f, t("prod.noConv", { from: m[f], to: m.cStockUOM })])))
      : {}),
    lines: {
      tab: "sup", title: "prod.suppliers", help: "prod.suppliers.help",
      cols: [
        { f: "cSupplierCode", l: "f.cSupplierCode", w: "w-md", lookup: "suppliers" }, { f: "cSupplierItem", l: "f.prod.cSupplierItem", w: "w-md" },
        { f: "dPurchasePrice", l: "f.prod.dPurchasePrice", w: "w-sm", n: true }, { f: "cCurrency", l: "f.cDevise", w: "w-xs" },
        { f: "iLeadTimeDays", l: "f.prod.iLeadTimeDays", w: "w-xs", n: true }, { f: "dMinOrderQty", l: "f.prod.dMinOrderQty", w: "w-xs", n: true },
        { f: "lPreferred", l: "f.prod.lPreferred", w: "w-xs", type: "check" },
      ],
      newLine: (m) => ({ cCurrency: m.cCurrency || "CAD", lPreferred: !(m.lines || []).length }),
    },
    panel: {
      tab: "stock",
      html: (m) => {
        if (!m.lStocked) return "";
        const rows = (m.stock || []).map((s) => `<tr><td>${esc(s.cWarehouse)}</td><td>${esc(s.cWarehouseName)}</td><td class="num">${esc(qtyFmt(s.dQtyOnHand))}</td><td class="num">${esc(qtyFmt(s.dQtyReserved))}</td><td class="num">${esc(qtyFmt(s.dQtyAvailable))}</td><td class="num">${esc(qtyFmt(s.dReorderPoint))}</td><td class="num">${esc(money(s.dValue))}</td></tr>`).join("");
        return `<div class="card"><div class="card-head"><h2>${esc(t("prod.stock"))}</h2>
            <span class="muted">${esc(t("prod.stockSummary", { oh: qtyFmt(m.dQtyOnHand), av: qtyFmt(m.dQtyAvailable), oo: qtyFmt(m.dQtyOnOrder), u: m.cStockUOM }))}</span>
            <span style="margin-left:auto;display:flex;gap:8px"><button class="btn small" id="prodMove">＋ ${esc(t("inv.newMovement"))}</button><a class="btn small" href="#/inv/stock">${esc(t("menu.inv.stock"))} →</a></span></div>
          ${rows ? `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("f.inv.cWarehouse"))}</th><th></th><th class="num">${esc(t("f.inv.dQtyOnHand"))}</th><th class="num">${esc(t("f.inv.dQtyReserved"))}</th><th class="num">${esc(t("f.inv.dQtyAvailable"))}</th><th class="num">${esc(t("f.par.dReorderPoint"))}</th><th class="num">${esc(t("f.inv.dValue"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`
            : `<div class="empty">${esc(t("prod.noStock"))}</div>`}</div>`;
      },
      bind: (m) => { const b = $("#prodMove"); if (b) b.addEventListener("click", () => newWith("movements", { cProduct: m.cCode, cDescFR: dl(m, "cDesc"), cWarehouse: m.cDefaultWarehouse || "ENT-01" })); },
    },
  },
  warehouses: {
    api: "warehouses", route: "/inv/warehouses", tabset: "wh", title: "wh.title", sub: "wh.subtitle", one: "wh.one", newTitle: "wh.new",
    id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cName")}`, sort: "cCode",
    columns: [
      { f: "cCode", l: "f.cCode" }, { f: "cNameFR", l: "f.cName", wrap: true, fmt: (v, r) => esc(dl(r, "cName")) },
      { f: "cType", l: "f.wh.cType", fmt: (v) => esc(t("o.wh." + v)) }, { f: "cCity", l: "f.cCity" },
      { f: "lUseLocations", l: "f.wh.lUseLocations", fmt: yesNo }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    defaults: { cType: "main", cProvince: "QC", cCountry: "CA", lUseLocations: true, lActive: true },
    sections: [
      { t: "common.general", fields: [
        { f: "cCode", l: "f.cCode", req: true, key: true },
        { f: "cType", l: "f.wh.cType", type: "select", options: opts("o.wh.", ["main", "transit", "consignment", "quarantine", "virtual"]) },
        { f: "cManager", l: "f.wh.cManager" }, { f: "lActive", l: "opt.active", type: "check" },
        { f: "cNameFR", l: "f.cNameFR", req: true, span: 2 }, { f: "cNameEN", l: "f.cNameEN", span: 2 },
      ] },
      { t: "sup.address", fields: [
        { f: "cAddress1", l: "f.cAddress1", span: 2 }, { f: "cCity", l: "f.cCity" }, { f: "cProvince", l: "f.cProvince" },
        { f: "cZipCode", l: "f.cZipCode" }, { f: "cCountry", l: "f.cCountry" }, { f: "cPhone", l: "f.wh.cPhone" }, { f: "cEmail", l: "f.email", type: "email" },
      ] },
      { t: "wh.rules", help: "wh.rules.help", fields: [
        { f: "lUseLocations", l: "f.wh.lUseLocations", type: "check", help: "f.wh.lUseLocations.help" },
        { f: "lAllowNegative", l: "f.wh.lAllowNegative", type: "check" },
        { f: "cReceivingLoc", l: "f.wh.cReceivingLoc", lookup: "locations", lookupParams: (m) => ({ wh: m.cCode }) },
        { f: "cShippingLoc", l: "f.wh.cShippingLoc", lookup: "locations", lookupParams: (m) => ({ wh: m.cCode }) },
      ] },
    ],
  },
  locations: {
    api: "locations", route: "/inv/locations", tabset: "wh", title: "wh.title", sub: "wh.subtitle", one: "loc.one", newTitle: "loc.new",
    id: (r) => r.cWarehouse + "/" + r.cCode, label: (r) => `${r.cWarehouse} / ${r.cCode}`, sort: "iPickSeq",
    filters: [whFilter, { f: "cType", l: "f.loc.cType", options: opts("o.loc.", LOCATION_TYPES) }, { f: "lBlocked", l: "f.loc.lBlocked", options: [["true", "common.yes"], ["false", "common.no"]] }],
    columns: [
      { f: "cWarehouse", l: "f.inv.cWarehouse" }, { f: "cCode", l: "f.loc.cCode" }, { f: "cZone", l: "f.loc.cZone" }, { f: "cAisle", l: "f.loc.cAisle" },
      { f: "cRack", l: "f.loc.cRack" }, { f: "cLevel", l: "f.loc.cLevel" }, { f: "cBin", l: "f.loc.cBin" },
      { f: "cType", l: "f.loc.cType", fmt: (v) => esc(t("o.loc." + v)) }, { f: "cDescription", l: "f.cDescription", wrap: true },
      { f: "iPickSeq", l: "f.loc.iPickSeq", num: true },
      { f: "lBlocked", l: "f.loc.lBlocked", fmt: (v) => (v ? `<span class="badge no">${esc(t("f.loc.lBlocked"))}</span>` : "") },
    ],
    defaults: () => ({ cWarehouse: "ENT-01", cType: "picking", lMixProducts: true, lMixLots: true, lActive: true }),
    sections: [
      { t: "common.general", fields: [
        { f: "cWarehouse", l: "f.inv.cWarehouse", req: true, key: true, lookup: "warehouses" },
        { f: "cCode", l: "f.loc.cCode", key: true, help: "f.loc.cCode.help" },
        { f: "cType", l: "f.loc.cType", type: "select", options: opts("o.loc.", LOCATION_TYPES) },
        { f: "dQtyOnHand", l: "f.inv.dQtyOnHand", readonly: true, show: (m, n) => !n },
        { f: "cDescription", l: "f.cDescription", span: 2 }, { f: "lActive", l: "opt.active", type: "check" },
        { f: "lBlocked", l: "f.loc.lBlocked", type: "check", help: "f.loc.lBlocked.help" },
      ] },
      { t: "loc.hierarchy", help: "loc.hierarchy.help", fields: [
        { f: "cZone", l: "f.loc.cZone" }, { f: "cAisle", l: "f.loc.cAisle" }, { f: "cRack", l: "f.loc.cRack" }, { f: "cLevel", l: "f.loc.cLevel" },
        { f: "cBin", l: "f.loc.cBin" }, { f: "iPickSeq", l: "f.loc.iPickSeq", type: "number", help: "f.loc.iPickSeq.help" },
      ] },
      { t: "loc.wms", help: "loc.wms.help", fields: [
        { f: "dMaxWeight", l: "f.loc.dMaxWeight", type: "number" }, { f: "dMaxVolume", l: "f.loc.dMaxVolume", type: "number" },
        { f: "iMaxPallets", l: "f.loc.iMaxPallets", type: "number" },
        { f: "lMixProducts", l: "f.loc.lMixProducts", type: "check" }, { f: "lMixLots", l: "f.loc.lMixLots", type: "check" },
      ] },
    ],
  },
  params: {
    api: "stock-params", route: "/inv/params", title: "par.title", sub: "par.subtitle", one: "par.one", newTitle: "par.new",
    id: (r) => r.cProduct + "/" + r.cWarehouse, label: (r) => `${r.cProduct} / ${r.cWarehouse}`, sort: "cProduct",
    filters: [whFilter],
    columns: [
      { f: "cProduct", l: "f.prod.cCode" }, descCol("cDesc"), { f: "cWarehouse", l: "f.inv.cWarehouse" },
      { f: "dReorderPoint", l: "f.par.dReorderPoint", num: true, fmt: (v) => esc(qtyFmt(v)) },
      { f: "dMinQty", l: "f.par.dMinQty", num: true, fmt: (v) => esc(qtyFmt(v)) }, { f: "dMaxQty", l: "f.par.dMaxQty", num: true, fmt: (v) => esc(qtyFmt(v)) },
      { f: "dOrderQty", l: "f.par.dOrderQty", num: true, fmt: (v) => esc(qtyFmt(v)) },
      { f: "dQtyAvailable", l: "f.inv.dQtyAvailable", num: true, fmt: (v, r) => `<span class="${r.dReorderPoint !== "" && num(v) <= num(r.dReorderPoint) ? "low" : ""}">${esc(qtyFmt(v))}</span>` },
      { f: "cDefaultLocation", l: "f.par.cDefaultLocation" },
    ],
    defaults: () => ({ cWarehouse: "ENT-01", lActive: true }),
    sections: [
      { t: "common.general", help: "par.help", fields: [
        { f: "cProduct", l: "f.prod.cCode", req: true, key: true, lookup: "stockproducts" },
        { f: "cWarehouse", l: "f.inv.cWarehouse", req: true, key: true, lookup: "warehouses" },
        { f: "cDefaultLocation", l: "f.par.cDefaultLocation", lookup: "locations", lookupParams: (m) => ({ wh: m.cWarehouse }) },
        { f: "lActive", l: "opt.active", type: "check" },
        { f: "dReorderPoint", l: "f.par.dReorderPoint", type: "number", help: "f.par.dReorderPoint.help" },
        { f: "dMinQty", l: "f.par.dMinQty", type: "number" }, { f: "dMaxQty", l: "f.par.dMaxQty", type: "number", help: "f.par.dMaxQty.help" },
        { f: "dOrderQty", l: "f.par.dOrderQty", type: "number", help: "f.par.dOrderQty.help" },
        { f: "iLeadTimeDays", l: "f.prod.iLeadTimeDays", type: "number" },
      ] },
    ],
  },
  movements: {
    api: "stock-movements", route: "/inv/movements", title: "mv.title", sub: "mv.subtitle", one: "mv.one", newTitle: "mv.new",
    id: (r) => r.iNo, label: (r) => `#${r.iNo} — ${r.cProduct}`, sort: "iNo", dir: "desc", noDelete: true,
    locked: (m, isNew) => !isNew,
    badge: (m, isNew) => (isNew ? "" : `<span class="badge mv-${esc(m.cType)}">${esc(t("o.mv." + m.cType))}</span>`),
    sub2: (m, isNew) => (isNew ? t("mv.newHelp") : t("mv.postedBy", { u: m.cUser, d: fmtDateTime(m.dCreated) })),
    filters: [{ f: "cType", l: "f.mv.cType", options: opts("o.mv.", MOVE_TYPES) }, whFilter],
    columns: [
      { f: "iNo", l: "#", num: true }, { f: "dDate", l: "f.mv.dDate" },
      { f: "cType", l: "f.mv.cType", fmt: (v) => `<span class="badge mv-${esc(v)}">${esc(t("o.mv." + v))}</span>` },
      { f: "cProduct", l: "f.prod.cCode" }, descCol("cDesc"),
      { f: "cWarehouse", l: "f.mv.place", fmt: (v, r) => esc(v + (r.cLocation ? " / " + r.cLocation : "") + (r.cWhTo ? " → " + r.cWhTo + (r.cLocTo ? " / " + r.cLocTo : "") : "")) },
      { f: "cLot", l: "f.mv.lotSerial", fmt: (v, r) => esc([v, r.cSerial].filter(Boolean).join(" · ")) },
      { f: "dQty", l: "f.mv.dQty", num: true, fmt: (v, r) => esc(qtyFmt(v) + " " + (r.cUOM || "")) },
      { f: "dValue", l: "f.inv.dValue", num: true, fmt: (v) => esc(money(v)) },
      { f: "cDocNo", l: "f.mv.doc", fmt: (v, r) => esc(t("o.doc." + r.cDocType) + (v ? " " + v : "")) }, { f: "cUser", l: "f.mv.cUser" },
    ],
    defaults: () => ({ cType: "IN", dDate: today(), cDocType: "MAN", cWarehouse: "ENT-01", dQty: "1" }),
    sections: [
      { t: "common.general", fields: [
        { f: "cType", l: "f.mv.cType", type: "select", options: opts("o.mv.", MOVE_TYPES), rerender: true, help: "mv.typeHelp" },
        { f: "dDate", l: "f.mv.dDate", type: "date", req: true },
        { f: "cProduct", l: "f.prod.cCode", req: true, lookup: "stockproducts", fill: "cDescFR" },
        { f: "cDescFR", l: "f.cDescription", readonly: true },
        { f: "dQty", l: "f.mv.dQty", type: "number", req: true, help: "mv.qtyHelp" },
        { f: "dUnitCost", l: "f.mv.dUnitCost", type: "number", show: (m, n) => !n || MV_IN(m), help: "mv.costHelp" },
        { f: "dValue", l: "f.inv.dValue", readonly: true, show: (m, n) => !n },
        { f: "dAvgCostAfter", l: "f.mv.dAvgCostAfter", readonly: true, show: (m, n) => !n },
      ] },
      { t: "mv.place", fields: [
        { f: "cWarehouse", l: "f.inv.cWarehouse", req: true, lookup: "warehouses" },
        { f: "cLocation", l: "f.mv.cLocation", lookup: "locations", lookupParams: (m) => ({ wh: m.cWarehouse }) },
        { f: "cWhTo", l: "f.mv.cWhTo", req: true, lookup: "warehouses", show: (m) => m.cType === "TRF" },
        { f: "cLocTo", l: "f.mv.cLocTo", lookup: "locations", lookupParams: (m) => ({ wh: m.cWhTo }), show: (m) => m.cType === "TRF" },
      ] },
      { t: "mv.tracking", help: "mv.trackingHelp", fields: [
        { f: "cLot", l: "f.mv.cLot" }, { f: "cSerial", l: "f.mv.cSerial" }, { f: "dExpiry", l: "f.mv.dExpiry", type: "date" },
      ] },
      { t: "mv.reference", fields: [
        { f: "cDocType", l: "f.mv.cDocType", type: "select", options: opts("o.doc.", DOC_TYPES) }, { f: "cDocNo", l: "f.mv.cDocNo" },
        { f: "cReason", l: "f.mv.cReason", span: 2 }, { f: "cComment", l: "f.Commentaires", type: "textarea", span: 4 },
      ] },
    ],
  },
  counts: {
    api: "stock-counts", route: "/inv/counts", title: "cnt.title", sub: "cnt.subtitle", one: "cnt.one", newTitle: "cnt.new",
    id: (r) => r.iNo, label: (r) => `#${r.iNo} — ${r.cWarehouse}`, sort: "iNo", dir: "desc",
    locked: (m) => m.cStatus === "Posted",
    badge: (m, isNew) => (isNew ? "" : statusBadge(m.cStatus)),
    sub2: (m, isNew) => (isNew ? t("cnt.newHelp") : t("cnt.progress", { c: m.countedLines, n: m.lineCount })),
    filters: [{ f: "cStatus", l: "f.cStatut", options: [["Draft", "status.Draft"], ["Posted", "status.Posted"]] }, whFilter],
    columns: [
      { f: "iNo", l: "#", num: true }, { f: "dDate", l: "f.mv.dDate" }, { f: "cWarehouse", l: "f.inv.cWarehouse" },
      { f: "cDescription", l: "f.cDescription", wrap: true }, { f: "lineCount", l: "common.lineCount", num: true },
      { f: "countedLines", l: "cnt.counted", num: true }, { f: "cStatus", l: "f.cStatut", fmt: statusBadge },
    ],
    defaults: () => ({ cWarehouse: "ENT-01", dDate: today(), lines: [] }),
    sections: [{ t: "common.general", fields: [
      { f: "cWarehouse", l: "f.inv.cWarehouse", req: true, key: true, lookup: "warehouses" },
      { f: "dDate", l: "f.mv.dDate", type: "date" }, { f: "cDescription", l: "f.cDescription", span: 2 },
      { f: "cLocationPrefix", l: "f.cnt.cLocationPrefix", help: "f.cnt.cLocationPrefix.help" },
      { f: "cProductPrefix", l: "f.cnt.cProductPrefix", help: "f.cnt.cProductPrefix.help" },
      { f: "dPosted", l: "f.cnt.dPosted", readonly: true, show: (m) => m.cStatus === "Posted" },
      { f: "dValueDiff", l: "f.cnt.dValueDiff", readonly: true, show: (m) => m.cStatus === "Posted" },
    ] }],
    lines: {
      title: "cnt.lines", help: "cnt.linesHelp", show: (m, isNew) => !isNew,
      rowClass: (l) => (l.dDiff !== "" && l.dDiff != null && num(l.dDiff) !== 0 ? "diff" : ""),
      cols: [
        { f: "cProduct", l: "f.prod.cCode", w: "w-md", lookup: "stockproducts", fill: "cDescFR" }, { f: "cDescFR", l: "f.cDescription", w: "w-lg", ro: true },
        { f: "cLocation", l: "f.mv.cLocation", w: "w-md", lookup: "locations", lookupParams: (m) => ({ wh: m.cWarehouse }) },
        { f: "cLot", l: "f.mv.cLot", w: "w-sm" }, { f: "cSerial", l: "f.mv.cSerial", w: "w-sm" },
        { f: "dQtyExpected", l: "f.cnt.dQtyExpected", w: "w-xs", n: true, ro: true },
        { f: "dQtyCounted", l: "f.cnt.dQtyCounted", w: "w-sm", n: true }, { f: "dDiff", l: "f.cnt.dDiff", w: "w-xs", n: true, ro: true },
      ],
    },
    actions: [
      { id: "generate", l: "cnt.generate", show: (m, isNew) => !isNew && m.cStatus === "Draft", confirm: "cnt.generateConfirm",
        run: async (m, ctx) => { await api(ctx.path, { method: "PUT", body: m }); return api(ctx.path + "/generate", { method: "POST" }); } },
      { id: "post", l: "cnt.post", primary: true, show: (m, isNew) => !isNew && m.cStatus === "Draft", confirm: "cnt.postConfirm", done: "cnt.posted",
        run: async (m, ctx) => { await api(ctx.path, { method: "PUT", body: m }); return api(ctx.path + "/post", { method: "POST" }); } },
    ],
  },
  stock: {
    api: "inventory/stock", route: "/inv/stock", title: "stk.title", sub: "stk.subtitle", noNew: true, rowHref: productLink,
    id: (r) => r.cProduct, sort: "cProduct", filters: [whFilter],
    columns: [
      { f: "cProduct", l: "f.prod.cCode" }, descCol("cDesc"), { f: "cWarehouse", l: "f.inv.cWarehouse" }, { f: "cLocation", l: "f.mv.cLocation" },
      { f: "cLot", l: "f.mv.cLot" }, { f: "cSerial", l: "f.mv.cSerial" }, { f: "dExpiry", l: "f.mv.dExpiry" },
      { f: "dQtyOnHand", l: "f.inv.dQtyOnHand", num: true, fmt: (v) => esc(qtyFmt(v)) },
      { f: "dQtyReserved", l: "f.inv.dQtyReserved", num: true, fmt: (v) => esc(qtyFmt(v)) },
      { f: "dQtyAvailable", l: "f.inv.dQtyAvailable", num: true, fmt: (v) => esc(qtyFmt(v)) }, { f: "cUOM", l: "f.prod.unit" },
      { f: "dValue", l: "f.inv.dValue", num: true, fmt: (v) => esc(money(v)) },
    ],
  },
  valuation: {
    api: "inventory/valuation", route: "/inv/valuation", title: "val.title", sub: "val.subtitle", noNew: true, rowHref: productLink,
    id: (r) => r.cProduct, sort: "cProduct", filters: [whFilter],
    columns: [
      { f: "cProduct", l: "f.prod.cCode" }, descCol("cDesc"), { f: "cCategory", l: "f.prod.cCategory" }, { f: "cWarehouse", l: "f.inv.cWarehouse" },
      { f: "cCostMethod", l: "f.prod.cCostMethod", fmt: (v) => esc(t("o.cost." + v)) },
      { f: "dQtyOnHand", l: "f.inv.dQtyOnHand", num: true, fmt: (v, r) => esc(qtyFmt(v) + " " + r.cUOM) },
      { f: "dUnitCost", l: "f.mv.dUnitCost", num: true, fmt: (v) => esc(money(v)) },
      { f: "dValue", l: "f.inv.dValue", num: true, fmt: (v) => esc(money(v)) }, { f: "cGLInventory", l: "f.prod.cGLInventory" },
    ],
    footer: (data) => `<div class="totals"><table><tr class="grand"><td>${esc(t("val.total"))}</td><td>${esc(money(data.totalValue))}</td></tr></table></div>`,
  },
});
