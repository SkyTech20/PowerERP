"""The help of the screens: the Markdown files of help/<lang>/<screen>.md, read once into items.

Each heading carries the fixed code of its item, the same in every language:

    # Invoices {#sales.invoices}                 the screen (the file name, = the menu / permission key)
    ## Post {#sales.invoices.post}               an action (an action of the screen in permissions.py)
    ### Customer {#sales.invoices.cCustomer}     a field (its name in the form, data-f)
    ### Quantity {#sales.invoices.lines.dQty}    a column of a grid (<screen>.<grid>.<field>)
    ## Lines {#sales.invoices.lines}             any other section

Another tab of a tab set puts the resource in its codes: admin.taxes.taxgroups.cCode (static/js/helpui.js).

The text under a heading, down to the next heading, is the body of the item. A link to another item is written
[Post](#sales.invoices.post); it opens that item in the Help screen.

Who sees an item: the screen's view permission (an administrator-only screen: the administrator; the general
pages, whose file name starts with "_": everybody), and for an action item the permission of that action too.
"""

from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from markdown_it import MarkdownIt

from powererp.core.permissions import SCREEN_BY_KEY, SCREENS

LANGS = ("en", "fr")
DEFAULT_LANG = "en"

# Screens of the administrator role only (not in permissions.SCREENS: their routes are ADMIN_ENDPOINTS)
ADMIN_SCREENS = ("admin.users", "admin.roles", "admin.audit", "admin.privacy", "admin.backups", "admin.settings")
# The order of the table of contents: the general pages, then the menu order
ORDER = [s.key for s in SCREENS] + list(ADMIN_SCREENS)

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*(?:\{#([^}\s]*)\})?\s*$")
CODE = re.compile(r"^_?[a-z][a-zA-Z0-9]*(\.[a-zA-Z][a-zA-Z0-9_-]*)*$")
FENCE = re.compile(r"^\s*(```|~~~)")
LINK = re.compile(r"\]\(#([^)\s]+)\)")

_md = MarkdownIt("commonmark", {"html": False}).enable("table")


@dataclass
class Item:
    code: str
    screen: str
    lang: str
    level: int
    title: str
    body: str  # Markdown
    order: int
    path: list[str] = field(default_factory=list)  # titles of the parent headings
    html: str = ""
    text: str = ""  # plain text of the body (search, snippets)


@dataclass
class HelpIndex:
    items: dict[str, dict[str, Item]]  # lang -> code -> item
    problems: list[str]  # files that break the rules (tests/test_help.py fails on any)

    # ------------------------------------------------------------------ access
    @staticmethod
    def permission(code: str) -> tuple[str, str] | None:
        """(screen, action) an item needs; None for the general pages (everybody)."""
        screen = screen_of(code)
        if screen.startswith("_"):
            return None
        rest = code[len(screen) + 1 :]
        s = SCREEN_BY_KEY.get(screen)
        if s is not None and rest in s.actions:
            return screen, rest
        return screen, "view"

    def visible(self, code: str, can: Callable[[str], bool], is_admin: bool) -> bool:
        need = self.permission(code)
        if need is None or is_admin:
            return True
        screen, action = need
        if screen not in SCREEN_BY_KEY:
            return False  # an administrator-only screen
        return can(f"{screen}:view") and can(f"{screen}:{action}")

    # ------------------------------------------------------------------ reading
    def item(self, code: str, lang: str) -> tuple[Item, bool] | None:
        """The item in this language, or in English when it is not translated yet (second value True)."""
        own = self.items.get(lang, {}).get(code)
        if own is not None:
            return own, False
        en = self.items.get(DEFAULT_LANG, {}).get(code)
        return (en, lang != DEFAULT_LANG) if en is not None else None

    def screens(self) -> list[str]:
        """Every documented screen, general pages first, then in menu order."""
        found = {i.screen for by_code in self.items.values() for i in by_code.values()}
        rank = {k: n for n, k in enumerate(ORDER)}
        return sorted(found, key=lambda s: (not s.startswith("_"), rank.get(s, len(rank)), s))

    def page(self, screen: str, lang: str) -> list[tuple[Item, bool]]:
        """The items of a screen, in the order of the file (English order; a translated file may add none)."""
        codes = [i.code for i in self.items.get(DEFAULT_LANG, {}).values() if i.screen == screen]
        if not codes:  # a page written in French only
            codes = [i.code for i in self.items.get(lang, {}).values() if i.screen == screen]
        found = [self.item(c, lang) for c in codes]
        return sorted((f for f in found if f is not None), key=lambda f: f[0].order)

    def search(self, query: str, lang: str, limit: int = 30) -> list[tuple[Item, bool, int]]:
        """Items holding every word of the query (accents and case ignored): title first, then code, then text."""
        words = [w for w in fold(query).split() if w]
        if not words:
            return []
        codes = {c for by_code in self.items.values() for c in by_code}
        hits = []
        for code in codes:
            found = self.item(code, lang)
            if found is None:
                continue
            it, fallback = found
            title, ident, body = fold(it.title), fold(it.code), fold(it.text)
            score = 0
            for w in words:
                s = (5 if w in title else 0) + (4 if w in ident else 0) + (1 if w in body else 0)
                if not s:
                    break
                score += s
            else:
                hits.append((it, fallback, score))
        rank = {k: n for n, k in enumerate(self.screens())}
        hits.sort(key=lambda h: (-h[2], rank.get(h[0].screen, 0), h[0].order))
        return hits[:limit]


def fold(s: str) -> str:
    """Lower case, without accents (é -> e)."""
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def screen_of(code: str) -> str:
    """The screen of an item code: the longest known screen key it starts with, else its first two parts."""
    if code.startswith("_"):
        return code.split(".")[0]
    for key in sorted(ORDER, key=len, reverse=True):
        if code == key or code.startswith(key + "."):
            return key
    return ".".join(code.split(".")[:2])


def snippet(text: str, query: str, size: int = 160) -> str:
    """A line of the text around the first word of the query found in it."""
    words = [w for w in fold(query).split() if w]
    folded = fold(text)
    at = min((folded.find(w) for w in words if w in folded), default=0)
    start = max(0, at - size // 3)
    cut = text[start : start + size].strip()
    return ("… " if start else "") + cut + (" …" if start + size < len(text) else "")


def summary(text: str, size: int = 200) -> str:
    """The first sentence of a text (the tip of the ⓘ of a field)."""
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    first = m.group(1) if m else text
    return first if len(first) <= size else first[: size - 2].rstrip() + " …"


def render(body: str) -> tuple[str, str]:
    """HTML (raw HTML in the Markdown is not allowed) and plain text of a body."""
    out = _md.render(LINK.sub(lambda m: f"](#/help/{m.group(1)})", body))
    plain = html.unescape(re.sub(r"<[^>]+>", " ", out))
    return out, re.sub(r"\s+", " ", plain).strip()


def parse(text: str, screen: str, lang: str, problems: list[str]) -> list[Item]:
    """The items of one file."""
    where = f"help/{lang}/{screen}.md"
    items: list[Item] = []
    parents: list[Item] = []
    body: list[str] = []
    fenced = False

    def close() -> None:
        if items:
            items[-1].body = "\n".join(body).strip()
        body.clear()

    for n, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fenced = not fenced
        m = None if fenced else HEADING.match(line)
        if m is None:
            if items:
                body.append(line)
            elif line.strip():
                problems.append(f"{where}:{n}: text before the first heading")
            continue
        close()
        level, title, code = len(m.group(1)), m.group(2), m.group(3) or ""
        if not code:
            problems.append(f"{where}:{n}: heading without a code {{#...}}: {title}")
            continue
        if not CODE.match(code):
            problems.append(f"{where}:{n}: invalid code {code}")
            continue
        if not items and (level != 1 or code != screen):
            problems.append(f"{where}:{n}: the file must start with '# <title> {{#{screen}}}'")
        if items and (level == 1 or not (code == screen or code.startswith(screen + "."))):
            problems.append(f"{where}:{n}: code {code} does not belong to the screen {screen}")
        while parents and parents[-1].level >= level:
            parents.pop()
        it = Item(code, screen, lang, level, title, "", len(items), [p.title for p in parents])
        items.append(it)
        parents.append(it)
    close()
    for it in items:
        it.html, it.text = render(it.body)
    return items


def load(root: Path, langs: Iterable[str] = LANGS) -> HelpIndex:
    """Every help file under root (help/<lang>/<screen>.md)."""
    items: dict[str, dict[str, Item]] = {}
    problems: list[str] = []
    for lang in langs:
        by_code = items.setdefault(lang, {})
        folder = root / lang
        for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            screen = path.stem
            if not screen.startswith("_") and screen not in ORDER:
                problems.append(f"help/{lang}/{path.name}: not a screen of the menu (permissions.py)")
            for it in parse(path.read_text(encoding="utf-8"), screen, lang, problems):
                if it.code in by_code:
                    problems.append(f"help/{lang}/{path.name}: code {it.code} used twice")
                    continue
                by_code[it.code] = it
    en = items.get(DEFAULT_LANG, {})
    for lang, by_code in items.items():
        for it in by_code.values():
            for target in LINK.findall(it.body):
                if target not in by_code and target not in en:
                    problems.append(f"help/{lang}/{it.screen}.md: link to an unknown item #{target} ({it.code})")
        if lang == DEFAULT_LANG:
            continue
        for screen in {i.screen for i in by_code.values()}:
            ours = {c for c, i in by_code.items() if i.screen == screen}
            theirs = {c for c, i in en.items() if i.screen == screen}
            for c in sorted(theirs ^ ours):
                side = "English" if c in theirs else lang
                problems.append(f"help/{lang}/{screen}.md: code {c} only in the {side} file")
    return HelpIndex(items, problems)
