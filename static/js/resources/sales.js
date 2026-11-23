/* PowerERP: Sales: list / form definitions. V1: the customers (ship-to addresses and contacts); V2: the price lists,
   and the price check of a customer. */
import { $, api, enc, esc, lang, num, t, yesNo } from "../core.js";
import { lookupOptions, lookupRows } from "../lookups.js";
import { RES } from "../registry.js";
import { dl, opts, today } from "./inventory.js";

export const LANGS = ["fr", "en"];
const price = (v) => (v === "" || v == null ? "" : new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { minimumFractionDigits: 2, maximumFractionDigits: 4 }).format(num(v)));

// The price rule that gave a price / a discount, in words
export function priceSource(r) {
  if (r.cPriceSource === "price_list") return t("sales.check.fromList", { l: r.cPriceList, q: r.dMinQty, u: r.cUOM });
  return t(r.cPriceList ? "sales.check.notInList" : "sales.check.listPrice", { l: r.cPriceList });
}
export function discountSource(r) {
  if (r.cDiscountSource === "line") return t("sales.check.discLine", { l: r.cPriceList });
  if (r.cDiscountSource === "category") return t("sales.check.discCategory", { l: r.cPriceList, c: r.cDiscountCategory });
  if (r.cDiscountSource === "customer") return t("sales.check.discCustomer");
  return t("sales.check.noDiscount");
}

// Customer > Price check: what the customer pays for a product, and why
const priceCheck = {
  tab: "prices",
  html: () => `<div class="card"><div class="card-head"><h2>${esc(t("sales.check.title"))}</h2><span class="help muted">${esc(t("sales.check.help"))}</span></div>
    <div class="card-body"><div class="form-grid">
      <div class="field span-2"><label for="pcProduct">${esc(t("sales.check.product"))}</label><select id="pcProduct"></select></div>
      <div class="field"><label for="pcQty">${esc(t("sales.check.qty"))}</label><input type="text" id="pcQty" inputmode="decimal" value="1" style="text-align:right"></div>
      <div class="field"><label for="pcUom">${esc(t("sales.check.uom"))}</label><input type="text" id="pcUom" placeholder="${esc(t("sales.check.uom.ph"))}"></div>
      <div class="field"><label for="pcDate">${esc(t("sales.check.date"))}</label><input type="date" id="pcDate" value="${today()}"></div>
    </div><div id="pcResult"></div></div></div>`,
  bind: (m) => {
    const sel = $("#pcProduct");
    lookupRows("sellable_products").then((rows) => {
      sel.innerHTML = lookupOptions(rows, rows.length ? rows[0].code : "");
      run();
    });
    const run = async () => {
      const out = $("#pcResult");
      if (!sel.value) { out.innerHTML = ""; return; }
      const q = `customer=${enc(m.cCode)}&product=${enc(sel.value)}&qty=${enc($("#pcQty").value)}&uom=${enc($("#pcUom").value)}&date=${enc($("#pcDate").value)}`;
      try {
        const r = await api("pricing?" + q);
        out.innerHTML = `<table class="grid"><tbody>
          <tr><td>${esc(t("sales.check.listPriceRow"))}</td><td class="num">${esc(price(r.dListPrice))}</td><td class="muted">${esc(t("sales.check.per", { u: r.cUOM }))}</td></tr>
          <tr><td>${esc(t("sales.check.price"))}</td><td class="num">${esc(price(r.dPrice))}</td><td>${esc(priceSource(r))}</td></tr>
          <tr><td>${esc(t("sales.check.discount"))}</td><td class="num">${r.cDiscountSource ? esc(r.dDiscountPct) + " %" : ""}</td><td>${esc(discountSource(r))}</td></tr>
          <tr class="total-row"><td>${esc(t("sales.check.net"))}</td><td class="num">${esc(price(r.dNetPrice))}</td><td>${r.lBelowMinPrice ? `<span class="badge no">${esc(t("sales.check.belowMin", { p: price(r.dMinPrice) }))}</span>` : ""}${r.lNoPrice ? `<span class="badge no">${esc(t("sales.check.noPrice"))}</span>` : ""}</td></tr>
        </tbody></table>`;
      } catch (err) {
        out.innerHTML = `<p class="help">${esc(t("err." + err.code) !== "err." + err.code ? t("err." + err.code) : t("err.generic"))}</p>`;
      }
    };
    ["#pcProduct", "#pcQty", "#pcUom", "#pcDate"].forEach((s) => $(s).addEventListener("change", run));
  },
};

