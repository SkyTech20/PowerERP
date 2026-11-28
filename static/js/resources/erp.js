/* PowerERP: General ledger, suppliers, purchasing, invoices and users: list / form definitions. */
import { CURRENCIES, api, esc, fmtDateTime, lang, money, num, roleName, sourceBadge, statusBadge, t, yesNo } from "../core.js";
import { RES } from "../registry.js";
import { route } from "../router.js";
import { setPrefill } from "../state.js";

// General ledger: the type of an account, the descriptions in the language of the screen (English: else French)
export const GL_TYPES = ["asset", "liability", "equity", "revenue", "expense"];
const glDesc = (r) => (lang === "en" && r.cDescEN) || r.cDesc || "";
const ccCode = (r) => `${r.cCC1}${r.cCC2 ? "-" + r.cCC2 : ""}`;
const activeFilter = { f: "lActive", l: "opt.active", options: [["true", "common.yes"], ["false", "common.no"]] };
// The cost center of a purchase line: the department, then one of its sub-departments
export const CC_COLS = [
  { f: "cCC1", l: "f.lCC1", w: "w-sm", lookup: "cc1" },
  { f: "cCC2", l: "f.lCC2", w: "w-sm", lookup: "cc2", lookupParams: (m, ln) => ({ cc1: ln.cCC1 || "-" }) },
];

// Receptions: put into the stock (Check shows what goes in; Put in stock posts it, then the reception is locked)
const recBadge = (posted) => `<span class="badge ${posted ? "yes" : ""}">${esc(t(posted ? "rec.badge.posted" : "rec.badge.pending"))}</span>`;

const recSaveThen = async (m, ctx, step) => {
  const saved = await api(ctx.path, { method: "PUT", body: m });
  const res = await api(ctx.path + "/" + step, { method: "POST" });
  return step === "check" ? { ...saved, _check: res } : res;
};

const recStock = {
  html: (m) => {
    const check = m._check;
    if (!check && !m.lStockPosted) return "";
    const problems = check && check.problems.length
      ? `<div class="alert error"><b>${esc(t("rec.stock.problems"))}</b><ul>${check.problems.map((p) =>
        `<li>${p.iLine ? `${esc(t("rec.stock.line"))} ${esc(p.iLine)}${p.cProduct ? " (" + esc(p.cProduct) + ")" : ""}: ` : ""}${esc(t("err." + p.code))}`
        + `${p.field && p.field !== "lines" ? " — " + esc(t(REC_FIELD_LABEL[p.field] || p.field)) : ""}${p.detail ? " — " + esc(p.detail) : ""}</li>`).join("")}</ul></div>`
      : check ? `<div class="alert success">${esc(t("rec.stock.ready"))}</div>` : "";
    const warnings = check && check.warnings.length
      ? `<div class="alert">${check.warnings.map((w) => esc(t("rec.warn." + w.code))).join("<br>")}</div>` : "";
    const head = (cols) => `<thead><tr>${cols.map(([l, n]) => `<th${n ? ' class="num"' : ""}>${esc(t(l))}</th>`).join("")}</tr></thead>`;
    let body;
    if (check) {
      const rows = check.entries;
      body = rows.length ? `<div class="table-wrap"><table class="grid">${head([["rec.stock.line"], ["f.CodeArticle"], ["f.Description"], ["rec.stock.qty", 1], ["f.mv.cLocation"], ["f.rec.cLot"], ["f.rec.cSupplierLot"], ["f.rec.dExpiry"], ["f.rec.cSerial"]])}
        <tbody>${rows.map((e) => `<tr${e.cSkip ? ' class="muted"' : ""}><td>${esc(e.iLine)}</td><td>${esc(e.cProduct)}</td><td>${esc(e.cDescription)}</td>
        <td class="num">${esc(e.dQty)} ${esc(e.cUOM)}</td>${e.cSkip ? `<td colspan="5">${esc(t("rec.skip." + e.cSkip))}</td>`
          : `<td>${esc(e.cLocation)}</td><td>${esc(e.cLot)}</td><td>${esc(e.cSupplierLot)}</td><td>${esc(e.dExpiry)}</td><td>${esc(e.cSerial)}</td>`}</tr>`).join("")}</tbody></table></div>`
        : `<p class="help">${esc(t("rec.stock.none"))}</p>`;
    } else {
      const rows = m.movements || [];
      body = rows.length ? `<div class="table-wrap"><table class="grid">${head([["rec.stock.movement"], ["f.CodeArticle"], ["rec.stock.qty", 1], ["f.mv.cLocation"], ["f.rec.cLot"], ["f.rec.dExpiry"], ["f.rec.cSerial"], ["rec.stock.value", 1]])}
        <tbody>${rows.map((mv) => `<tr><td><a href="#/inv/movements/${esc(mv.iNo)}">${esc(mv.iNo)}</a></td><td>${esc(mv.cProduct)}</td>
        <td class="num">${esc(mv.dQty)}</td><td>${esc(mv.cLocation)}</td><td>${esc(mv.cLot)}</td><td>${esc(mv.dExpiry || "")}</td><td>${esc(mv.cSerial)}</td>
        <td class="num">${esc(money(mv.dValue || 0))}</td></tr>`).join("")}</tbody></table></div>`
        : `<p class="help">${esc(t("rec.stock.none"))}</p>`;
    }
    return `<div class="card"><div class="card-head"><h2>${esc(t(check ? "rec.stock.plan" : "rec.stock.done"))}</h2>
      <span class="help muted">${esc(t(check ? "rec.stock.help" : "rec.stock.helpDone"))}</span></div><div class="card-body">${problems}${warnings}${body}</div></div>`;
  },
};

