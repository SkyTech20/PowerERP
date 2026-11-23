/* PowerERP: Sales: list / form definitions. V1: the customers (ship-to addresses and contacts). */
import { esc, t, yesNo } from "../core.js";
import { RES } from "../registry.js";
import { opts } from "./inventory.js";

export const LANGS = ["fr", "en"];

Object.assign(RES, {
  customers: {
    api: "customers", route: "/sales/customers", title: "sales.cust.title", sub: "sales.cust.subtitle",
    one: "sales.cust.one", newTitle: "sales.cust.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${r.cName}`, sort: "cName",
    columns: [
      { f: "cCode", l: "f.cCode" }, { f: "cName", l: "f.cName", wrap: true }, { f: "cCity", l: "f.cCity" },
      { f: "cProvince", l: "f.cProvince" }, { f: "cTaxGroup", l: "sales.f.cTaxGroup" },
      { f: "cLang", l: "sales.f.cLang", fmt: (v) => esc(t("sales.o.lang." + v)) },
      { f: "iAddresses", l: "sales.cust.shipTos", n: true }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    filters: [
      { f: "cTaxGroup", l: "sales.f.cTaxGroup", lookup: "taxgroups" },
      { f: "lActive", l: "opt.active", options: [["true", "common.yes"], ["false", "common.no"]] },
    ],
    defaults: () => ({ cLang: "fr", cProvince: "QC", cCountry: "CA", cTaxGroup: "QC", lActive: true, addresses: [], contacts: [] }),
    formTabs: [["gen", "common.general"], ["ship", "sales.cust.tab.shipTo"], ["contacts", "sales.cust.tab.contacts"]],
    sections: [
      { tab: "gen", t: "common.general", fields: [
        { f: "cCode", l: "f.cCode", req: true, key: true, help: "sales.cust.code.help" },
        { f: "cName", l: "f.cName", req: true, span: 2 },
        { f: "lActive", l: "opt.active", type: "check" },
        { f: "cLegalName", l: "sales.f.cLegalName", span: 2, help: "sales.f.cLegalName.help" },
        { f: "cLang", l: "sales.f.cLang", type: "select", options: opts("sales.o.lang.", LANGS), help: "sales.f.cLang.help" },
      ] },
      { tab: "gen", t: "sales.cust.billTo", fields: [
        { f: "cAddress1", l: "f.cAddress1", span: 2 }, { f: "cAddress2", l: "f.cAddress2", span: 2 },
        { f: "cCity", l: "f.cCity" }, { f: "cProvince", l: "f.cProvince" }, { f: "cCountry", l: "f.cCountry" }, { f: "cZipCode", l: "f.cZipCode" },
        { f: "cPhone", l: "sales.f.cPhone" }, { f: "cEmail", l: "sales.f.cEmail", span: 2, help: "sales.f.cEmail.help" },
      ] },
      { tab: "gen", t: "sales.cust.billing", fields: [
        { f: "cTaxGroup", l: "sales.f.cTaxGroup", req: true, lookup: "taxgroups", help: "sales.f.cTaxGroup.help" },
        { f: "cTaxExemptNo", l: "sales.f.cTaxExemptNo", help: "sales.f.cTaxExemptNo.help" },
        { f: "cTermCode", l: "f.cTermCode", lookup: "customer_terms", free: true, fill: "cTermDesc" }, { f: "cTermDesc", l: "f.cTermDesc" },
        { f: "dDiscountPct", l: "sales.f.dDiscountPct", type: "number", help: "sales.f.dDiscountPct.help" },
        { f: "cWarehouse", l: "sales.f.cWarehouse", lookup: "warehouses", help: "sales.f.cWarehouse.help" },
        { f: "cNotes", l: "sales.f.cNotes", type: "textarea", span: 4 },
      ] },
    ],
    grids: [
      { key: "addresses", tab: "ship", title: "sales.cust.tab.shipTo", help: "sales.cust.shipTo.help",
        cols: [
          { f: "cCode", l: "f.cCode", w: "w-sm" }, { f: "cName", l: "f.cName", w: "w-md" },
          { f: "cAddress1", l: "f.cAddress1", w: "w-md" }, { f: "cAddress2", l: "f.cAddress2", w: "w-sm" },
          { f: "cCity", l: "f.cCity", w: "w-sm" }, { f: "cProvince", l: "sales.f.cProv", w: "w-xs" },
          { f: "cZipCode", l: "f.cZipCode", w: "w-sm" }, { f: "cCountry", l: "sales.f.cCtry", w: "w-xs" },
          { f: "cContact", l: "sales.f.cContact", w: "w-sm" }, { f: "cPhone", l: "sales.f.cPhone", w: "w-sm" },
          { f: "cTaxGroup", l: "sales.f.cTaxGroup", w: "w-sm", lookup: "taxgroups" },
          { f: "lDefault", l: "sales.f.lDefault", w: "w-xs", type: "check" },
        ],
        newLine: (m) => ({ cCode: "", cName: m.cName || "", cAddress1: "", cAddress2: "", cCity: "", cProvince: m.cProvince || "QC", cZipCode: "",
          cCountry: m.cCountry || "CA", cContact: "", cPhone: "", cTaxGroup: "", lDefault: !(m.addresses || []).length }) },
      { key: "contacts", tab: "contacts", title: "sales.cust.tab.contacts", help: "sales.cust.contacts.help",
        cols: [
          { f: "cName", l: "f.cName", w: "w-md" }, { f: "cTitle", l: "sales.f.cTitle", w: "w-md" },
          { f: "cPhone", l: "sales.f.cPhone", w: "w-sm" }, { f: "cEmail", l: "sales.f.cEmail", w: "w-lg" },
          { f: "lInvoices", l: "sales.f.lInvoices", w: "w-xs", type: "check" },
        ],
        newLine: () => ({ cName: "", cTitle: "", cPhone: "", cEmail: "", lInvoices: false }) },
    ],
  },
});