Object.assign(RES, {
  customers: {
    api: "customers", route: "/sales/customers", title: "sales.cust.title", sub: "sales.cust.subtitle",
    one: "sales.cust.one", newTitle: "sales.cust.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${r.cName}`, sort: "cName",
    columns: [
      { f: "cCode", l: "f.cCode" }, { f: "cName", l: "f.cName", wrap: true }, { f: "cCity", l: "f.cCity" },
      { f: "cProvince", l: "f.cProvince" }, { f: "cTaxGroup", l: "sales.f.cTaxGroup" },
      { f: "cLang", l: "sales.f.cLang", fmt: (v) => esc(t("sales.o.lang." + v)) },
      { f: "cPriceList", l: "sales.f.cPriceList" },
      { f: "iAddresses", l: "sales.cust.shipTos", n: true }, { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    filters: [
      { f: "cTaxGroup", l: "sales.f.cTaxGroup", lookup: "taxgroups" },
      { f: "cPriceList", l: "sales.f.cPriceList", lookup: "price_lists" },
      { f: "lActive", l: "opt.active", options: [["true", "common.yes"], ["false", "common.no"]] },
    ],
    defaults: () => ({ cLang: "fr", cProvince: "QC", cCountry: "CA", cTaxGroup: "QC", lActive: true, addresses: [], contacts: [] }),
    formTabs: [["gen", "common.general"], ["ship", "sales.cust.tab.shipTo"], ["contacts", "sales.cust.tab.contacts"], ["prices", "sales.check.tab"]],
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
        { f: "cPriceList", l: "sales.f.cPriceList", lookup: "price_lists", help: "sales.f.cPriceList.help" },
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
    panel: priceCheck,
  },
  pricelists: {
    api: "price-lists", route: "/sales/price-lists", title: "sales.pl.title", sub: "sales.pl.subtitle",
    one: "sales.pl.one", newTitle: "sales.pl.new", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
    columns: [
      { f: "cCode", l: "f.cCode" }, { f: "cDescFR", l: "f.cDescription", wrap: true, fmt: (v, r) => esc(dl(r, "cDesc")) },
      { f: "dStartDate", l: "sales.f.dStartDate" }, { f: "dEndDate", l: "sales.f.dEndDate" },
      { f: "iProducts", l: "sales.pl.products", n: true }, { f: "iCustomers", l: "sales.pl.customers", n: true },
      { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    defaults: () => ({ lActive: true, lines: [], discounts: [] }),
    formTabs: [["gen", "common.general"], ["prices", "sales.pl.tab.prices"], ["disc", "sales.pl.tab.discounts"]],
    sections: [
      { tab: "gen", t: "common.general", help: "sales.pl.help", fields: [
        { f: "cCode", l: "f.cCode", req: true, key: true, help: "sales.pl.code.help" },
        { f: "dStartDate", l: "sales.f.dStartDate", type: "date", help: "sales.f.dStartDate.help" },
        { f: "dEndDate", l: "sales.f.dEndDate", type: "date" },
        { f: "lActive", l: "opt.active", type: "check" },
        { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
        { f: "cNotes", l: "sales.f.cNotes", type: "textarea", span: 4 },
      ] },
    ],
    lines: {
      tab: "prices", title: "sales.pl.tab.prices", help: "sales.pl.prices.help",
        cols: [
          { f: "cProduct", l: "sales.f.cProduct", w: "w-lg", lookup: "sellable_products" },
          { f: "cUOM", l: "sales.f.cUOM", w: "w-md", lookup: "uom" },
          { f: "dMinQty", l: "sales.f.dMinQty", w: "w-sm", n: true },
          { f: "dPrice", l: "sales.f.dPrice", w: "w-sm", n: true },
          { f: "dDiscountPct", l: "sales.f.dLineDiscountPct", w: "w-sm", n: true },
        ],
      newLine: () => ({ cProduct: "", cUOM: "", dMinQty: "0", dPrice: "", dDiscountPct: "" }),
    },
    grids: [
      { key: "discounts", tab: "disc", title: "sales.pl.tab.discounts", help: "sales.pl.discounts.help",
        cols: [{ f: "cCategory", l: "sales.f.cCategory", w: "w-lg", lookup: "categories" }, { f: "dDiscountPct", l: "sales.f.dDiscountPct", w: "w-sm", n: true }],
        newLine: () => ({ cCategory: "", dDiscountPct: "" }) },
    ],
    panel: {
      tab: "gen",
      html: (m) => `<div class="card"><div class="card-head"><h2>${esc(t("sales.pl.customers"))}</h2><span class="help muted">${esc(t("sales.pl.customers.help"))}</span></div>
        <div class="card-body">${(m.customers || []).length ? (m.customers || []).map((c) => `<a class="badge" href="#/sales/customers/${enc(c)}">${esc(c)}</a>`).join(" ") : `<p class="help">${esc(t("sales.pl.noCustomers"))}</p>`}</div></div>`,
    },
  },
});
