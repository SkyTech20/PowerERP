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
  // Amount/quantity inputs: drop anything that is not a digit, separator or minus ("$", spaces, letters).
  const numOnly = (el) => {
    const v = el.value, c = v.replace(/[^\d.,-]/g, "");
    if (c !== v) {
      const pos = Math.max(0, (el.selectionStart || 0) - (v.length - c.length));
      el.value = c;
      try { el.setSelectionRange(pos, pos); } catch (e) { /* ignore */ }
    }
    return c;
  };
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
      err.detail = data && data.detail;
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
    { k: "pur", icon: "🛒", items: [{ k: "pur.po", route: "/po" }, { k: "pur.receptions", route: "/receptions" }, "pur.requisitions", "pur.returns", "pur.pricelists"] },
    { k: "ar", icon: "💰", items: ["ar.customers", "ar.invoices", "ar.receipts", "ar.credits", "ar.collections"] },
    { k: "sales", icon: "📈", items: ["sales.quotes", "sales.orders", "sales.shipping", "sales.pricing", "sales.commissions"] },
    { k: "inv", icon: "📦", items: [
      { k: "inv.items", route: "/inv/items" }, { k: "inv.stock", route: "/inv/stock" }, { k: "inv.movements", route: "/inv/movements" },
      { k: "inv.replenishment", route: "/inv/replenishment" }, { k: "inv.count", route: "/inv/counts" }, { k: "inv.valuation", route: "/inv/valuation" },
      { k: "inv.warehouses", route: "/inv/warehouses" }, { k: "inv.params", route: "/inv/params" }, { k: "inv.setup", route: "/inv/categories" },
    ] },
    { k: "prod", icon: "🏭", items: ["prod.bom", "prod.workorders", "prod.routings", "prod.mrp", "prod.shopfloor"] },
    { k: "hr", icon: "👥", items: ["hr.employees", "hr.timesheets", "hr.payroll", "hr.benefits"] },
    { k: "fa", icon: "🏢", items: ["fa.assets", "fa.depreciation"] },
    { k: "proj", icon: "📁", items: ["proj.projects", "proj.jobcost"] },
    { k: "crm", icon: "🤝", items: ["crm.contacts", "crm.opportunities"] },
    { k: "rep", icon: "📊", items: ["rep.designer", "rep.bi"] },
    { k: "admin", icon: "⚙️", items: ["admin.companies", { k: "admin.users", route: "/admin/users", admin: true }, { k: "admin.taxes", route: "/admin/taxes" }, "admin.currencies", { k: "admin.backups", route: "/admin/backups", admin: true }, "admin.settings"] },
  ];
  const openGroups = new Set(["gl", "ap", "pur", "inv"]);
  let user = null; // logged-in user (GET api/auth/me)
  const isAdmin = () => !!user && user.role === "admin";
  // Menu items flagged admin: true are links for administrators only.
  const usable = (i) => typeof i === "object" && (!i.admin || isAdmin());

  function renderSidebar() {
    const path = currentPath();
    const menuRoute = activeMenuRoute(path);
    const isActive = (route) => (route === "/" ? path === "/" : route === menuRoute || path === route || path.startsWith(route + "/"));
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
  };

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

  // ------------------------------------------------------------------ Products, taxes and inventory
  const today = () => new Date().toISOString().slice(0, 10);
  const opts = (prefix, values) => values.map((v) => [v, prefix + v]);
  // FR / EN text of a record (cDescFR / cDescEN, cNameFR / cNameEN): the UI language, else French
  const dl = (r, base) => (lang === "fr" ? r[base + "FR"] : r[base + "EN"] || r[base + "FR"]) || "";
  const qtyFmt = (v) => (v === "" || v == null ? "" : new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { maximumFractionDigits: 4 }).format(num(v)));
  const optBadge = (prefix, cls) => (v) => (v ? `<span class="badge ${cls ? cls(v) : ""}">${esc(t(prefix + v))}</span>` : "");
  const descCol = (base) => ({ f: base + "FR", l: "f.cDescription", wrap: true, fmt: (v, r) => esc(dl(r, base)) });
  const productLink = (r) => "/inv/items/" + enc(r.cProduct);
  const whFilter = { f: "cWarehouse", l: "f.inv.cWarehouse", lookup: "warehouses" };
  const isStockType = (m) => ["stock", "kit", "raw"].includes(m.cType);
  let prefill = null; // { key, values }: defaults for the next "new" form (e.g. a movement for this product)
  function newWith(key, values) { prefill = { key, values }; location.hash = "#" + RES[key].route + "/new"; }

  const PRODUCT_TYPES = ["stock", "nonstock", "service", "kit", "raw"];
  const MOVE_TYPES = ["IN", "OUT", "TRF", "ADJ", "CNT", "RSV"];
  const DOC_TYPES = ["MAN", "PO", "REC", "INV", "SO", "CNT", "PROD"];
  const LOCATION_TYPES = ["picking", "reserve", "receiving", "shipping", "quarantine", "staging"];
  const MV_IN = (m) => m.cType === "IN" || ((m.cType === "ADJ" || m.cType === "CNT") && num(m.dQty) > 0);

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
    products: {
      api: "products", route: "/inv/items", title: "prod.title", sub: "prod.subtitle", one: "prod.one", newTitle: "prod.new",
      id: (r) => r.cCode, label: (r) => `${r.cCode} — ${dl(r, "cDesc")}`, sort: "cCode",
      formTabs: [["gen", "prod.tab.general"], ["units", "prod.units"], ["prices", "prod.costs"], ["tax", "prod.tab.taxes"],
        ["inv", "prod.inventory"], ["log", "prod.tab.logistics"], ["sup", "prod.suppliers"], ["stock", "prod.stock"]],
      filters: [
        { f: "cStatus", l: "f.prod.cStatus", options: opts("o.status.", ["active", "inactive", "discontinued"]) },
        { f: "cType", l: "f.prod.cType", options: opts("o.ptype.", PRODUCT_TYPES) },
        { f: "cCategory", l: "f.prod.cCategory", lookup: "categories" },
      ],
      columns: [
        { f: "cCode", l: "f.prod.cCode" }, descCol("cDesc"), { f: "cCategory", l: "f.prod.cCategory" },
        { f: "cType", l: "f.prod.cType", fmt: (v) => esc(t("o.ptype." + v)) }, { f: "cStockUOM", l: "f.prod.unit" },
        { f: "dQtyOnHand", l: "f.inv.dQtyOnHand", num: true, fmt: (v, r) => (r.lStocked ? esc(qtyFmt(v)) : "—") },
        { f: "dQtyAvailable", l: "f.inv.dQtyAvailable", num: true, fmt: (v, r) => (r.lStocked ? esc(qtyFmt(v)) : "—") },
        { f: "dPrice1", l: "f.prod.dPrice1", num: true, fmt: (v, r) => (v ? esc(money(v, r.cCurrency)) : "") },
        { f: "cStatus", l: "f.prod.cStatus", fmt: optBadge("o.status.", (v) => (v === "active" ? "yes" : "no")) },
      ],
      defaults: () => ({ cStatus: "active", cType: "stock", cCostMethod: "avg", cCurrency: "CAD", cStockUOM: "UN", cPurchaseUOM: "UN",
        dPurchaseFactor: "1", cSalesUOM: "UN", dSalesFactor: "1", cSalesTaxGroup: "QC", cPurchaseTaxGroup: "QC", lStocked: true,
        lSellable: true, lPurchasable: true, lPORequired: true, cWeightUOM: "kg", cDimUOM: "cm", cCountryOrigin: "CA", cABCClass: "", lines: [] }),
      sections: [
        { t: "prod.ident", fields: [
          { f: "cCode", l: "f.prod.cCode", req: true, key: true },
          { f: "cType", l: "f.prod.cType", type: "select", options: opts("o.ptype.", PRODUCT_TYPES), rerender: true },
          { f: "cStatus", l: "f.prod.cStatus", type: "select", options: opts("o.status.", ["active", "inactive", "discontinued"]) },
          { f: "cCategory", l: "f.prod.cCategory", lookup: "categories" },
          { f: "cDescFR", l: "f.cDescFR", req: true, span: 2 }, { f: "cDescEN", l: "f.cDescEN", span: 2 },
          { f: "cLongDescFR", l: "f.prod.cLongDescFR", type: "textarea", span: 2 }, { f: "cLongDescEN", l: "f.prod.cLongDescEN", type: "textarea", span: 2 },
          { f: "cBrand", l: "f.prod.cBrand" }, { f: "cModel", l: "f.prod.cModel" },
          { f: "cManufacturer", l: "f.prod.cManufacturer" }, { f: "cMfrPartNo", l: "f.prod.cMfrPartNo" },
          { f: "cUPC", l: "f.prod.cUPC", help: "f.prod.cUPC.help" }, { f: "cImageUrl", l: "f.prod.cImageUrl" },
          { f: "cSpecUrl", l: "f.prod.cSpecUrl" }, { f: "cSdsUrl", l: "f.prod.cSdsUrl", help: "f.prod.cSdsUrl.help" },
        ] },
        { tab: "units", t: "prod.units", fields: [
          { f: "cStockUOM", l: "f.prod.cStockUOM", req: true, lookup: "uom" },
          { f: "cPurchaseUOM", l: "f.prod.cPurchaseUOM", lookup: "uom" },
          { f: "dPurchaseFactor", l: "f.prod.dPurchaseFactor", type: "number", help: "f.prod.factor.help" },
          { f: "cSalesUOM", l: "f.prod.cSalesUOM", lookup: "uom" }, { f: "dSalesFactor", l: "f.prod.dSalesFactor", type: "number" },
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
          { f: "lStocked", l: "f.prod.lStocked", type: "check", show: isStockType, help: "f.prod.lStocked.help" },
          { f: "cDefaultWarehouse", l: "f.prod.cDefaultWarehouse", lookup: "warehouses", show: isStockType },
          { f: "cABCClass", l: "f.prod.cABCClass", type: "select", options: [["", "—"], ["A", "A"], ["B", "B"], ["C", "C"]], raw: true, show: isStockType },
          { f: "iShelfLifeDays", l: "f.prod.iShelfLifeDays", type: "number", show: isStockType },
          { f: "lLotControl", l: "f.prod.lLotControl", type: "check", show: isStockType },
          { f: "lSerialControl", l: "f.prod.lSerialControl", type: "check", show: isStockType },
          { f: "lExpiryControl", l: "f.prod.lExpiryControl", type: "check", show: isStockType },
        ] },
        { tab: "log", t: "prod.logistics", fields: [
          { f: "lSellable", l: "f.prod.lSellable", type: "check" }, { f: "lPurchasable", l: "f.prod.lPurchasable", type: "check" },
          { f: "lPORequired", l: "f.prod.lPORequired", type: "check" }, { f: "lHazardous", l: "f.prod.lHazardous", type: "check" },
          { f: "iWarrantyMonths", l: "f.prod.iWarrantyMonths", type: "number" }, { f: "cCountryOrigin", l: "f.prod.cCountryOrigin" },
          { f: "cHSCode", l: "f.prod.cHSCode", help: "f.prod.cHSCode.help" }, { f: "cFreightClass", l: "f.prod.cFreightClass" },
          { f: "cNotes", l: "f.prod.cNotes", type: "textarea", span: 4 },
        ] },
      ],
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

  // ---------- Replenishment: products at or below their reorder point, and the POs to create
  function replenishmentView() {
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
            <td><a href="#${productLink(r)}">${esc(r.cProduct)}</a></td><td class="wrap">${esc(dl(r, "cDesc"))}</td><td>${esc(r.cWarehouse)}</td>
            <td class="num">${esc(qtyFmt(r.dQtyAvailable))}</td><td class="num">${esc(qtyFmt(r.dQtyOnOrder))}</td>
            <td class="num">${esc(qtyFmt(r.dReorderPoint))}</td><td class="num">${esc(qtyFmt(r.dMaxQty))}</td>
            <td class="num">${esc(qtyFmt(r.dSuggestedQty))} ${esc(r.cStockUOM)}</td>
            <td class="w-sm"><input type="text" data-qty value="${esc(r.dPurchaseQty)}" inputmode="decimal" style="text-align:right;width:70px"> ${esc(r.cPurchaseUOM)}</td>
            <td>${r.cSupplierCode ? esc(r.cSupplierCode + " — " + r.cSupplierName) : `<span class="badge no">${esc(t("rep.noSupplier"))}</span>`}</td>
            <td class="num">${esc(money(r.dUnitCost))}</td><td class="num" data-amt></td></tr>`).join("");
        const done = created ? `<div class="card notice"><div class="card-body">${esc(t("rep.created"))}
            ${created.map((p) => `<a class="btn small" href="#/po/${enc(p.cPO)}">${esc(p.cPO)} — ${esc(p.cSupplierName)} (${esc(money(p.dTotalAmount))})</a>`).join(" ")}</div></div>` : "";
        $("#view").innerHTML = pageHead(t("rep.title"), t("rep.subtitle"), `<button class="btn primary" id="createPo" ${data.items.length ? "" : "disabled"}>${esc(t("rep.createPo"))}</button>`) + done + `
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
        $("#repWh").addEventListener("change", async (e) => { wh = e.target.value; created = null; await this.load(); this.render(); });
        $("#createPo").addEventListener("click", async () => {
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

  function fmtDateTime(v) {
    if (!v) return "—";
    const d = new Date(v);
    if (isNaN(d)) return v;
    return d.toLocaleString(lang === "fr" ? "fr-CA" : "en-CA", { dateStyle: "short", timeStyle: "short" });
  }

  // ------------------------------------------------------------------ Lookups
  // Lookup fields are plain <select>s filled with the whole list (code — label); the list is fetched
  // once per open form. A value missing from the list (old data) is kept as its own option.
  let lookupCache = {};
  function lookupRows(kind, params) {
    const extra = params ? Object.entries(params).map(([k, v]) => "&" + k + "=" + enc(v == null ? "" : v)).join("") : "";
    const key = kind + extra;
    if (!lookupCache[key]) lookupCache[key] = api("lookups/" + kind + "?all=1&lang=" + lang + extra).catch(() => { delete lookupCache[key]; return []; });
    return lookupCache[key];
  }
  function lookupOptions(rows, value) {
    const v = value == null ? "" : String(value);
    const known = !v || rows.some((r) => r.code === v);
    return `<option value=""></option>${known ? "" : `<option value="${esc(v)}" selected>${esc(v)}</option>`}`
      + rows.map((r) => `<option value="${esc(r.code)}" ${r.code === v ? "selected" : ""}>${esc(r.code)}${r.label ? " — " + esc(r.label) : ""}</option>`).join("");
  }
  // Fills the select and calls onPick(code, label) on change. Returns a refresh function that reloads the
  // list when the params (e.g. the warehouse of a location) have changed.
  function bindLookup(sel, kind, onPick, params) {
    let rows = [];
    let lastKey = null;
    const fill = async () => {
      const p = params ? params() : null;
      const key = JSON.stringify(p);
      if (key === lastKey) return;
      lastKey = key;
      rows = await lookupRows(kind, p);
      const v = sel.value;
      sel.innerHTML = lookupOptions(rows, v);
      sel.value = v;
    };
    fill();
    sel.addEventListener("change", () => {
      const r = rows.find((x) => x.code === sel.value);
      if (onPick) onPick(sel.value, r ? r.label : "");
    });
    return fill;
  }

  // ------------------------------------------------------------------ Views
  const listState = {};
  let view = null;

  function pageHead(title, sub, actions, crumbs) {
    return `<div class="page-head"><div>${crumbs ? `<div class="crumbs">${crumbs}</div>` : ""}<h1>${esc(title)}</h1>${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</div>
      <div class="actions">${actions || ""}</div></div>`;
  }

  // Screens shown as tabs of one menu entry: [resource key, label]
  const TABSETS = {
    gl: [["gl", "gl.tab.accounts"], ["cc", "gl.tab.cc"]],
    tax: [["taxcodes", "tax.tab.codes"], ["taxgroups", "tax.tab.groups"]],
    wh: [["warehouses", "wh.tab.warehouses"], ["locations", "wh.tab.locations"]],
    setup: [["categories", "setup.tab.categories"], ["uom", "setup.tab.uom"]],
  };
  function tabsHtml(R) {
    return `<div class="tabs">${TABSETS[R.tabset].map(([k, l]) => `<a href="#${RES[k].route}" class="${RES[k] === R ? "active" : ""}">${esc(t(l))}</a>`).join("")}</div>`;
  }
  const tabLabel = (R) => { const tab = TABSETS[R.tabset].find(([k]) => RES[k] === R); return tab ? t(tab[1]) : ""; };

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
            ${data.products != null ? kpi(data.reorderItems ? "/inv/replenishment" : "/inv/valuation", t("dash.inventory"), money(data.stockValue), t("dash.inventoryMeta", { n: fmtInt(data.products), r: data.reorderItems })) : ""}
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
        // Filters whose options come from a lookup (e.g. the warehouses)
        await Promise.all((R.filters || []).filter((f) => f.lookup && !f.options).map(async (f) => {
          f.options = (await api("lookups/" + f.lookup + "?lang=" + lang)).map((r) => [r.code, r.code]);
          f.raw = true;
        }));
        data = await api(R.api + "?" + params.toString());
      },
      render() {
        const pages = Math.max(1, Math.ceil(data.total / data.size));
        const head = R.columns.map((c) => {
          const arrow = st.sort === c.f ? `<span class="arrow">${st.dir === "desc" ? "▼" : "▲"}</span>` : "";
          return `<th class="sortable ${c.num ? "num" : ""}" data-sort="${c.f}">${esc(t(c.l))}${arrow}</th>`;
        }).join("");
        const href = (r) => (R.rowHref ? R.rowHref(r) : R.route + "/" + String(R.id(r)).split("/").map(enc).join("/"));
        const rows = data.items.map((r) => `<tr class="${R.noClick ? "" : "clickable"}" data-href="${esc(R.noClick ? "" : href(r))}">${R.columns.map((c) => {
          const v = r[c.f];
          const cell = c.fmt ? c.fmt(v, r) : esc(v);
          return `<td class="${c.num ? "num" : ""} ${c.wrap ? "wrap" : ""}">${cell}</td>`;
        }).join("")}</tr>`).join("");
        const filters = (R.filters || []).map((f) => `<select data-filter="${f.f}" aria-label="${esc(t(f.l))}" style="width:auto">
            <option value="">${esc(t(f.l))}: ${esc(t("common.all"))}</option>
            ${f.options.map(([v, l]) => `<option value="${esc(v)}" ${st.filters[f.f] === v ? "selected" : ""}>${esc(f.raw ? l : t(l))}</option>`).join("")}
          </select>`).join("");
        $("#view").innerHTML = pageHead(t(R.title), t(R.sub), R.noNew ? "" : `<a class="btn primary" href="#${R.route}/new">＋ ${esc(t("common.new"))}</a>`)
          + (R.tabset ? tabsHtml(R) : "")
          + `<div class="card"><div class="toolbar"><input type="search" id="q" placeholder="${esc(t("common.search"))}" value="${esc(st.q)}">${filters}
              <span class="count">${esc(t("common.records", { n: fmtInt(data.total) }))}</span></div>
            <div class="table-wrap">${data.items.length ? `<table class="grid"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>` : `<div class="empty">${esc(t("common.empty"))}</div>`}</div>
            ${R.footer ? R.footer(data) : ""}
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
        $$("tr[data-href]").forEach((tr) => { if (tr.dataset.href) tr.addEventListener("click", () => { location.hash = "#" + tr.dataset.href; }); });
        $("#prev").addEventListener("click", () => { st.page--; reload(); });
        $("#next").addEventListener("click", () => { st.page++; reload(); });
      },
    };
  }

  // ---------- Generic form
  // Field options: req, reqNew, key (read-only once saved), readonly, type (text | number | date | select | check |
  // textarea | password | email), lookup (+ fill, lookupParams, onPick), show(model, isNew), rerender (redraw on change).
  // Resource options: lines, totals, tax, locked(model, isNew), actions, panel { html(model), bind(model) }.
  function formView(key, id) {
    const R = RES[key];
    const isNew = id == null;
    let model = null;
    let errors = {};
    let missing = false;
    let locked = false;
    let activeTab = R.formTabs ? R.formTabs[0][0] : null; // R.formTabs: sections shown as tabs
    let refreshers = []; // lookups whose list depends on other fields
    lookupCache = {};
    let taxInfo = null; // { code, tps, tvq } of the supplier, when R.tax
    let taxLive = isNew; // existing records keep their stored taxes until something is changed

    const cur = () => (R.currency ? R.currency(model) : "CAD");
    const visible = (fd) => !fd.show || fd.show(model, isNew);

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
      if (!visible(fd)) return "";
      const v = model[fd.f];
      const ro = locked || fd.readonly || (fd.key && !isNew);
      const required = !locked && (fd.req || (fd.reqNew && isNew));
      const label = `<label for="f-${fd.f}">${esc(t(fd.l))}${required ? '<span class="req">*</span>' : ""}</label>`;
      const err = errors[fd.f] ? `<span class="err">${esc(t("err." + errors[fd.f]))}</span>` : "";
      const help = fd.help ? `<span class="help">${esc(t(fd.help))}</span>` : "";
      const cls = `field ${fd.span === 4 ? "span-4" : fd.span >= 2 ? "span-2" : ""} ${errors[fd.f] ? "invalid" : ""}`;
      if (fd.type === "check") {
        return `<div class="${cls}"><label class="check"><input type="checkbox" id="f-${fd.f}" data-f="${fd.f}" ${v ? "checked" : ""} ${ro ? "disabled" : ""}> ${esc(t(fd.l))}</label>${help}${err}</div>`;
      }
      let input;
      const blank = (x) => (x == null ? "" : String(x));
      if (fd.lookup && !ro) {
        input = `<select id="f-${fd.f}" data-f="${fd.f}">${lookupOptions([], v)}</select>`;
      } else if (fd.suggestions && !ro) {
        const opts = ["", ...fd.suggestions, ...(blank(v) && !fd.suggestions.includes(blank(v)) ? [blank(v)] : [])];
        input = `<select id="f-${fd.f}" data-f="${fd.f}">${opts.map((o) => `<option value="${esc(o)}" ${blank(v) === o ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>`;
      } else if (fd.type === "select") {
        input = `<select id="f-${fd.f}" data-f="${fd.f}" ${ro ? "disabled" : ""}>${fd.options.map(([ov, ol]) => `<option value="${esc(ov)}" ${String(v == null ? "" : v) === ov ? "selected" : ""}>${esc(fd.raw ? ol : t(ol))}</option>`).join("")}</select>`;
      } else if (fd.type === "textarea") {
        input = `<textarea id="f-${fd.f}" data-f="${fd.f}" ${ro ? "readonly" : ""}>${esc(v)}</textarea>`;
      } else {
        const type = ["date", "password", "email"].includes(fd.type) ? fd.type : "text";
        const auto = fd.type === "password" ? 'autocomplete="new-password"' : fd.autocomplete ? `autocomplete="${fd.autocomplete}"` : "";
        const mode = fd.type === "number" ? 'inputmode="decimal" style="text-align:right"' : fd.inputmode ? `inputmode="${fd.inputmode}"` : "";
        input = `<input type="${type}" id="f-${fd.f}" data-f="${fd.f}" value="${esc(v)}" ${ro ? "readonly" : ""} ${auto} ${mode}>`;
      }
      return `<div class="${cls}">${label}${input}${help}${err}</div>`;
    }

    function lineCell(c, ln) {
      const ro = locked || c.ro;
      const aria = `aria-label="${esc(c.raw ? c.l : t(c.l))}"`;
      if (c.type === "check") return `<input type="checkbox" data-lf="${c.f}" ${ln[c.f] ? "checked" : ""} ${ro ? "disabled" : ""} ${aria}>`;
      if (c.type === "select") {
        return `<select data-lf="${c.f}" ${ro ? "disabled" : ""} ${aria}>${c.options.map(([ov, ol]) => `<option value="${esc(ov)}" ${String(ln[c.f] == null ? "" : ln[c.f]) === ov ? "selected" : ""}>${esc(c.rawOpt ? ol : t(ol))}</option>`).join("")}</select>`;
      }
      if (c.lookup && !ro) return `<select data-lf="${c.f}" data-lookup="${c.lookup}" ${aria}>${lookupOptions([], ln[c.f])}</select>`;
      return `<input type="${c.type === "date" ? "date" : "text"}" data-lf="${c.f}" value="${esc(ln[c.f])}" ${c.n ? 'inputmode="decimal" data-num="1" style="text-align:right"' : ""} ${ro ? "readonly" : ""} ${aria}>`;
    }

    function linesHtml() {
      const L = R.lines;
      const head = L.cols.map((c) => `<th class="${c.n ? "num" : ""}">${esc(c.raw ? c.l : t(c.l))}</th>`).join("")
        + (L.amount ? `<th class="num">${esc(t(L.amountLabel))}</th>` : "") + (locked ? "" : "<th></th>");
      const body = (model.lines || []).map((ln, i) => `<tr data-line="${i}" class="${L.rowClass ? L.rowClass(ln) : ""}">${L.cols.map((c) => `<td class="${c.w}">${lineCell(c, ln)}</td>`).join("")}
        ${L.amount ? `<td class="num" data-amount>${esc(money(L.amount(ln), cur()))}</td>` : ""}
        ${locked ? "" : `<td><button type="button" class="link-btn" data-remove="${i}" title="${esc(t("common.removeLine"))}">✕</button></td>`}</tr>`).join("");
      const addBtn = locked ? "" : `<button type="button" class="btn small" id="addLine" style="margin-left:auto">＋ ${esc(t("common.addLine"))}</button>`;
      return `<div class="card"><div class="card-head"><h2>${esc(t(L.title || "common.lines"))}</h2>${L.help ? `<span class="help muted">${esc(t(L.help))}</span>` : ""}${addBtn}</div>
        <div class="table-wrap"><table class="grid lines"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>
        ${(model.lines || []).length ? "" : `<div class="empty">${esc(t("common.noLines"))}</div>`}</div>
        ${R.totals ? '<div class="totals" id="totals"></div>' : ""}</div>`;
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
      if (R.lines.amount) {
        $$("tr[data-line]").forEach((tr) => {
          const ln = model.lines[+tr.dataset.line];
          $("[data-amount]", tr).textContent = money(R.lines.amount(ln), cur());
        });
      }
      const totals = $("#totals");
      if (!totals) return;
      const focused = document.activeElement && document.activeElement.id;
      const caret = focused && document.activeElement.selectionStart;
      totals.innerHTML = totalsHtml();
      bindTotals();
      if (focused && focused.startsWith("t-")) { const el = $("#" + focused); el.focus(); try { el.setSelectionRange(caret, caret); } catch (e) { /* ignore */ } }
    }

    function bindTotals() {
      $$("#totals input[data-f]").forEach((el) => el.addEventListener("input", () => { model[el.dataset.f] = numOnly(el); taxLive = true; refreshAmounts(); }));
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
      locked = !!(R.locked && R.locked(model, isNew));
      const title = isNew ? t(R.newTitle) : `${t(R.one)} ${R.label(model)}`;
      const crumbs = `<a href="#${R.route}">${esc(t(R.title))}</a>${R.tabset ? " / " + esc(tabLabel(R)) : ""}`;
      const extra = (R.actions || []).filter((a) => !a.show || a.show(model, isNew))
        .map((a) => `<button class="btn ${a.primary ? "primary" : ""}" data-action="${a.id}">${esc(t(a.l))}</button>`).join("");
      const actions = locked
        ? `<a class="btn" href="#${R.route}">← ${esc(t("common.back"))}</a>${extra}`
        : `<a class="btn" href="#${R.route}">${esc(t("common.cancel"))}</a>
        ${isNew || R.noDelete ? "" : `<button class="btn danger" id="deleteBtn">${esc(t("common.delete"))}</button>`}
        ${extra}<button class="btn primary" id="saveBtn">${esc(t("common.save"))}</button>`;
      const badge = R.badge ? R.badge(model, isNew) : (!isNew && model.cSource ? sourceBadge(model.cSource) : "");
      // Tabs: each section / the lines / the panel says its tab; the tab with an error is opened
      const tabOf = (x) => (R.formTabs ? x.tab || R.formTabs[0][0] : null);
      const wrap = (tab, html) => (R.formTabs && html ? `<div class="ftab" data-tab="${tab}" ${tab === activeTab ? "" : "hidden"}>${html}</div>` : html);
      const tabHasError = (k) => R.sections.some((s) => tabOf(s) === k && s.fields.some((fd) => errors[fd.f]));
      if (R.formTabs && Object.keys(errors).length) {
        const bad = R.sections.find((s) => s.fields.some((fd) => errors[fd.f]));
        if (bad) activeTab = tabOf(bad); else if (errors.lines && R.lines) activeTab = tabOf(R.lines);
      }
      const sections = R.sections.map((s, i) => {
        const fields = s.fields.map(fieldHtml).join("");
        if (!fields) return "";
        return wrap(tabOf(s), `<div class="card"><div class="card-head"><h2>${esc(t(s.t))}</h2>${i === 0 ? badge : ""}</div>
          <div class="card-body">${s.help ? `<p class="help muted section-help">${esc(t(s.help))}</p>` : ""}<div class="form-grid">${fields}</div></div></div>`);
      }).join("");
      const lines = R.lines && (!R.lines.show || R.lines.show(model, isNew)) ? wrap(tabOf(R.lines), linesHtml()) : "";
      const panel = R.panel && !isNew ? wrap(tabOf(R.panel), R.panel.html(model)) : "";
      const present = (sections + lines + panel).match(/data-tab="[^"]+"/g) || [];
      if (R.formTabs && present.length && !present.includes(`data-tab="${activeTab}"`)) activeTab = R.formTabs[0][0];
      const tabBar = R.formTabs ? `<div class="tabs form-tabs" role="tablist">${R.formTabs.filter(([k]) => present.includes(`data-tab="${k}"`))
        .map(([k, l]) => `<a href="#" role="tab" data-ftab="${k}" class="${k === activeTab ? "active" : ""}">${esc(t(l))}${tabHasError(k) ? ' <span class="req">●</span>' : ""}</a>`).join("")}</div>` : "";
      $("#view").innerHTML = pageHead(title, R.sub2 ? R.sub2(model, isNew) : "", actions, crumbs)
        + tabBar + `<form id="form" novalidate>${sections}${lines}</form>${panel}`;
      $$("[data-ftab]").forEach((a) => a.addEventListener("click", (e) => {
        e.preventDefault();
        activeTab = a.dataset.ftab;
        $$("[data-ftab]").forEach((x) => x.classList.toggle("active", x === a));
        $$(".ftab").forEach((d) => { d.hidden = d.dataset.tab !== activeTab; });
      }));
      if ($("#totals")) { $("#totals").innerHTML = totalsHtml(); bindTotals(); }
      bind();
      if (R.panel && R.panel.bind && !isNew) R.panel.bind(model);
      if (R.tax && model[R.tax.supplier]) loadSupplierTax(model[R.tax.supplier]);
    }

    function bind() {
      refreshers = [];
      const refresh = () => refreshers.forEach((f) => f());
      const allFields = R.sections.flatMap((s) => s.fields);
      allFields.forEach((fd) => {
        const el = $(`[data-f="${fd.f}"]`, $("#form"));
        if (!el) return;
        const update = () => {
          model[fd.f] = fd.type === "check" ? el.checked : fd.int ? parseInt(el.value, 10) : fd.type === "number" ? numOnly(el) : el.value;
          if (fd.f === "cDevise" || fd.f === "Devise") refreshAmounts();
          if (fd.rerender) render(); else refresh();
        };
        el.addEventListener(fd.type === "check" || el.tagName === "SELECT" ? "change" : "input", update);
        if (fd.lookup && el.tagName === "SELECT") {
          const fill = bindLookup(el, fd.lookup, (code, label) => {
            model[fd.f] = code;
            if (fd.fill && label) {
              model[fd.fill] = label;
              const target = $(`[data-f="${fd.fill}"]`);
              if (target) target.value = label;
            }
            if (fd.onPick === "fillFromPo") fillFromPo(code);
            if (R.tax && fd.f === R.tax.supplier) { taxLive = true; loadSupplierTax(code); }
          }, fd.lookupParams ? () => fd.lookupParams(model) : null);
          if (fd.lookupParams) refreshers.push(fill);
        }
      });
      if (R.lines) {
        $$("tr[data-line]").forEach((tr) => {
          const ln = model.lines[+tr.dataset.line];
          $$("[data-lf]", tr).forEach((el) => {
            const col = R.lines.cols.find((c) => c.f === el.dataset.lf) || {};
            if (el.type === "checkbox" || el.tagName === "SELECT") {
              el.addEventListener("change", () => { ln[el.dataset.lf] = el.type === "checkbox" ? el.checked : el.value; });
            } else {
              el.addEventListener("input", () => { ln[el.dataset.lf] = el.dataset.num ? numOnly(el) : el.value; taxLive = true; refreshAmounts(); });
            }
            if (el.dataset.lookup) {
              const fill = bindLookup(el, el.dataset.lookup, (code, label) => {
                ln[el.dataset.lf] = code;
                if (col.fill && label) {
                  ln[col.fill] = label;
                  const target = $(`[data-lf="${col.fill}"]`, tr);
                  if (target) target.value = label;
                }
              }, col.lookupParams ? () => col.lookupParams(model) : null);
              if (col.lookupParams) refreshers.push(fill);
            }
          });
        });
        $$("[data-remove]").forEach((b) => b.addEventListener("click", () => { model.lines.splice(+b.dataset.remove, 1); taxLive = true; render(); }));
        const add = $("#addLine");
        if (add) {
          add.addEventListener("click", () => {
            model.lines = model.lines || [];
            model.lines.push(R.lines.newLine ? R.lines.newLine(model) : {});
            render();
            const rows = $$("tr[data-line]");
            const first = rows.length && $("input[data-lf]:not([data-lf=cUnique]):not([readonly])", rows[rows.length - 1]);
            if (first) first.focus();
          });
        }
      }
      $("#form").addEventListener("submit", (e) => { e.preventDefault(); if (!locked) save(); });
      const sv = $("#saveBtn");
      if (sv) sv.addEventListener("click", save);
      const del = $("#deleteBtn");
      if (del) del.addEventListener("click", remove);
      $$("[data-action]").forEach((b) => b.addEventListener("click", async () => {
        const a = R.actions.find((x) => x.id === b.dataset.action);
        if (a.confirm && !confirm(t(a.confirm))) return;
        b.disabled = true;
        try {
          const res = await a.run(model, { path: apiPath() });
          if (res && typeof res === "object") model = res;
          if (a.done) toast(t(a.done), "success");
          render();
        } catch (e) {
          showError(e);
          b.disabled = false;
        }
      }));
    }

    function apiPath() {
      return R.api + "/" + String(id).split("/").map(enc).join("/");
    }

    function showError(e) {
      if (e.field) { errors[e.field] = e.code; render(); }
      let msg = t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic");
      if (e.detail) msg += " (" + e.detail + ")";
      toast(msg, "error");
    }

    async function save() {
      errors = {};
      R.sections.flatMap((s) => s.fields).filter(visible).forEach((fd) => {
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
        showError(e);
      }
    }

    async function remove() {
      if (!confirm(t("common.confirmDelete"))) return;
      try {
        await api(apiPath(), { method: "DELETE" });
        toast(t("common.deleted"), "success");
        location.hash = "#" + R.route;
      } catch (e) { showError(e); }
    }

    return {
      async load() {
        if (isNew) {
          model = Object.assign({}, typeof R.defaults === "function" ? R.defaults() : R.defaults || {});
          if (prefill && prefill.key === key) { Object.assign(model, prefill.values); prefill = null; }
          return;
        }
        try { model = await api(apiPath()); } catch (e) { if (e.status === 404) missing = true; else throw e; }
      },
      render,
    };
  }

  // ---------- My account (change own password)
  // ------------------------------------------------------------------ Administration > Backups
  function backupView() {
    let st = null;
    let busy = false;
    const errText = (e) => (t("err." + e.code) !== "err." + e.code ? t("err." + e.code) : t("err.generic")) + (e.detail ? " — " + e.detail : "");
    const size = (n) => n >= 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB";
    return {
      async load() { st = await api("admin/backup"); },
      render() {
        const s = st.settings, last = st.status || {};
        const num = (id, l, v, help) => `<div class="field"><label for="${id}">${esc(t(l))}<span class="req">*</span></label>
            <input type="text" id="${id}" value="${esc(v)}" inputmode="numeric"><p class="help">${esc(t(help))}</p></div>`;
        const files = st.files.length ? `<table class="grid"><thead><tr><th>${esc(t("bk.files"))}</th><th>${esc(t("bk.date"))}</th>
              <th class="num">${esc(t("bk.size"))}</th><th></th></tr></thead><tbody>
            ${st.files.map((f) => `<tr><td>${esc(f.name)}</td><td>${esc(fmtDateTime(f.date))}</td><td class="num">${esc(size(f.size))}</td>
              <td><a class="btn small" href="api/admin/backup/files/${enc(f.name)}" download>${esc(t("bk.download"))}</a></td></tr>`).join("")}
            </tbody></table>` : `<div class="empty">${esc(t("bk.none"))}</div>`;
        $("#view").innerHTML = pageHead(t("bk.title"), t("bk.subtitle"),
          `<button class="btn primary" id="bkRun" ${busy ? "disabled" : ""}>${esc(t(busy ? "bk.running" : "bk.runNow"))}</button>`) + `
          <div class="card"><div class="card-body">
            <p><strong>${esc(t("bk.last"))}:</strong> ${last.lastSuccess ? esc(fmtDateTime(last.lastSuccess) + " — " + (last.lastFile || "")) : esc(t("bk.never"))}
            &nbsp;·&nbsp; <strong>${esc(t("bk.next"))}:</strong> ${st.nextRun ? esc(fmtDateTime(st.nextRun)) : esc(t("bk.off"))}</p>
            ${last.lastError ? `<p class="badge no">${esc(t("bk.lastError"))} (${esc(fmtDateTime(last.lastRun))}): ${esc(last.lastError)}</p>` : ""}
          </div></div>
          <form class="card" id="bkForm" novalidate><div class="card-head"><h2>${esc(t("bk.settings"))}</h2></div>
            <div class="card-body"><div class="form-grid">
              <div class="field"><label class="check"><input type="checkbox" id="bkEnabled" ${s.enabled ? "checked" : ""}> ${esc(t("bk.enabled"))}</label></div>
              ${num("bkInterval", "bk.interval", s.intervalHours, "bk.interval.help")}
              ${num("bkKeep", "bk.keep", s.keep, "bk.keep.help")}
              <div class="field"><label for="bkPath">${esc(t("bk.path"))}<span class="req">*</span></label>
                <input type="text" id="bkPath" value="${esc(s.path)}"><p class="help">${esc(t("bk.path.help"))}</p></div>
            </div><button type="submit" class="btn primary">${esc(t("common.save"))}</button></div></form>
          <div class="card"><div class="table-wrap">${files}</div><div class="card-body"><p class="help">${esc(t("bk.restore"))}</p></div></div>`;
        $("#bkForm").addEventListener("submit", async (e) => {
          e.preventDefault();
          try {
            st = await api("admin/backup", { method: "PUT", body: { enabled: $("#bkEnabled").checked,
              intervalHours: $("#bkInterval").value, keep: $("#bkKeep").value, path: $("#bkPath").value } });
            toast(t("bk.saved"), "success");
            this.render();
          } catch (err) { toast(errText(err), "error"); }
        });
        $("#bkRun").addEventListener("click", async () => {
          busy = true; this.render();
          try {
            st = await api("admin/backup/run", { method: "POST", body: {} });
            toast(t("bk.done", { name: st.status.lastFile }), "success");
          } catch (err) { toast(errText(err), "error"); await this.load(); }
          busy = false; this.render();
        });
      },
    };
  }

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

  // ------------------------------------------------------------------ Router
  function currentPath() {
    const h = location.hash.replace(/^#/, "");
    return h ? (h.startsWith("/") ? h : "/" + h) : "/";
  }

  // Menu entries that open the first screen of a tab set
  const ALIASES = { "/gl": "gl", "/admin/taxes": "taxcodes" };
  const routeOf = (path) => {
    const norm = "/" + path.split("/").filter(Boolean).join("/");
    if (ALIASES[norm]) return { key: ALIASES[norm], rest: [] };
    const key = Object.keys(RES).filter((k) => norm === RES[k].route || norm.startsWith(RES[k].route + "/"))
      .sort((a, b) => RES[b].route.length - RES[a].route.length)[0];
    return key ? { key, rest: norm.slice(RES[key].route.length).split("/").filter(Boolean) } : null;
  };
  function activeMenuRoute(path) {
    const hit = routeOf(path);
    if (!hit) return path;
    const R = RES[hit.key];
    return R.menu || (R.tabset ? RES[TABSETS[R.tabset][0][0]].menu || RES[TABSETS[R.tabset][0][0]].route : R.route);
  }

  function resolve(path) {
    const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
    if (!parts.length) return dashboardView();
    if (parts[0] === "account") return accountView();
    if (parts.join("/") === "admin/backups") return isAdmin() ? backupView() : dashboardView();
    if (parts.join("/") === "inv/replenishment") return replenishmentView();
    const hit = routeOf(parts.join("/"));
    if (!hit) return dashboardView();
    const R = RES[hit.key];
    if (R.admin && !isAdmin()) return dashboardView();
    if (!hit.rest.length) return listView(hit.key);
    if (hit.rest[0] === "new" && !R.noNew) return formView(hit.key, null);
    return formView(hit.key, hit.rest.join("/"));
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