// The label of a field named in a problem
const REC_FIELD_LABEL = {
  Entrepot: "f.Entrepot", CodeArticle: "f.CodeArticle", QuantiteRecue: "f.QuantiteRecue", cLocation: "f.rec.cLocation",
  cLot: "f.rec.cLot", dExpiry: "f.rec.dExpiry", cSerial: "f.rec.cSerial",
};

Object.assign(RES, {
  gl: {
    api: "gl-accounts", route: "/gl/accounts", menu: "/gl", title: "gl.title", sub: "gl.subtitle", one: "gl.account", newTitle: "gl.newAccount",
    tabset: "gl", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${glDesc(r)}`, sort: "cCode",
    filters: [{ f: "cType", l: "f.gl.cType", options: GL_TYPES.map((k) => [k, "o.gl." + k]) }, activeFilter],
    columns: [
      { f: "cCode", l: "f.cCode" }, { f: "cDesc", l: "f.cDesc", wrap: true, fmt: (v, r) => esc(glDesc(r)) },
      { f: "cType", l: "f.gl.cType", fmt: (v) => (v ? `<span class="badge gl-${esc(v)}">${esc(t("o.gl." + v))}</span>` : "") },
      { f: "lRequiresCC", l: "f.gl.lRequiresCC", fmt: (v) => (v ? esc(t("common.yes")) : "") },
      { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    defaults: { cType: "", lActive: true },
    sections: [
      { t: "common.general", help: "gl.help", fields: [
        { f: "cCode", l: "f.cCode", req: true, key: true, help: "f.gl.cCode.help" },
        { f: "cType", l: "f.gl.cType", type: "select", options: [["", "o.gl.guess"], ...GL_TYPES.map((k) => [k, "o.gl." + k])], help: "f.gl.cType.help" },
        { f: "lActive", l: "opt.active", type: "check" },
        { f: "cDesc", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
      ] },
      { t: "gl.rules", fields: [
        { f: "lRequiresCC", l: "f.gl.lRequiresCC", type: "check", help: "f.gl.lRequiresCC.help", span: 2 },
      ] },
    ],
  },
  cc: {
    api: "cost-centers", route: "/gl/cc", menu: "/gl", title: "gl.title", sub: "gl.subtitle", one: "gl.cc", newTitle: "gl.newCc",
    tabset: "gl", id: (r) => (r.cCC2 ? r.cCC1 + "/" + r.cCC2 : r.cCC1), label: (r) => `${ccCode(r)} — ${glDesc(r)}`, sort: "cCC1",
    oneOf: (m) => (m.cCC2 ? "gl.sub" : "gl.dept"),
    filters: [activeFilter],
    // a department, then its sub-departments under it (the list comes in cCC1, cCC2 order)
    columns: [
      { f: "cCC1", l: "gl.cc", fmt: (v, r) => (r.cCC2 ? `<span class="cc-sub">↳ ${esc(ccCode(r))}</span>` : `<b>${esc(r.cCC1)}</b>`) },
      { f: "cDesc", l: "f.cDesc", wrap: true, fmt: (v, r) => (r.cCC2 ? esc(glDesc(r)) : `<b>${esc(glDesc(r))}</b>`) },
      { f: "cCC2", l: "gl.level", fmt: (v) => esc(t(v ? "gl.sub" : "gl.dept")) },
      { f: "lActive", l: "opt.active", fmt: yesNo },
    ],
    defaults: { lActive: true },
    sections: [{ t: "common.general", help: "gl.cc.help", fields: [
      { f: "cCC1", l: "f.cCC1", req: true, key: true, help: "f.cCC1.help" },
      { f: "cCC2", l: "f.cCC2", key: true, help: "f.cCC2.help" },
      { f: "lActive", l: "opt.active", type: "check" },
      { f: "cDesc", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
    ] }],
    actions: [
      { id: "addSub", l: "gl.addSub", show: (m, isNew) => !isNew && !m.cCC2,
        run: (m) => { setPrefill({ key: "cc", values: { cCC1: m.cCC1 } }); location.hash = "#/gl/cc/new"; } },
    ],
  },
  suppliers: {
    api: "suppliers", route: "/suppliers", title: "sup.title", sub: "sup.subtitle", one: "sup.one", newTitle: "sup.new",
    id: (r) => r.cCode, label: (r) => `${r.cCode} — ${r.cName}`, sort: "cName",
    filters: [{ f: "iStatutAch", l: "f.iStatutAch", options: [["1", "opt.active"], ["0", "opt.inactive"]] }],
    columns: [
      { f: "cCode", l: "f.sup.cCode" }, { f: "cName", l: "f.cName", wrap: true }, { f: "cCity", l: "f.cCity" },
      { f: "cProvince", l: "f.cProvince" }, { f: "cTermCode", l: "f.cTermCode" }, { f: "cDescAch", l: "f.cDescAch" },
      { f: "iStatutAch", l: "f.iStatutAch", fmt: (v) => `<span class="badge ${v === 1 ? "yes" : "no"}">${esc(t(v === 1 ? "opt.active" : "opt.inactive"))}</span>` },
    ],
    defaults: { cCountry: "CA", cProvince: "QC", cTermCode: "n30", cTermDesc: "net 30 jours", iTypePO: 1, iStatutAch: 1 },
    sections: [
      { t: "common.general", fields: [
        { f: "cCode", l: "f.sup.cCode", req: true, key: true },
        { f: "cName", l: "f.cName", req: true, span: 3 },
      ] },
      { t: "sup.address", fields: [
        { f: "cAddress1", l: "f.cAddress1", span: 2 }, { f: "cAddress2", l: "f.cAddress2", span: 2 },
        { f: "cCity", l: "f.cCity" }, { f: "cProvince", l: "f.cProvince" }, { f: "cCountry", l: "f.cCountry" }, { f: "cZipCode", l: "f.cZipCode" },
      ] },
      { t: "sup.terms", fields: [
        { f: "cTermCode", l: "f.cTermCode", lookup: "terms", free: true, fill: "cTermDesc" }, { f: "cTermDesc", l: "f.cTermDesc" },
        { f: "cNoTPS", l: "f.cNoTPS" }, { f: "cNoTVQ", l: "f.cNoTVQ" },
      ] },
      { t: "sup.purchasing", fields: [
        { f: "cCodeAch", l: "f.cCodeAch", lookup: "buyers", free: true, fill: "cDescAch" }, { f: "cDescAch", l: "f.cDescAch" },
        { f: "cDeptSauv", l: "f.cDeptSauv" },
        { f: "iStatutAch", l: "f.iStatutAch", type: "select", int: true, options: [["1", "opt.active"], ["0", "opt.inactive"]] },
        { f: "iTypePO", l: "f.iTypePO", type: "select", int: true, options: [["1", "opt.poType1"], ["2", "opt.poType2"], ["3", "opt.poType3"]] },
      ] },
    ],
  },
  invoices: {
    api: "invoices", route: "/invoices", title: "inv.title", sub: "inv.subtitle", one: "inv.one", newTitle: "inv.new",
    id: (r) => r.id, label: (r) => `${r.cNoFacture} — ${r.cNomFourn || r.cNoFourn}`, sort: "id", dir: "desc",
    filters: [
      { f: "cStatut", l: "f.cStatut", options: ["Draft", "Approved", "Posted", "Paid"].map((s) => [s, "status." + s]) },
      { f: "cSource", l: "f.cSource", options: [["ERP", "source.ERP"], ["SkyAI", "source.SkyAI"]] },
    ],
    columns: [
      { f: "cNoFacture", l: "f.cNoFacture" }, { f: "cNoFourn", l: "f.cNoFourn" }, { f: "cNomFourn", l: "f.cNomFourn", wrap: true },
      { f: "dDateFacture", l: "f.dDateFacture" }, { f: "cNoCommAch", l: "f.cNoCommAch" },
      { f: "dTotalFacture", l: "f.dTotalFacture", num: true, fmt: (v, r) => esc(money(v, r.cDevise)) },
      { f: "cStatut", l: "f.cStatut", fmt: statusBadge }, { f: "cSource", l: "f.cSource", fmt: sourceBadge },
    ],
    defaults: () => ({ cDevise: "CAD", cStatut: "Draft", dDateFacture: new Date().toISOString().slice(0, 10), dTransport: "0.00", dTotalTPS: "0.00", dTotalTVP: "0.00", lines: [{ dQuantite: "1" }] }),
    sections: [{ t: "common.general", fields: [
      { f: "cNoFourn", l: "f.cNoFourn", req: true, lookup: "suppliers", fill: "cNomFourn" },
      { f: "cNomFourn", l: "f.cNomFourn", readonly: true, span: 2 },
      { f: "cStatut", l: "f.cStatut", type: "select", options: ["Draft", "Approved", "Posted", "Paid"].map((s) => [s, "status." + s]) },
      { f: "cNoFacture", l: "f.cNoFacture", req: true },
      { f: "dDateFacture", l: "f.dDateFacture", req: true, type: "date" },
      { f: "cNoCommAch", l: "f.cNoCommAch", lookup: "po" },
      { f: "cDevise", l: "f.cDevise", type: "select", options: CURRENCIES.map((c) => [c, c]), raw: true },
    ] }],
    currency: (m) => m.cDevise,
    lines: {
      cols: [
        { f: "cCodeProduit", l: "f.cCodeProduit", w: "w-md" }, { f: "cDescription", l: "f.cDescription", w: "w-lg" },
        { f: "dQuantite", l: "f.dQuantite", w: "w-xs", n: true }, { f: "dCoutUnitaire", l: "f.dCoutUnitaire", w: "w-sm", n: true },
        { f: "cGL", l: "f.cGL", w: "w-sm", lookup: "gl" }, ...CC_COLS,
        { f: "iNoReception", l: "f.iNoReception", w: "w-sm" },
      ],
      amountLabel: "f.dMontant", amount: (l) => num(l.dQuantite) * num(l.dCoutUnitaire),
    },
    totals: { sub: "dSousTotal", extras: ["dTransport", "dTotalTPS", "dTotalTVP"], total: "dTotalFacture" },
  },
  po: {
    api: "purchase-orders", route: "/po", title: "po.title", sub: "po.subtitle", one: "po.one", newTitle: "po.new",
    id: (r) => r.cPO, label: (r) => `${r.cPO} — ${r.cSupplierName}`, sort: "dCreationDate", dir: "desc",
    filters: [{ f: "lUnbilled", l: "f.lUnbilled", options: [["true", "common.yes"], ["false", "common.no"]] }],
    columns: [
      { f: "cPO", l: "f.cPO" }, { f: "dCreationDate", l: "f.dCreationDate" }, { f: "cSupplierCode", l: "f.cSupplierCode" },
      { f: "cSupplierName", l: "f.cSupplierName", wrap: true }, { f: "cBuyerName", l: "f.cBuyerName" },
      { f: "lineCount", l: "common.lineCount", num: true },
      { f: "dTotalAmount", l: "f.dTotalAmount", num: true, fmt: (v) => esc(money(v)) },
      { f: "lBlanketOrder", l: "f.lBlanketOrder", fmt: yesNo }, { f: "lUnbilled", l: "f.lUnbilled", fmt: yesNo },
    ],
    defaults: () => ({ COMPANY: "MA2", dCreationDate: new Date().toISOString().slice(0, 10), lUnbilled: true, lBlanketOrder: false, dFreight: "0.00", dGST: "0.00", dPST: "0.00", lines: [{ cUnique: "1", dQuantity: "1" }] }),
    sections: [{ t: "common.general", fields: [
      { f: "cPO", l: "f.cPO", req: true, key: true },
      { f: "dCreationDate", l: "f.dCreationDate", type: "date" },
      { f: "cSupplierCode", l: "f.cSupplierCode", req: true, lookup: "suppliers", fill: "cSupplierName" },
      { f: "cSupplierName", l: "f.cSupplierName" },
      { f: "cBuyerCode", l: "f.cBuyerCode", lookup: "buyers", free: true, fill: "cBuyerName" },
      { f: "cBuyerName", l: "f.cBuyerName" },
      { f: "cApplicantCode", l: "f.cApplicantCode" },
      { f: "COMPANY", l: "f.COMPANY", readonly: true },
      { f: "lBlanketOrder", l: "f.lBlanketOrder", type: "check" },
      { f: "lUnbilled", l: "f.lUnbilled", type: "check", help: "f.lUnbilled.help" },
    ] }],
    lines: {
      cols: [
        { f: "cUnique", l: "#", w: "w-xs", raw: true }, { f: "cProductcode", l: "f.cProductcode", w: "w-md" },
        { f: "cProductDesc", l: "f.cProductDesc", w: "w-lg" }, { f: "dQuantity", l: "f.dQuantity", w: "w-xs", n: true },
        { f: "dUnitCost", l: "f.dUnitCost", w: "w-sm", n: true },
      ],
      amountLabel: "f.lineTotal", amount: (l) => num(l.dQuantity) * num(l.dUnitCost),
      newLine: (m) => ({ cUnique: String((m.lines || []).length + 1), dQuantity: "1" }),
    },
    totals: { sub: "dSubTotal", extras: ["dFreight", "dGST", "dPST"], total: "dTotalAmount" },
    tax: { supplier: "cSupplierCode", freight: "dFreight", tps: "dGST", tvq: "dPST" },
  },
  receptions: {
    api: "receptions", route: "/receptions", title: "rec.title", sub: "rec.subtitle", one: "rec.one", newTitle: "rec.new",
    id: (r) => r.NoReception, label: (r) => `${r.NoReception} — ${r.Fournisseur}`, sort: "DateReception", dir: "desc",
    filters: [
      { f: "lUnbilled", l: "f.lUnbilled", options: [["true", "common.yes"], ["false", "common.no"]] },
      { f: "lStockPosted", l: "f.lStockPosted", options: [["true", "common.yes"], ["false", "common.no"]] },
    ],
    columns: [
      { f: "NoReception", l: "f.NoReception" }, { f: "DateReception", l: "f.DateReception" }, { f: "NoBonCommande", l: "f.NoBonCommande" },
      { f: "CodeFournisseur", l: "f.CodeFournisseur" }, { f: "Fournisseur", l: "f.Fournisseur", wrap: true }, { f: "Statut", l: "f.Statut" },
      { f: "lineCount", l: "common.lineCount", num: true },
      { f: "MontantTotal", l: "f.MontantTotal", num: true, fmt: (v, r) => esc(money(v, r.Devise)) },
      { f: "lUnbilled", l: "f.lUnbilled", fmt: yesNo },
      { f: "lStockPosted", l: "f.lStockPosted", fmt: recBadge },
    ],
    locked: (m) => !!m.lStockPosted,
    badge: (m, isNew) => (isNew ? "" : recBadge(m.lStockPosted)),
    defaults: () => ({ COMPANY: "MA2", DateReception: new Date().toISOString().slice(0, 10), Statut: "Reçu", Entrepot: "ENT-01", Devise: "CAD", lUnbilled: true, Transport: "0.00", TPS: "0.00", TVQ: "0.00", lines: [] }),
    sections: [{ t: "common.general", fields: [
      { f: "NoReception", l: "f.NoReception", req: true, key: true, inputmode: "numeric" },
      { f: "DateReception", l: "f.DateReception", req: true, type: "date" },
      { f: "NoBonCommande", l: "f.NoBonCommande", req: true, lookup: "po", onPick: "fillFromPo" },
      { f: "Statut", l: "f.Statut", suggestions: ["Reçu", "En cours", "Partiellement reçu"] },
      { f: "CodeFournisseur", l: "f.CodeFournisseur", lookup: "suppliers", fill: "Fournisseur" },
      { f: "Fournisseur", l: "f.Fournisseur" },
      { f: "Entrepot", l: "f.Entrepot", lookup: "warehouses" },
      { f: "ResponsableReception", l: "f.ResponsableReception" },
      { f: "Devise", l: "f.Devise", type: "select", options: CURRENCIES.map((c) => [c, c]), raw: true },
      { f: "lUnbilled", l: "f.lUnbilled", type: "check", help: "f.lUnbilled.help" },
      { f: "Commentaires", l: "f.Commentaires", type: "textarea", span: 4 },
      { f: "dStockPosted", l: "f.dStockPosted", readonly: true, show: (m) => !!m.lStockPosted },
      { f: "cStockPostedBy", l: "f.cStockPostedBy", readonly: true, show: (m) => !!m.lStockPosted },
    ] }],
    currency: (m) => m.Devise,
    actions: [
      { id: "check", l: "rec.check", show: (m, isNew) => !isNew && !m.lStockPosted, run: (m, ctx) => recSaveThen(m, ctx, "check") },
      { id: "post", l: "rec.post", perm: "post", show: (m, isNew) => !isNew && !m.lStockPosted, confirm: "rec.post.confirm", done: "rec.post.done",
        run: (m, ctx) => recSaveThen(m, ctx, "post") },
    ],
    panels: [recStock],
    lines: {
      help: "rec.lines.help", minWidth: 1900,
      cols: [
        { f: "CodeArticle", l: "f.CodeArticle", w: "w-md" }, { f: "Description", l: "f.Description", w: "w-md" },
        { f: "QuantiteCommandee", l: "f.QuantiteCommandee", w: "w-xs", n: true }, { f: "QuantiteRecue", l: "f.QuantiteRecue", w: "w-xs", n: true },
        { f: "PrixUnitaire", l: "f.PrixUnitaire", w: "w-sm", n: true },
        { f: "cSupplierLot", l: "f.rec.cSupplierLot", w: "w-md" }, { f: "cLot", l: "f.rec.cLot", w: "w-md", ph: "rec.auto" },
        { f: "dExpiry", l: "f.rec.dExpiry", w: "w-md", type: "date" },
        { f: "cLocation", l: "f.rec.cLocation", w: "w-md", lookup: "locations", lookupParams: (m) => ({ wh: m.Entrepot }) },
        { f: "cSerial", l: "f.rec.cSerial", w: "w-md" },
        { f: "cGL", l: "f.cGL", w: "w-sm", lookup: "gl" }, ...CC_COLS,
      ],
      amountLabel: "f.Montant", amount: (l) => num(l.QuantiteRecue) * num(l.PrixUnitaire),
    },
    totals: { sub: "SousTotal", extras: ["Transport", "TPS", "TVQ"], total: "MontantTotal" },
    tax: { supplier: "CodeFournisseur", freight: "Transport", tps: "TPS", tvq: "TVQ" },
  },
});

RES.users = {
  api: "users", route: "/admin/users", admin: true, title: "usr.title", sub: "usr.subtitle", one: "usr.one", newTitle: "usr.new",
  id: (r) => r.id, label: (r) => `${r.username} — ${r.name}`, sort: "username",
  filters: [
    { f: "role", l: "f.role", lookup: "roles" },
    { f: "active", l: "f.active", options: [["true", "opt.active"], ["false", "opt.inactive"]] },
  ],
  columns: [
    { f: "username", l: "f.username" }, { f: "name", l: "f.userName", wrap: true }, { f: "email", l: "f.email" },
    { f: "role", l: "f.role", fmt: (v) => esc(roleName(v)) },
    { f: "lang", l: "f.lang", fmt: (v) => esc(String(v || "").toUpperCase()) },
    { f: "active", l: "f.active", fmt: (v) => `<span class="badge ${v ? "yes" : "no"}">${esc(t(v ? "opt.active" : "opt.inactive"))}</span>` },
    { f: "last_login", l: "f.lastLogin", fmt: (v) => esc(fmtDateTime(v)) },
    { f: "locked", l: "usr.locked", fmt: (v, r) => (v ? `<span class="badge no" title="${esc(t("usr.lockedUntil", { d: fmtDateTime(r.locked_until) }))}">${esc(t("usr.lockedBadge"))}</span>` : "") },
  ],
  // locked after too many failed sign-ins (the server refuses it for a while): the administrator lets the user in
  actions: [
    { id: "unlock", l: "usr.unlock", primary: true, show: (m, isNew) => !isNew && m.locked, done: "usr.unlocked",
      run: (m, ctx) => api(ctx.path + "/unlock", { method: "POST", body: {} }) },
  ],
  panels: [{ html: (m) => (m.locked ? `<div class="alert warn">${esc(t("usr.lockedNotice", { d: fmtDateTime(m.locked_until) }))}</div>` : "") }],
  defaults: () => ({ role: "USER", lang, active: true }),
  sections: [
    { t: "common.general", fields: [
      { f: "username", l: "f.username", req: true, key: true, autocomplete: "off" },
      { f: "name", l: "f.userName", req: true, span: 2 },
      { f: "email", l: "f.email", type: "email" },
      { f: "role", l: "f.role", req: true, lookup: "roles" },
      { f: "lang", l: "f.lang", type: "select", options: [["en", "English"], ["fr", "Français"]], raw: true },
      { f: "active", l: "opt.active", type: "check" },
    ] },
    { t: "usr.passwordSection", fields: [
      { f: "password", l: "f.password", type: "password", reqNew: true, help: "usr.passwordHelp" },
    ] },
  ],
};
