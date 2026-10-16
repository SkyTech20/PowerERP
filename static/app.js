/* Mini ERP sample — single page app (no build step, no external dependencies). */
(function () {
  "use strict";

  const API = "api/";  // relative: works at / and behind a prefix such as /erp/
  const I18N = window.ERP_I18N;
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  // ------------------------------------------------------------------ i18n
  let lang = "en";
  try {
    lang = localStorage.getItem("erp.lang") || ((navigator.language || "").toLowerCase().startsWith("fr") ? "fr" : "en");
  } catch (e) { /* storage unavailable */ }
  if (!I18N[lang]) lang = "en";

  function t(key, vars) {
    let s = (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
    if (vars) Object.keys(vars).forEach((k) => { s = s.replace("{" + k + "}", vars[k]); });
    return s;
  }

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  const num = (v) => { const n = parseFloat(String(v == null ? "" : v).replace(",", ".")); return isNaN(n) ? 0 : n; };
  function money(v, cur) {
    try {
      return new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { style: "currency", currency: cur || "CAD" }).format(num(v));
    } catch (e) { return num(v).toFixed(2) + " " + (cur || ""); }
  }
  // Quebec sales taxes, charged when the supplier has the matching registration number.
  const TAX_RATES = { tps: 0.05, tvq: 0.09975 };
  const round2 = (v) => Math.round((v + Number.EPSILON) * 100) / 100;
  const fmtInt = (v) => new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA").format(v || 0);

  // ------------------------------------------------------------------ API
  async function api(path, opts) {
    opts = opts || {};
    const res = await fetch(API + path, {
      method: opts.method || "GET",
      headers: opts.body ? { "Content-Type": "application/json" } : {},
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    let data = null;
    try { data = await res.json(); } catch (e) { /* empty body */ }
    if (res.status === 401 && !opts.noAuthRedirect) showLogin();
    if (!res.ok) {
      const err = new Error((data && data.error) || "generic");
      err.code = (data && data.error) || "generic";
      err.field = data && data.field;
      err.status = res.status;
      throw err;
    }
    return data;
  }

  function toast(msg, kind) {
    const el = document.createElement("div");
    el.className = "toast " + (kind || "");
    el.textContent = msg;
    $("#toasts").appendChild(el);
    setTimeout(() => el.remove(), 3200);
  }

  // ------------------------------------------------------------------ Menu
  // Items given as plain strings are visible but disabled.
  const MENU = [
    { k: "dashboard", icon: "🏠", route: "/" },
    { sep: true },
    { k: "gl", icon: "📒", items: [{ k: "gl.accounts", route: "/gl" }, "gl.journal", "gl.periods", "gl.statements", "gl.budgets", "gl.bankrec"] },
    { k: "ap", icon: "💳", items: [{ k: "ap.suppliers", route: "/suppliers" }, { k: "ap.invoices", route: "/invoices" }, "ap.payments", "ap.chequeRun", "ap.recurring", "ap.aging"] },
    { k: "pur", icon: "🛒", items: [{ k: "pur.po", route: "/po" }, { k: "pur.receptions", route: "/receptions" }, { k: "pur.selection", route: "/selection" }, "pur.requisitions", "pur.returns", "pur.pricelists"] },
    { k: "ar", icon: "💰", items: ["ar.customers", "ar.invoices", "ar.receipts", "ar.credits", "ar.collections"] },
    { k: "sales", icon: "📈", items: ["sales.quotes", "sales.orders", "sales.shipping", "sales.pricing", "sales.commissions"] },
    { k: "inv", icon: "📦", items: ["inv.items", "inv.warehouses", "inv.movements", "inv.count", "inv.lots"] },
    { k: "prod", icon: "🏭", items: ["prod.bom", "prod.workorders", "prod.routings", "prod.mrp", "prod.shopfloor"] },
    { k: "hr", icon: "👥", items: ["hr.employees", "hr.timesheets", "hr.payroll", "hr.benefits"] },
    { k: "fa", icon: "🏢", items: ["fa.assets", "fa.depreciation"] },
    { k: "proj", icon: "📁", items: ["proj.projects", "proj.jobcost"] },
    { k: "crm", icon: "🤝", items: ["crm.contacts", "crm.opportunities"] },
    { k: "rep", icon: "📊", items: ["rep.designer", "rep.bi"] },
    { k: "admin", icon: "⚙️", items: ["admin.companies", { k: "admin.users", route: "/admin/users", admin: true }, "admin.taxes", "admin.currencies", "admin.settings"] },
  ];
  const openGroups = new Set(["gl", "ap", "pur"]);
  let user = null; // logged-in user (GET api/auth/me)
  const isAdmin = () => !!user && user.role === "admin";
  // Menu items flagged admin: true are links for administrators only.
  const usable = (i) => typeof i === "object" && (!i.admin || isAdmin());

  function renderSidebar() {
    const path = currentPath();
    const isActive = (route) => (route === "/" ? path === "/" : path === route || path.startsWith(route + "/"));
    const html = MENU.map((m) => {
      if (m.sep) return '<div class="nav-sep"></div>';
      if (m.route) {
        return `<a class="nav-link ${isActive(m.route) ? "active" : ""}" href="#${m.route}"><span class="nav-icon">${m.icon}</span>${esc(t("menu." + m.k))}</a>`;
      }
      const enabled = m.items.some(usable);
      const sub = m.items.map((i) => {
        if (usable(i)) {
          return `<a class="nav-link ${isActive(i.route) ? "active" : ""}" href="#${i.route}">${esc(t("menu." + i.k))}</a>`;
        }
        const k = typeof i === "object" ? i.k : i;
        return `<span class="nav-link disabled" aria-disabled="true" title="${esc(t("app.menuUnavailable"))}">${esc(t("menu." + k))}<span class="lock">🔒</span></span>`;
      }).join("");
      return `<details class="nav-group ${enabled ? "" : "dimmed"}" data-group="${m.k}" ${openGroups.has(m.k) ? "open" : ""}>
        <summary><span class="nav-icon">${m.icon}</span>${esc(t("menu." + m.k))}<span class="chev">▶</span></summary>
        <div class="nav-sub">${sub}</div></details>`;
    }).join("");
    const nav = $("#sidebar");
    nav.innerHTML = html;
    $$("details.nav-group", nav).forEach((d) => d.addEventListener("toggle", () => {
      if (d.open) openGroups.add(d.dataset.group); else openGroups.delete(d.dataset.group);
    }));
    $$(".nav-link.disabled", nav).forEach((el) => el.addEventListener("click", () => toast(t("app.unavailable"))));
    $$("a.nav-link", nav).forEach((el) => el.addEventListener("click", () => document.body.classList.remove("nav-open")));
  }

  function applyStaticI18n() {
    document.documentElement.lang = lang;
    $$("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    $$(".lang-switch button").forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
  }

  // ------------------------------------------------------------------ Resources
  const yesNo = (v) => `<span class="badge ${v ? "yes" : "no"}">${esc(t(v ? "common.yes" : "common.no"))}</span>`;
  const statusBadge = (v) => `<span class="badge ${esc(v)}">${esc(t("status." + v))}</span>`;
  const sourceBadge = (v) => `<span class="badge ${esc(v)}">${esc(t("source." + v))}</span>`;
  const enc = encodeURIComponent;

  const CURRENCIES = ["CAD", "USD", "EUR"];

  const RES = {
    gl: {
      api: "gl-accounts", route: "/gl/accounts", menu: "/gl", title: "gl.title", sub: "gl.subtitle", one: "gl.account", newTitle: "gl.newAccount",
      tabs: "accounts", id: (r) => r.cCode, label: (r) => `${r.cCode} — ${r.cDesc}`, sort: "cCode",
      columns: [{ f: "cCode", l: "f.cCode" }, { f: "cDesc", l: "f.cDesc", wrap: true }],
      sections: [{ t: "common.general", fields: [
        { f: "cCode", l: "f.cCode", req: true, key: true },
        { f: "cDesc", l: "f.cDesc", req: true, span: 3 },
      ] }],
    },
    cc: {
      api: "cost-centers", route: "/gl/cc", menu: "/gl", title: "gl.title", sub: "gl.subtitle", one: "gl.cc", newTitle: "gl.newCc",
      tabs: "cc", id: (r) => (r.cCC2 ? r.cCC1 + "/" + r.cCC2 : r.cCC1), label: (r) => `${r.cCC1}${r.cCC2 ? "-" + r.cCC2 : ""} — ${r.cDesc}`, sort: "cCC1",
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
        { f: "Entrepot", l: "f.Entrepot", suggestions: ["ENT-01", "ENT-02"] },
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
  };

  RES.users = {
    api: "users", route: "/admin/users", title: "usr.title", sub: "usr.subtitle", one: "usr.one", newTitle: "usr.new",
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

  function fmtDateTime(v) {
    if (!v) return "—";
    const d = new Date(v);
    if (isNaN(d)) return v;
    return d.toLocaleString(lang === "fr" ? "fr-CA" : "en-CA", { dateStyle: "short", timeStyle: "short" });
  }

  // ------------------------------------------------------------------ Lookups
  const lookupCache = {};
  let uid = 0;
  function bindLookup(input, kind, onPick) {
    const listId = "dl-" + (++uid);
    const dl = document.createElement("datalist");
    dl.id = listId;
    input.setAttribute("list", listId);
    input.setAttribute("autocomplete", "off");
    input.after(dl);
    let timer = null;
    const load = () => {
      const q = input.value.trim();
      api("lookups/" + kind + "?q=" + enc(q)).then((rows) => {
        lookupCache[kind] = lookupCache[kind] || {};
        rows.forEach((r) => { lookupCache[kind][r.code.toUpperCase()] = r.label; });
        dl.innerHTML = rows.map((r) => `<option value="${esc(r.code)}">${esc(r.label)}</option>`).join("");
      }).catch(() => {});
    };
    input.addEventListener("focus", load, { once: true });
    input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(load, 180); });
    input.addEventListener("change", () => {
      const label = (lookupCache[kind] || {})[input.value.trim().toUpperCase()];
      if (onPick) onPick(input.value.trim(), label);
    });
  }

  // ------------------------------------------------------------------ Views
  const listState = {};
  let view = null;

  function pageHead(title, sub, actions, crumbs) {
    return `<div class="page-head"><div>${crumbs ? `<div class="crumbs">${crumbs}</div>` : ""}<h1>${esc(title)}</h1>${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</div>
      <div class="actions">${actions || ""}</div></div>`;
  }

  function glTabs(active) {
    return `<div class="tabs"><a href="#/gl/accounts" class="${active === "accounts" ? "active" : ""}">${esc(t("gl.tab.accounts"))}</a>
      <a href="#/gl/cc" class="${active === "cc" ? "active" : ""}">${esc(t("gl.tab.cc"))}</a></div>`;
  }

  // ---------- Dashboard
  function dashboardView() {
    let data = null;
    return {
      async load() { data = await api("summary"); },
      render() {
        const kpi = (route, label, value, meta) => `<a class="card kpi" href="#${route}"><div class="label">${esc(label)}</div><div class="value">${value}</div><div class="meta">${esc(meta)}</div></a>`;
        const recent = data.recentInvoices.length
          ? `<div class="table-wrap"><table class="grid"><thead><tr><th>${esc(t("f.cNoFacture"))}</th><th>${esc(t("f.cNomFourn"))}</th><th>${esc(t("f.dDateFacture"))}</th><th class="num">${esc(t("f.dTotalFacture"))}</th><th>${esc(t("f.cStatut"))}</th></tr></thead><tbody>
            ${data.recentInvoices.map((i) => `<tr class="clickable" data-href="#/invoices/${i.id}"><td>${esc(i.cNoFacture)}</td><td>${esc(i.cNomFourn || i.cNoFourn)}</td><td>${esc(i.dDateFacture)}</td><td class="num">${esc(money(i.dTotalFacture, i.cDevise))}</td><td>${statusBadge(i.cStatut)} ${i.cSource === "SkyAI" ? sourceBadge(i.cSource) : ""}</td></tr>`).join("")}
            </tbody></table></div>`
          : `<div class="empty">${esc(t("common.empty"))}</div>`;
        $("#view").innerHTML = pageHead(t("dash.title"), t("dash.subtitle"), `<button class="btn danger" id="clearBtn">🗑 ${esc(t("dash.clear"))}</button><button class="btn" id="resetBtn">↺ ${esc(t("dash.reset"))}</button>`) + `
          <div class="kpis">
            ${kpi("/suppliers", t("dash.suppliers"), fmtInt(data.suppliers), t("dash.activeSuppliers", { n: fmtInt(data.activeSuppliers) }))}
            ${kpi("/gl/accounts", t("dash.gl"), fmtInt(data.glAccounts), t("dash.cc", { n: fmtInt(data.costCenters) }))}
            ${kpi("/po", t("dash.po"), fmtInt(data.purchaseOrders), t("dash.unbilledPo", { n: data.unbilledPOs }))}
            ${kpi("/receptions", t("dash.receptions"), fmtInt(data.receptions), t("dash.unbilledRec", { n: data.unbilledReceptions }))}
            ${kpi("/invoices", t("dash.invoices"), fmtInt(data.openInvoices), money(data.openInvoicesAmount) + " · " + t("dash.invoicesTotal", { n: data.invoices }))}
          </div>
          <div class="card"><div class="card-head"><h2>${esc(t("dash.recent"))}</h2><a class="btn small" style="margin-left:auto" href="#/invoices">${esc(t("menu.ap.invoices"))} →</a></div>${recent}</div>`;
        $$("tr[data-href]").forEach((tr) => tr.addEventListener("click", () => { location.hash = tr.dataset.href; }));
        $("#clearBtn").addEventListener("click", async () => {
          if (!confirm(t("dash.clearConfirm"))) return;
          await api("clear", { method: "POST" });
          toast(t("dash.clearDone"), "success");
          await this.load();
          this.render();
        });
        $("#resetBtn").addEventListener("click", async () => {
          if (!confirm(t("dash.resetConfirm"))) return;
          await api("reset", { method: "POST" });
          toast(t("dash.resetDone"), "success");
          await this.load();
          this.render();
        });
      },
    };
  }

  // ---------- Generic list
  function listView(key) {
    const R = RES[key];
    const st = listState[key] = listState[key] || { q: "", page: 1, size: 25, sort: R.sort, dir: R.dir || "asc", filters: {} };
    let data = null;
    return {
      async load() {
        const params = new URLSearchParams({ q: st.q, page: st.page, size: st.size, sort: st.sort || "", dir: st.dir });
        Object.entries(st.filters).forEach(([k, v]) => { if (v !== "") params.set("f_" + k, v); });
        data = await api(R.api + "?" + params.toString());
      },
      render() {
        const pages = Math.max(1, Math.ceil(data.total / data.size));
        const head = R.columns.map((c) => {
          const arrow = st.sort === c.f ? `<span class="arrow">${st.dir === "desc" ? "▼" : "▲"}</span>` : "";
          return `<th class="sortable ${c.num ? "num" : ""}" data-sort="${c.f}">${esc(t(c.l))}${arrow}</th>`;
        }).join("");
        const rows = data.items.map((r) => `<tr class="clickable" data-id="${esc(R.id(r))}">${R.columns.map((c) => {
          const v = r[c.f];
          const cell = c.fmt ? c.fmt(v, r) : esc(v);
          return `<td class="${c.num ? "num" : ""} ${c.wrap ? "wrap" : ""}">${cell}</td>`;
        }).join("")}</tr>`).join("");
        const filters = (R.filters || []).map((f) => `<select data-filter="${f.f}" aria-label="${esc(t(f.l))}" style="width:auto">
            <option value="">${esc(t(f.l))}: ${esc(t("common.all"))}</option>
            ${f.options.map(([v, l]) => `<option value="${esc(v)}" ${st.filters[f.f] === v ? "selected" : ""}>${esc(t(l))}</option>`).join("")}
          </select>`).join("");
        $("#view").innerHTML = pageHead(t(R.title), t(R.sub), `<a class="btn primary" href="#${R.route}/new">＋ ${esc(t("common.new"))}</a>`)
          + (R.tabs ? glTabs(R.tabs) : "")
          + `<div class="card"><div class="toolbar"><input type="search" id="q" placeholder="${esc(t("common.search"))}" value="${esc(st.q)}">${filters}
              <span class="count">${esc(t("common.records", { n: fmtInt(data.total) }))}</span></div>
            <div class="table-wrap">${data.items.length ? `<table class="grid"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>` : `<div class="empty">${esc(t("common.empty"))}</div>`}</div>
            <div class="pager"><span>${esc(t("common.page", { p: data.page, n: pages }))}</span>
              <button class="btn small" id="prev" ${data.page <= 1 ? "disabled" : ""}>‹ ${esc(t("common.prev"))}</button>
              <button class="btn small" id="next" ${data.page >= pages ? "disabled" : ""}>${esc(t("common.next"))} ›</button></div></div>`;

        const reload = async () => { await this.load(); this.render(); };
        let timer = null;
        const q = $("#q");
        q.addEventListener("input", () => {
          clearTimeout(timer);
          timer = setTimeout(async () => {
            st.q = q.value; st.page = 1;
            await reload();
            const nq = $("#q"); nq.focus(); nq.setSelectionRange(nq.value.length, nq.value.length);
          }, 250);
        });
        $$("select[data-filter]").forEach((s) => s.addEventListener("change", () => { st.filters[s.dataset.filter] = s.value; st.page = 1; reload(); }));
        $$("th[data-sort]").forEach((th) => th.addEventListener("click", () => {
          const f = th.dataset.sort;
          if (st.sort === f) st.dir = st.dir === "asc" ? "desc" : "asc"; else { st.sort = f; st.dir = "asc"; }
          reload();
        }));
        $$("tr[data-id]").forEach((tr) => tr.addEventListener("click", () => { location.hash = "#" + R.route + "/" + tr.dataset.id.split("/").map(enc).join("/"); }));
        $("#prev").addEventListener("click", () => { st.page--; reload(); });
        $("#next").addEventListener("click", () => { st.page++; reload(); });
      },
    };
  }

  // ---------- Generic form
  function formView(key, id) {
    const R = RES[key];
    const isNew = id == null;
    let model = null;
    let errors = {};
    let missing = false;
    let taxInfo = null; // { code, tps, tvq } of the supplier, when R.tax
    let taxLive = isNew; // existing records keep their stored taxes until something is changed

    const cur = () => (R.currency ? R.currency(model) : "CAD");

    // Load the supplier's TPS / TVQ numbers and recompute the taxes.
    async function loadSupplierTax(code) {
      code = String(code || "").trim();
      if (!R.tax || (taxInfo && taxInfo.code === code)) return;
      taxInfo = { code, tps: false, tvq: false };
      if (code) {
        try {
          const sup = await api("suppliers/" + enc(code));
          taxInfo = { code, tps: !!String(sup.cNoTPS || "").trim(), tvq: !!String(sup.cNoTVQ || "").trim() };
        } catch (e) { /* unknown supplier: no taxes */ }
      }
      if ($("#totals")) refreshAmounts();
    }

    function applyTaxes() {
      if (!R.tax || !taxInfo || !taxLive) return;
      const base = (model.lines || []).reduce((s, l) => s + R.lines.amount(l), 0) + num(model[R.tax.freight]);
      model[R.tax.tps] = (taxInfo.tps ? round2(base * TAX_RATES.tps) : 0).toFixed(2);
      model[R.tax.tvq] = (taxInfo.tvq ? round2(base * TAX_RATES.tvq) : 0).toFixed(2);
    }

    function fieldHtml(fd) {
      const v = model[fd.f];
      const ro = fd.readonly || (fd.key && !isNew);
      const required = fd.req || (fd.reqNew && isNew);
      const label = `<label for="f-${fd.f}">${esc(t(fd.l))}${required ? '<span class="req">*</span>' : ""}</label>`;
      const err = errors[fd.f] ? `<span class="err">${esc(t("err." + errors[fd.f]))}</span>` : "";
      const help = fd.help ? `<span class="help">${esc(t(fd.help))}</span>` : "";
      const cls = `field ${fd.span === 4 ? "span-4" : fd.span >= 2 ? "span-2" : ""} ${errors[fd.f] ? "invalid" : ""}`;
      if (fd.type === "check") {
        return `<div class="${cls}"><label class="check"><input type="checkbox" id="f-${fd.f}" data-f="${fd.f}" ${v ? "checked" : ""}> ${esc(t(fd.l))}</label>${help}</div>`;
      }
      let input;
      if (fd.type === "select") {
        input = `<select id="f-${fd.f}" data-f="${fd.f}">${fd.options.map(([ov, ol]) => `<option value="${esc(ov)}" ${String(v) === ov ? "selected" : ""}>${esc(fd.raw ? ol : t(ol))}</option>`).join("")}</select>`;
      } else if (fd.type === "textarea") {
        input = `<textarea id="f-${fd.f}" data-f="${fd.f}">${esc(v)}</textarea>`;
      } else {
        const list = fd.suggestions ? `list="sg-${fd.f}"` : "";
        const sg = fd.suggestions ? `<datalist id="sg-${fd.f}">${fd.suggestions.map((s) => `<option value="${esc(s)}">`).join("")}</datalist>` : "";
        const type = ["date", "password", "email"].includes(fd.type) ? fd.type : "text";
        const auto = fd.type === "password" ? 'autocomplete="new-password"' : fd.autocomplete ? `autocomplete="${fd.autocomplete}"` : "";
        input = `<input type="${type}" id="f-${fd.f}" data-f="${fd.f}" value="${esc(v)}" ${ro ? "readonly" : ""} ${list} ${auto} ${fd.inputmode ? `inputmode="${fd.inputmode}"` : ""}>${sg}`;
      }
      return `<div class="${cls}">${label}${input}${help}${err}</div>`;
    }

    function linesHtml() {
      const L = R.lines;
      const head = L.cols.map((c) => `<th class="${c.n ? "num" : ""}">${esc(c.raw ? c.l : t(c.l))}</th>`).join("") + `<th class="num">${esc(t(L.amountLabel))}</th><th></th>`;
      const body = (model.lines || []).map((ln, i) => `<tr data-line="${i}">${L.cols.map((c) =>
        `<td class="${c.w}"><input type="text" data-lf="${c.f}" value="${esc(ln[c.f])}" ${c.n ? 'inputmode="decimal" style="text-align:right"' : ""} ${c.lookup ? `data-lookup="${c.lookup}"` : ""} aria-label="${esc(c.raw ? c.l : t(c.l))}"></td>`).join("")}
        <td class="num" data-amount>${esc(money(L.amount(ln), cur()))}</td>
        <td><button type="button" class="link-btn" data-remove="${i}" title="${esc(t("common.removeLine"))}">✕</button></td></tr>`).join("");
      return `<div class="card"><div class="card-head"><h2>${esc(t("common.lines"))}</h2><button type="button" class="btn small" id="addLine" style="margin-left:auto">＋ ${esc(t("common.addLine"))}</button></div>
        <div class="table-wrap"><table class="grid lines"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>
        <div class="totals" id="totals"></div></div>`;
    }

    function totalsHtml() {
      const T = R.totals;
      applyTaxes();
      const isTax = (f) => R.tax && (f === R.tax.tps || f === R.tax.tvq);
      const sub = (model.lines || []).reduce((s, l) => s + R.lines.amount(l), 0);
      const total = sub + T.extras.reduce((s, f) => s + num(model[f]), 0);
      return `<table><tr><td>${esc(t("f." + T.sub))}</td><td>${esc(money(sub, cur()))}</td></tr>
        ${T.extras.map((f) => `<tr><td><label for="t-${f}">${esc(t("f." + f))}</label></td><td><input type="text" id="t-${f}" data-f="${f}" inputmode="decimal" value="${esc(model[f])}" ${isTax(f) ? "readonly" : ""}></td></tr>`).join("")}
        <tr class="grand"><td>${esc(t("f." + T.total))}</td><td>${esc(money(total, cur()))}</td></tr></table>
        ${R.tax ? `<p class="help tax-note">${esc(t("common.taxAuto"))}</p>` : ""}`;
    }

    function refreshAmounts() {
      if (!R.lines) return;
      $$("tr[data-line]").forEach((tr) => {
        const ln = model.lines[+tr.dataset.line];
        $("[data-amount]", tr).textContent = money(R.lines.amount(ln), cur());
      });
      const totals = $("#totals");
      const focused = document.activeElement && document.activeElement.id;
      const caret = focused && document.activeElement.selectionStart;
      totals.innerHTML = totalsHtml();
      bindTotals();
      if (focused && focused.startsWith("t-")) { const el = $("#" + focused); el.focus(); try { el.setSelectionRange(caret, caret); } catch (e) { /* ignore */ } }
    }

    function bindTotals() {
      $$("#totals input[data-f]").forEach((el) => el.addEventListener("input", () => { model[el.dataset.f] = el.value; taxLive = true; refreshAmounts(); }));
    }

    async function fillFromPo(po) {
      if (!po) return;
      try {
        const p = await api("purchase-orders/" + enc(po));
        if (!model.CodeFournisseur) { model.CodeFournisseur = p.cSupplierCode; model.Fournisseur = p.cSupplierName; }
        if (!(model.lines || []).some((l) => l.CodeArticle || l.Description)) {
          model.lines = p.lines.map((l) => ({ CodeArticle: l.cProductcode, Description: l.cProductDesc, QuantiteCommandee: l.dQuantity, QuantiteRecue: l.dQuantity, PrixUnitaire: l.dUnitCost }));
        }
        taxLive = true;
        render();
        if (R.tax) loadSupplierTax(model[R.tax.supplier]);
      } catch (e) { /* unknown PO: leave the form as typed */ }
    }

    function render() {
      if (missing) {
        $("#view").innerHTML = pageHead(t(R.one), "", `<a class="btn" href="#${R.route}">← ${esc(t("common.back"))}</a>`) + `<div class="card"><div class="empty">${esc(t("common.notFound"))}</div></div>`;
        return;
      }
      const title = isNew ? t(R.newTitle) : `${t(R.one)} ${R.label(model)}`;
      const crumbs = `<a href="#${R.route}">${esc(t(R.title))}</a>${R.tabs ? " / " + esc(t("gl.tab." + R.tabs)) : ""}`;
      const actions = `<a class="btn" href="#${R.route}">${esc(t("common.cancel"))}</a>
        ${isNew ? "" : `<button class="btn danger" id="deleteBtn">${esc(t("common.delete"))}</button>`}
        <button class="btn primary" id="saveBtn">${esc(t("common.save"))}</button>`;
      const sections = R.sections.map((s) => `<div class="card"><div class="card-head"><h2>${esc(t(s.t))}</h2>
          ${!isNew && s === R.sections[0] && model.cSource ? sourceBadge(model.cSource) : ""}</div>
        <div class="card-body"><div class="form-grid">${s.fields.map(fieldHtml).join("")}</div></div></div>`).join("");
      $("#view").innerHTML = pageHead(title, "", actions, crumbs) + `<form id="form" novalidate>${sections}${R.lines ? linesHtml() : ""}</form>`;
      if (R.lines) { $("#totals").innerHTML = totalsHtml(); bindTotals(); }
      bind();
      if (R.tax && model[R.tax.supplier]) loadSupplierTax(model[R.tax.supplier]);
    }

    function bind() {
      const allFields = R.sections.flatMap((s) => s.fields);
      allFields.forEach((fd) => {
        const el = $(`[data-f="${fd.f}"]`, $("#form"));
        if (!el) return;
        const update = () => {
          model[fd.f] = fd.type === "check" ? el.checked : fd.int ? parseInt(el.value, 10) : el.value;
          if (fd.f === "cDevise" || fd.f === "Devise") refreshAmounts();
        };
        el.addEventListener(fd.type === "check" || fd.type === "select" ? "change" : "input", update);
        if (fd.lookup && !el.readOnly) {
          bindLookup(el, fd.lookup, (code, label) => {
            model[fd.f] = code;
            if (fd.fill && label) {
              model[fd.fill] = label;
              const target = $(`[data-f="${fd.fill}"]`);
              if (target) target.value = label;
            }
            if (fd.onPick === "fillFromPo") fillFromPo(code);
            if (R.tax && fd.f === R.tax.supplier) { taxLive = true; loadSupplierTax(code); }
          });
        }
      });
      if (R.lines) {
        $$("tr[data-line]").forEach((tr) => {
          const ln = model.lines[+tr.dataset.line];
          $$("input[data-lf]", tr).forEach((el) => {
            el.addEventListener("input", () => { ln[el.dataset.lf] = el.value; taxLive = true; refreshAmounts(); });
            if (el.dataset.lookup) bindLookup(el, el.dataset.lookup, (code) => { ln[el.dataset.lf] = code; });
          });
        });
        $$("[data-remove]").forEach((b) => b.addEventListener("click", () => { model.lines.splice(+b.dataset.remove, 1); taxLive = true; render(); }));
        $("#addLine").addEventListener("click", () => {
          model.lines = model.lines || [];
          model.lines.push(R.lines.newLine ? R.lines.newLine(model) : {});
          render();
          const rows = $$("tr[data-line]");
          const first = rows.length && $("input[data-lf]:not([data-lf=cUnique])", rows[rows.length - 1]);
          if (first) first.focus();
        });
      }
      $("#form").addEventListener("submit", (e) => { e.preventDefault(); save(); });
      $("#saveBtn").addEventListener("click", save);
      const del = $("#deleteBtn");
      if (del) del.addEventListener("click", remove);
    }

    function apiPath() {
      return R.api + "/" + String(id).split("/").map(enc).join("/");
    }

    async function save() {
      errors = {};
      R.sections.flatMap((s) => s.fields).forEach((fd) => {
        if ((fd.req || (fd.reqNew && isNew)) && !String(model[fd.f] == null ? "" : model[fd.f]).trim()) errors[fd.f] = "required";
      });
      if (Object.keys(errors).length) { render(); toast(t("err.form"), "error"); return; }
      try {
        const saved = await api(isNew ? R.api : apiPath(), { method: isNew ? "POST" : "PUT", body: model });
        toast(t(isNew ? "common.created" : "common.saved"), "success");
        if (isNew) {
          location.hash = "#" + R.route + "/" + String(R.id(saved)).split("/").map(enc).join("/");
        } else {
          model = saved;
          render();
        }
      } catch (e) {
        if (e.field) { errors[e.field] = e.code; render(); }
        toast(t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic"), "error");
      }
    }

    async function remove() {
      if (!confirm(t("common.confirmDelete"))) return;
      try {
        await api(apiPath(), { method: "DELETE" });
        toast(t("common.deleted"), "success");
        location.hash = "#" + R.route;
      } catch (e) { toast(t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic"), "error"); }
    }

    return {
      async load() {
        if (isNew) {
          model = Object.assign({}, typeof R.defaults === "function" ? R.defaults() : R.defaults || {});
          return;
        }
        try { model = await api(apiPath()); } catch (e) { if (e.status === 404) missing = true; else throw e; }
      },
      render,
    };
  }

  // ---------- My account (change own password)
  function accountView() {
    return {
      async load() {},
      render() {
        const f = (id, l, auto) => `<div class="field"><label for="${id}">${esc(t(l))}<span class="req">*</span></label><input type="password" id="${id}" autocomplete="${auto}"></div>`;
        $("#view").innerHTML = pageHead(t("acc.title"), `${user.name} (${user.username}) · ${t("role." + user.role)}`) + `
          <form class="card" id="pwForm" novalidate><div class="card-head"><h2>${esc(t("acc.changePassword"))}</h2></div>
            <div class="card-body"><div class="form-grid">
              ${f("pwCurrent", "acc.current", "current-password")}${f("pwNew", "f.password", "new-password")}${f("pwConfirm", "acc.confirm", "new-password")}
            </div><p class="help">${esc(t("usr.passwordHelp"))}</p>
            <button type="submit" class="btn primary">${esc(t("common.save"))}</button></div></form>`;
        $("#pwForm").addEventListener("submit", async (e) => {
          e.preventDefault();
          const current = $("#pwCurrent").value, password = $("#pwNew").value;
          if (!current || !password) { toast(t("err.form"), "error"); return; }
          if (password !== $("#pwConfirm").value) { toast(t("err.password_mismatch"), "error"); return; }
          try {
            await api("auth/password", { method: "POST", body: { current, password } });
            toast(t("acc.passwordChanged"), "success");
            this.render();
          } catch (err) { toast(t("err." + err.code) !== "err." + err.code ? t("err." + err.code) : t("err.generic"), "error"); }
        });
      },
    };
  }

  // ------------------------------------------------------------------ Supplier selection (SkyAI requisitions)
  // Criteria used by getBestSupplier.p: weights, history window, tie margin, AI instructions,
  // plus a test box that runs the selection on typed items.
  function selectionView() {
    let data = null, result = null, testText = "";
    const CRIT = ["price", "leadTime", "onTime", "quality"];
    const pct = (v) => (v == null ? "—" : Math.round(v * 100) + " %");
    function numField(id, label, value, help) {
      return `<div class="field"><label for="${id}">${esc(t(label))}</label><input type="text" inputmode="numeric" id="${id}" value="${esc(value)}" ${isAdmin() ? "" : "readonly"}>${help ? `<span class="help">${esc(t(help))}</span>` : ""}</div>`;
    }
    function read() {
      const v = (id) => $("#" + id).value;
      return {
        weights: Object.fromEntries(CRIT.map((k) => [k, num(v("w-" + k))])),
        historyMonths: num(v("s-months")), minOrders: num(v("s-min")), tieMargin: num(v("s-tie")),
        maxCandidates: num(v("s-max")), useAI: $("#s-ai").checked, instructions: v("s-instr"),
      };
    }
    function parseItems(text) {
      // one item per line: "code ; description ; quantity" (code may be empty)
      return text.split("\n").map((l) => l.trim()).filter(Boolean).map((l, i) => {
        const [code, desc, qty] = l.split(";").map((x) => (x || "").trim());
        return { line: i + 1, productCode: code, description: desc || code, quantity: num(qty) || 1 };
      });
    }
    function resultHtml() {
      if (!result) return "";
      const rows = result.items.map((it) => {
        const prod = it.matchedProduct ? `${esc(it.matchedProduct.code)} — ${esc(it.matchedProduct.desc)}` : `<span class="muted">${esc(t("sel.noMatch"))}</span>`;
        const cands = it.candidates.length ? it.candidates.map((c) => `<div class="sel-cand ${c.recommended ? "best" : ""}">
            <b>${esc(c.cCode)}</b> ${esc(c.cName)} · <b>${esc(c.score)}</b>/100 ${c.recommended ? `<span class="badge yes">${esc(t("sel.recommended"))}</span>` : ""}${c.tied ? ` <span class="badge Approved">${esc(t("sel.tied"))}</span>` : ""}
            <div class="help">${esc(c.reason)}</div>
            ${c.source === "rules" ? "" : `<div class="help">${esc(t("sel.m.price"))} ${money(c.metrics.avgUnitPrice)} · ${esc(t("sel.m.lead"))} ${esc(c.metrics.avgLeadDays == null ? "—" : String(c.metrics.avgLeadDays).replace(".", lang === "fr" ? "," : ".") + " " + t("sel.days"))} · ${esc(t("sel.m.onTime"))} ${pct(c.metrics.onTimeRate)} · ${esc(t("sel.m.quality"))} ${pct(c.metrics.conformityRate)} · ${esc(t("sel.m.orders"))} ${esc(c.metrics.orders)}</div>`}</div>`).join("")
          : `<div class="help">${esc(it.reason || "")}</div>`;
        return `<tr><td>${esc(it.line)}</td><td>${esc(it.description)}<div class="help">${prod}</div></td><td>${esc(t("sel.decision." + it.decision))}</td><td class="sel-cands">${cands}</td></tr>`;
      }).join("");
      return `<div class="card"><div class="card-head"><h2>${esc(t("sel.result"))}</h2><span class="badge SkyAI" style="margin-left:auto">${esc(t("sel.engine." + result.engine))}</span></div>
        <div class="table-wrap"><table class="grid sel-table"><thead><tr><th>#</th><th>${esc(t("sel.item"))}</th><th>${esc(t("sel.decision"))}</th><th>${esc(t("sel.candidates"))}</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
    }
    return {
      async load() { data = await api("supplier-selection/settings"); },
      render() {
        const s = data.settings, ai = data.ai;
        const aiLine = ai.configured ? t("sel.aiOn", { model: ai.model }) : t("sel.aiOff");
        $("#view").innerHTML = pageHead(t("sel.title"), t("sel.subtitle")) + `
          <form class="card" id="selForm" novalidate><div class="card-head"><h2>${esc(t("sel.weights"))}</h2></div>
            <div class="card-body"><div class="form-grid">
              ${CRIT.map((k) => numField("w-" + k, "sel.w." + k, s.weights[k])).join("")}
            </div><p class="help">${esc(t("sel.weightsHelp"))}</p></div>
            <div class="card-head"><h2>${esc(t("sel.rules"))}</h2></div>
            <div class="card-body"><div class="form-grid">
              ${numField("s-months", "sel.months", s.historyMonths)}${numField("s-min", "sel.minOrders", s.minOrders)}
              ${numField("s-tie", "sel.tie", s.tieMargin, "sel.tieHelp")}${numField("s-max", "sel.max", s.maxCandidates)}
              <div class="field span-4"><label class="check"><input type="checkbox" id="s-ai" ${s.useAI ? "checked" : ""} ${isAdmin() ? "" : "disabled"}> ${esc(t("sel.useAI"))}</label><span class="help">${esc(aiLine)}</span></div>
              <div class="field span-4"><label for="s-instr">${esc(t("sel.instructions"))}</label><textarea id="s-instr" ${isAdmin() ? "" : "readonly"}>${esc(s.instructions)}</textarea><span class="help">${esc(t("sel.instructionsHelp"))}</span></div>
            </div>${isAdmin() ? `<button type="submit" class="btn primary">${esc(t("common.save"))}</button>` : `<p class="help">${esc(t("sel.adminOnly"))}</p>`}</div></form>
          <form class="card" id="selTest" novalidate><div class="card-head"><h2>${esc(t("sel.test"))}</h2></div>
            <div class="card-body"><div class="field span-4"><label for="s-items">${esc(t("sel.items"))}</label><textarea id="s-items" rows="5" placeholder="AL6061-F125-48 ; Feuille aluminium 6061 1/8 ; 10&#10; ; Écrous inox 1/4-20 boîte de 100 ; 12">${esc(testText)}</textarea><span class="help">${esc(t("sel.itemsHelp"))}</span></div>
            <button type="submit" class="btn">${esc(t("sel.run"))}</button></div></form>
          <div id="selResult">${resultHtml()}</div>`;
        $("#selForm").addEventListener("submit", async (e) => {
          e.preventDefault();
          try {
            data = await api("supplier-selection/settings", { method: "PUT", body: read() });
            toast(t("common.saved"), "success");
            this.render();
          } catch (err) { toast(t("err.generic"), "error"); }
        });
        $("#selTest").addEventListener("submit", async (e) => {
          e.preventDefault();
          testText = $("#s-items").value;
          const items = parseItems(testText);
          if (!items.length) { toast(t("err.form"), "error"); return; }
          const btn = $("#selTest button");
          btn.disabled = true;
          try {
            result = await api("supplier-selection/test", { method: "POST", body: { items, lang, settings: read() } });
            $("#selResult").innerHTML = resultHtml();
          } catch (err) { toast(t("err.generic"), "error"); }
          btn.disabled = false;
        });
      },
    };
  }

  // ------------------------------------------------------------------ Router
  function currentPath() {
    const h = location.hash.replace(/^#/, "");
    return h ? (h.startsWith("/") ? h : "/" + h) : "/";
  }

  function resolve(path) {
    const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
    if (!parts.length) return dashboardView();
    const [head, ...rest] = parts;
    if (head === "gl") {
      const tab = rest[0] === "cc" ? "cc" : "accounts";
      const key = tab === "cc" ? "cc" : "gl";
      const sub = rest.slice(1);
      if (!sub.length) return listView(key);
      if (sub[0] === "new") return formView(key, null);
      return formView(key, sub.join("/"));
    }
    if (head === "account") return accountView();
    if (head === "selection") return selectionView();
    if (head === "admin" && rest[0] === "users" && isAdmin()) {
      if (!rest[1]) return listView("users");
      if (rest[1] === "new") return formView("users", null);
      return formView("users", rest[1]);
    }
    const map = { suppliers: "suppliers", invoices: "invoices", po: "po", receptions: "receptions" };
    const key = map[head];
    if (!key) return dashboardView();
    if (!rest.length) return listView(key);
    if (rest[0] === "new") return formView(key, null);
    return formView(key, rest.join("/"));
  }

  let navToken = 0;
  async function route() {
    const token = ++navToken;
    renderSidebar();
    const v = resolve(currentPath());
    $("#view").innerHTML = `<div class="empty">${esc(t("common.loading"))}</div>`;
    try {
      await v.load();
      if (token !== navToken) return;
      view = v;
      v.render();
      window.scrollTo(0, 0);
    } catch (e) {
      $("#view").innerHTML = `<div class="card"><div class="empty">${esc(t("err.generic"))}</div></div>`;
    }
  }

  // ------------------------------------------------------------------ Login
  function setLang(l, remember) {
    if (!I18N[l]) return;
    lang = l;
    try { localStorage.setItem("erp.lang", lang); } catch (e) { /* ignore */ }
    applyStaticI18n();
    if (user) {
      renderSidebar();
      if (view) view.render();
      if (remember) api("auth/lang", { method: "POST", body: { lang } }).catch(() => {});
    }
  }

  function showUser() {
    const initials = (user.name || user.username).split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
    $("#userAvatar").textContent = initials;
    $("#userName").textContent = user.name || user.username;
    $("#userLink").title = t("acc.title");
  }

  function showLogin() {
    user = null;
    view = null;
    document.body.classList.add("logged-out");
    $("#login").hidden = false;
    $("#loginError").hidden = true;
    $("#loginPass").value = "";
    setTimeout(() => $("#loginUser").focus(), 0);
  }

  let langPicked = false; // language chosen on the login screen: saved to the user instead of the stored one
  function enterApp(u) {
    user = u;
    if (langPicked) api("auth/lang", { method: "POST", body: { lang } }).catch(() => {});
    else if (u.lang && I18N[u.lang]) setLang(u.lang);
    langPicked = false;
    document.body.classList.remove("logged-out");
    $("#login").hidden = true;
    showUser();
    route();
  }

  $("#loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = $("#loginError");
    err.hidden = true;
    const username = $("#loginUser").value.trim(), password = $("#loginPass").value;
    if (!username || !password) { err.textContent = t("auth.missing"); err.hidden = false; return; }
    try {
      enterApp(await api("auth/login", { method: "POST", body: { username, password }, noAuthRedirect: true }));
    } catch (ex) {
      err.textContent = t(ex.code === "bad_login" ? "auth.bad" : "err.generic");
      err.hidden = false;
      $("#loginPass").select();
    }
  });

  $("#logoutBtn").addEventListener("click", async () => {
    try { await api("auth/logout", { method: "POST", noAuthRedirect: true }); } catch (e) { /* ignore */ }
    showLogin();
    history.replaceState(null, "", "#/");
  });

  // ------------------------------------------------------------------ Boot
  $$(".lang-switch button").forEach((b) => b.addEventListener("click", () => {
    if (!user) langPicked = true;
    setLang(b.dataset.lang, true);
  }));
  $("#menuToggle").addEventListener("click", () => document.body.classList.toggle("nav-open"));
  window.addEventListener("hashchange", () => { if (user) route(); });
  applyStaticI18n();
  api("auth/me", { noAuthRedirect: true }).then(enterApp).catch(showLogin);
})();
