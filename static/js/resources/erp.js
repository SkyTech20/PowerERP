/* PowerERP: General ledger, suppliers, purchasing, invoices and users: list / form definitions. */
import { CURRENCIES, api, esc, fmtDateTime, lang, money, num, sourceBadge, statusBadge, t, yesNo } from "../core.js";
import { RES } from "../registry.js";
import { route } from "../router.js";

Object.assign(RES, {
  gl: {
    api: "gl-accounts", route: "/gl/accounts", menu: "/gl", title: "gl.title", sub: "gl.subtitle", one: "gl.account", newTitle: "gl.newAccount",
    tabset: "gl", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${r.cDesc}`, sort: "cCode",
    columns: [{ f: "cCode", l: "f.cCode" }, { f: "cDesc", l: "f.cDesc", wrap: true }],
    sections: [{ t: "common.general", fields: [
      { f: "cCode", l: "f.cCode", req: true, key: true },
      { f: "cDesc", l: "f.cDesc", req: true, span: 3 },
    ] }],
  },
  cc: {
    api: "cost-centers", route: "/gl/cc", menu: "/gl", title: "gl.title", sub: "gl.subtitle", one: "gl.cc", newTitle: "gl.newCc",
    tabset: "gl", id: (r) => (r.cCC2 ? r.cCC1 + "/" + r.cCC2 : r.cCC1), label: (r) => `${r.cCC1}${r.cCC2 ? "-" + r.cCC2 : ""} — ${r.cDesc}`, sort: "cCC1",
    columns: [{ f: "cCC1", l: "f.cCC1" }, { f: "cCC2", l: "f.cCC2" }, { f: "cDesc", l: "f.cDesc", wrap: true }],
    sections: [{ t: "common.general", fields: [
      { f: "cCC1", l: "f.cCC1", req: true, key: true },
      { f: "cCC2", l: "f.cCC2", key: true },
      { f: "cDesc", l: "f.cDesc", req: true, span: 2 },
    ] }],
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
    defaults: { cCountry: "CA", cProvince: "qc", cTermCode: "n30", cTermDesc: "net 30 jours", iTypePO: 1, iStatutAch: 1 },
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
        { f: "cTermCode", l: "f.cTermCode", lookup: "terms", fill: "cTermDesc" }, { f: "cTermDesc", l: "f.cTermDesc" },
        { f: "cNoTPS", l: "f.cNoTPS" }, { f: "cNoTVQ", l: "f.cNoTVQ" },
      ] },
      { t: "sup.purchasing", fields: [
        { f: "cCodeAch", l: "f.cCodeAch", lookup: "buyers", fill: "cDescAch" }, { f: "cDescAch", l: "f.cDescAch" },
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
        { f: "cGL", l: "f.cGL", w: "w-sm", lookup: "gl" }, { f: "cCC1", l: "f.lCC1", w: "w-xs" }, { f: "cCC2", l: "f.lCC2", w: "w-xs" },
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
      { f: "cBuyerCode", l: "f.cBuyerCode", lookup: "buyers", fill: "cBuyerName" },
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
    filters: [{ f: "lUnbilled", l: "f.lUnbilled", options: [["true", "common.yes"], ["false", "common.no"]] }],
    columns: [
      { f: "NoReception", l: "f.NoReception" }, { f: "DateReception", l: "f.DateReception" }, { f: "NoBonCommande", l: "f.NoBonCommande" },
      { f: "CodeFournisseur", l: "f.CodeFournisseur" }, { f: "Fournisseur", l: "f.Fournisseur", wrap: true }, { f: "Statut", l: "f.Statut" },
      { f: "lineCount", l: "common.lineCount", num: true },
      { f: "MontantTotal", l: "f.MontantTotal", num: true, fmt: (v, r) => esc(money(v, r.Devise)) },
      { f: "lUnbilled", l: "f.lUnbilled", fmt: yesNo },
    ],
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
    ] }],
    currency: (m) => m.Devise,
    lines: {
      cols: [
        { f: "CodeArticle", l: "f.CodeArticle", w: "w-md" }, { f: "Description", l: "f.Description", w: "w-lg" },
        { f: "QuantiteCommandee", l: "f.QuantiteCommandee", w: "w-xs", n: true }, { f: "QuantiteRecue", l: "f.QuantiteRecue", w: "w-xs", n: true },
        { f: "PrixUnitaire", l: "f.PrixUnitaire", w: "w-sm", n: true },
        { f: "cGL", l: "f.cGL", w: "w-sm", lookup: "gl" }, { f: "cCC1", l: "f.lCC1", w: "w-xs" }, { f: "cCC2", l: "f.lCC2", w: "w-xs" },
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
    { f: "role", l: "f.role", options: [["admin", "role.admin"], ["user", "role.user"]] },
    { f: "active", l: "f.active", options: [["true", "opt.active"], ["false", "opt.inactive"]] },
  ],
  columns: [
    { f: "username", l: "f.username" }, { f: "name", l: "f.userName", wrap: true }, { f: "email", l: "f.email" },
    { f: "role", l: "f.role", fmt: (v) => esc(t("role." + v)) },
    { f: "lang", l: "f.lang", fmt: (v) => esc(String(v || "").toUpperCase()) },
    { f: "active", l: "f.active", fmt: (v) => `<span class="badge ${v ? "yes" : "no"}">${esc(t(v ? "opt.active" : "opt.inactive"))}</span>` },
    { f: "last_login", l: "f.lastLogin", fmt: (v) => esc(fmtDateTime(v)) },
  ],
  defaults: () => ({ role: "user", lang, active: true }),
  sections: [
    { t: "common.general", fields: [
      { f: "username", l: "f.username", req: true, key: true, autocomplete: "off" },
      { f: "name", l: "f.userName", req: true, span: 2 },
      { f: "email", l: "f.email", type: "email" },
      { f: "role", l: "f.role", type: "select", options: [["user", "role.user"], ["admin", "role.admin"]] },
      { f: "lang", l: "f.lang", type: "select", options: [["en", "English"], ["fr", "Français"]], raw: true },
      { f: "active", l: "opt.active", type: "check" },
    ] },
    { t: "usr.passwordSection", fields: [
      { f: "password", l: "f.password", type: "password", reqNew: true, help: "usr.passwordHelp" },
    ] },
  ],
};
