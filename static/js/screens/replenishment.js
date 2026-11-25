/* PowerERP: Inventory > Replenishment. */
import { $, $$, api, enc, esc, fmtInt, lang, money, num, numOnly, t, toast } from "../core.js";
import { dl, productLink, qtyFmt } from "../resources/inventory.js";
import { canOpen } from "../router.js";
import { can } from "../state.js";
import { decorateScreen, helpButtonOf } from "../helpui.js";
import { pageHead } from "../views.js";

// ---------- Replenishment: products at or below their reorder point, and the POs to create
export function replenishmentView() {
  let data = null;
  let wh = "";
  let whs = [];
  let created = null;
  return {
    async load() {
      whs = await api("lookups/warehouses?lang=" + lang);
      data = await api("inventory/replenishment?size=500" + (wh ? "&f_cWarehouse=" + enc(wh) : ""));
      data.items.forEach((r) => { r.pick = !!r.cSupplierCode; });
    },
    render() {
      const rows = data.items.map((r, i) => `<tr data-i="${i}">
          <td><input type="checkbox" data-pick ${r.pick ? "checked" : ""} ${r.cSupplierCode ? "" : "disabled"} aria-label="${esc(t("rep.pick"))}"></td>
          <td>${canOpen(productLink(r)) ? `<a href="#${productLink(r)}">${esc(r.cProduct)}</a>` : esc(r.cProduct)}</td><td class="wrap">${esc(dl(r, "cDesc"))}</td><td>${esc(r.cWarehouse)}</td>
          <td class="num">${esc(qtyFmt(r.dQtyAvailable))}</td><td class="num">${esc(qtyFmt(r.dQtyOnOrder))}</td>
          <td class="num">${esc(qtyFmt(r.dReorderPoint))}</td><td class="num">${esc(qtyFmt(r.dMaxQty))}</td>
          <td class="num">${esc(qtyFmt(r.dSuggestedQty))} ${esc(r.cStockUOM)}</td>
          <td class="w-sm"><input type="text" data-qty value="${esc(r.dPurchaseQty)}" inputmode="decimal" style="text-align:right;width:70px"> ${esc(r.cPurchaseUOM)}</td>
          <td>${r.cSupplierCode ? esc(r.cSupplierCode + " — " + r.cSupplierName) : `<span class="badge no">${esc(t("rep.noSupplier"))}</span>`}</td>
          <td class="num">${esc(money(r.dUnitCost))}</td><td class="num" data-amt></td></tr>`).join("");
      const done = created ? `<div class="card notice"><div class="card-body">${esc(t("rep.created"))}
          ${created.map((p) => `<a class="btn small" href="#/po/${enc(p.cPO)}">${esc(p.cPO)} — ${esc(p.cSupplierName)} (${esc(money(p.dTotalAmount))})</a>`).join(" ")}</div></div>` : "";
      $("#view").innerHTML = pageHead(t("rep.title"), t("rep.subtitle"), helpButtonOf("inv.replenishment") + (can("inv.replenishment", "create_po") ? `<button class="btn primary" id="createPo" ${data.items.length ? "" : "disabled"}>${esc(t("rep.createPo"))}</button>` : "")) + done + `
        <div class="card"><div class="toolbar"><select id="repWh" style="width:auto"><option value="">${esc(t("f.inv.cWarehouse"))}: ${esc(t("common.all"))}</option>
            ${whs.map((w) => `<option value="${esc(w.code)}" ${w.code === wh ? "selected" : ""}>${esc(w.code)} — ${esc(w.label)}</option>`).join("")}</select>
            <span class="help muted">${esc(t("rep.help"))}</span><span class="count">${esc(t("common.records", { n: fmtInt(data.total) }))}</span></div>
          <div class="table-wrap">${data.items.length ? `<table class="grid"><thead><tr><th></th><th>${esc(t("f.prod.cCode"))}</th><th>${esc(t("f.cDescription"))}</th><th>${esc(t("f.inv.cWarehouse"))}</th>
            <th class="num">${esc(t("f.inv.dQtyAvailable"))}</th><th class="num">${esc(t("f.inv.dQtyOnOrder"))}</th><th class="num">${esc(t("f.par.dReorderPoint"))}</th><th class="num">${esc(t("f.par.dMaxQty"))}</th>
            <th class="num">${esc(t("rep.suggested"))}</th><th>${esc(t("rep.toOrder"))}</th><th>${esc(t("f.cSupplierName"))}</th><th class="num">${esc(t("rep.unitCost"))}</th><th class="num">${esc(t("f.lineTotal"))}</th></tr></thead>
            <tbody>${rows}</tbody></table>` : `<div class="empty">${esc(t("rep.none"))}</div>`}</div>
          <div class="totals"><table><tr class="grand"><td>${esc(t("rep.total"))}</td><td id="repTotal"></td></tr></table></div></div>`;
      const totals = () => {
        let sum = 0;
        $$("tr[data-i]").forEach((tr) => {
          const r = data.items[+tr.dataset.i];
          const amt = num(r.dPurchaseQty) * num(r.dUnitCost);
          $("[data-amt]", tr).textContent = money(amt);
          if (r.pick) sum += amt;
        });
        $("#repTotal").textContent = money(sum);
      };
      $$("tr[data-i]").forEach((tr) => {
        const r = data.items[+tr.dataset.i];
        $("[data-pick]", tr).addEventListener("change", (e) => { r.pick = e.target.checked; totals(); });
        $("[data-qty]", tr).addEventListener("input", (e) => { r.dPurchaseQty = numOnly(e.target); totals(); });
      });
      totals();
      decorateScreen("inv.replenishment");
      $("#repWh").addEventListener("change", async (e) => { wh = e.target.value; created = null; await this.load(); this.render(); });
      if ($("#createPo")) $("#createPo").addEventListener("click", async () => {
        // Quantity and cost in purchase units (e.g. cases): the PO lines are converted to stock units by the ERP
        const lines = data.items.filter((r) => r.pick && num(r.dPurchaseQty) > 0)
          .map((r) => ({ cProduct: r.cProduct, dPurchaseQty: r.dPurchaseQty, cSupplierCode: r.cSupplierCode, dUnitCost: r.dUnitCost }));
        if (!lines.length) { toast(t("rep.nothing"), "error"); return; }
        if (!confirm(t("rep.confirm", { n: lines.length }))) return;
        try {
          const res = await api("inventory/replenishment/po", { method: "POST", body: { cWarehouse: wh, lines } });
          created = res.purchaseOrders;
          toast(t("rep.createdToast", { n: created.length }), "success");
          await this.load();
          this.render();
        } catch (e) { toast(t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic"), "error"); }
      });
    },
  };
}
