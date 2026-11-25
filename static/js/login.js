/* PowerERP: Login screen, language, entering the app. */
import { $, I18N, api, lang, setLangValue, setUnauthorizedHandler, t } from "./core.js";
import { applyStaticI18n, renderSidebar } from "./menu.js";
import { route } from "./router.js";
import { setUser, setView, user, view } from "./state.js";

// ------------------------------------------------------------------ Login
export function setLang(l, remember) {
  if (!I18N[l]) return;
  setLangValue(l);
  try { localStorage.setItem("erp.lang", lang); } catch (e) { /* ignore */ }
  applyStaticI18n();
  if (user) {
    renderSidebar();
    if (view) view.render();
    if (remember) api("auth/lang", { method: "POST", body: { lang } }).catch(() => {});
  }
}

export function showUser() {
  const initials = (user.name || user.username).split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  $("#userAvatar").textContent = initials;
  $("#userName").textContent = user.name || user.username;
  $("#userLink").title = t("acc.title");
}

export function showLogin() {
  setUser(null);
  setView(null);
  document.body.classList.add("logged-out");
  $("#login").hidden = false;
  $("#loginError").hidden = true;
  $("#loginPass").value = "";
  setTimeout(() => $("#loginUser").focus(), 0);
}

export let langPicked = false; // language chosen on the login screen: saved to the user instead of the stored one
export function enterApp(u) {
  setUser(u);
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
    err.textContent = ex.code === "locked" ? t("auth.locked", { n: ex.detail || "15" }) : t(ex.code === "bad_login" ? "auth.bad" : "err.generic");
    err.hidden = false;
    $("#loginPass").select();
  }
});

$("#logoutBtn").addEventListener("click", async () => {
  try { await api("auth/logout", { method: "POST", noAuthRedirect: true }); } catch (e) { /* ignore */ }
  showLogin();
  history.replaceState(null, "", "#/");
});


export function setLangPicked(v) { langPicked = v; }

setUnauthorizedHandler(showLogin);
