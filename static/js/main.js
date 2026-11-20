/* PowerERP: PowerERP single page app: entry point (ES modules, no build step). */
import "./resources/erp.js";
import "./resources/inventory.js";
import { $, $$, api } from "./core.js";
import { enterApp, setLang, setLangPicked, showLogin } from "./login.js";
import { applyStaticI18n } from "./menu.js";
import { route } from "./router.js";
import { user } from "./state.js";

// ------------------------------------------------------------------ Boot
$$(".lang-switch button").forEach((b) => b.addEventListener("click", () => {
  if (!user) setLangPicked(true);
  setLang(b.dataset.lang, true);
}));
$("#menuToggle").addEventListener("click", () => document.body.classList.toggle("nav-open"));
window.addEventListener("hashchange", () => { if (user) route(); });
applyStaticI18n();
api("auth/me", { noAuthRedirect: true }).then(enterApp).catch(showLogin);
