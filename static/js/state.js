/* PowerERP: State shared by the screens: the logged-in user, the screen shown, defaults for the next new form, lookup cache. */

export let user = null; // logged-in user (GET api/auth/me)
export let view = null; // the screen shown (an object with load() and render())
export let prefill = null; // { key, values }: defaults for the next "new" form (e.g. a movement for this product)
export const lookupCache = {};
export const isAdmin = () => !!user && !!user.isAdmin;
// A permission of the user's role ("<screen>:<action>", powererp/core/permissions.py); the server checks it again.
export const can = (screen, action = "view") => isAdmin() || (!!user && (user.permissions || []).includes(`${screen}:${action}`));
export function setUser(u) { user = u; }
export function setView(v) { view = v; }
export function setPrefill(p) { prefill = p; }
export function clearLookups() { Object.keys(lookupCache).forEach((k) => delete lookupCache[k]); }

// The tab a form opens on (e.g. back from a location to the Locations tab of its warehouse), used once
export let formTab = null;
export function setFormTab(v) { formTab = v; }
