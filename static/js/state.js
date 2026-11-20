/* PowerERP: State shared by the screens: the logged-in user, the screen shown, defaults for the next new form, lookup cache. */

export let user = null; // logged-in user (GET api/auth/me)
export let view = null; // the screen shown (an object with load() and render())
export let prefill = null; // { key, values }: defaults for the next "new" form (e.g. a movement for this product)
export const lookupCache = {};
export const isAdmin = () => !!user && user.role === "admin";
export function setUser(u) { user = u; }
export function setView(v) { view = v; }
export function setPrefill(p) { prefill = p; }
export function clearLookups() { Object.keys(lookupCache).forEach((k) => delete lookupCache[k]); }
