/* PowerERP: Access levels of a screen (Administration > Roles). No DOM here: tests/js/access.test.mjs runs it.

A role stores permissions "<screen>:<action>". The Roles screen shows each screen with one level:
  none  no permission
  view  view (+ print where the screen prints)
  edit  view, create, edit (+ print)
  full  every action of the screen (delete, post, credit note, approve, create PO…)
  custom  any other set, picked action by action
*/

export const LEVELS = ["none", "view", "edit", "full"];
const LEVEL_ACTIONS = { none: [], view: ["view", "print"], edit: ["view", "create", "edit", "print"] };

// The actions of a level on a screen (only those the screen has).
export function actionsOf(level, screenActions) {
  if (level === "full") return [...screenActions];
  return screenActions.filter((a) => (LEVEL_ACTIONS[level] || []).includes(a));
}

// The levels worth offering on a screen: those that give a different set (a view-only screen: none / view).
export function levelsOf(screenActions) {
  const seen = new Set();
  return LEVELS.filter((l) => {
    const k = actionsOf(l, screenActions).join(",");
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

// The level of the actions a role has on a screen ("custom" when no level matches).
export function levelOf(has, screenActions) {
  const set = new Set(has);
  const own = screenActions.filter((a) => set.has(a));
  for (const l of [...levelsOf(screenActions)].reverse()) {
    const want = actionsOf(l, screenActions);
    if (want.length === own.length && want.every((a) => set.has(a))) return l;
  }
  return "custom";
}

// The permissions of a role as { screen: [actions] }, and back.
export function byScreen(permissions) {
  const out = {};
  for (const p of permissions || []) {
    const [s, a] = p.split(":");
    (out[s] = out[s] || []).push(a);
  }
  return out;
}
export function toPermissions(map, catalog) {
  return catalog.flatMap((c) => c.actions.filter((a) => (map[c.cScreen] || []).includes(a)).map((a) => `${c.cScreen}:${a}`));
}

// An action needs the view of its screen; taking the view away takes every action.
export function toggleAction(has, action, on) {
  const set = new Set(has);
  if (on) { set.add(action); set.add("view"); } else if (action === "view") set.clear(); else set.delete(action);
  return [...set];
}

// The summary of a module: the common level of its screens, else "k of n" screens opened.
export function moduleSummary(map, screens) {
  const levels = screens.map((c) => levelOf(map[c.cScreen] || [], c.actions));
  // every screen at its top level (a view-only screen tops at "view"): the module is "full"
  if (levels.every((l, i) => l !== "none" && l === levelsOf(screens[i].actions).at(-1))) return { level: "full" };
  if (levels.every((l) => l === levels[0])) return { level: levels[0] };
  return { open: levels.filter((l) => l !== "none").length, total: screens.length };
}
