"""Manual module: the help of the screens, inside the ERP (Help screen, the "?" of each screen).

The text is in help/<lang>/<screen>.md (see content.py for the format and the item codes). It is read once at
start-up; every route answers only with the items the logged-in user's role may see.

    GET /api/help/toc?lang=en              the documented screens and their sections
    GET /api/help/page/<screen>?lang=en    the items of one screen
    GET /api/help/item/<code>?lang=en      one item (and the screen it is in)
    GET /api/help/search?q=...&lang=en     the items found
"""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, Flask, jsonify, request

from powererp.container import Container
from powererp.core.errors import NotFound
from powererp.core.security import current_can, current_is_admin

from .content import DEFAULT_LANG, LANGS, HelpIndex, Item, load, snippet, summary

HELP_DIR = Path(__file__).resolve().parent.parent.parent.parent / "help"

__all__ = ["HELP_DIR", "HelpIndex", "load", "register"]


def _lang() -> str:
    lang = (request.args.get("lang") or "").lower()
    return lang if lang in LANGS else DEFAULT_LANG


def _item(it: Item, fallback: bool) -> dict:
    return {
        "code": it.code,
        "screen": it.screen,
        "level": it.level,
        "title": it.title,
        "path": it.path,
        "html": it.html,
        "summary": summary(it.text),
        "lang": it.lang,
        "untranslated": fallback,
    }


def _blueprint(index: HelpIndex) -> Blueprint:
    bp = Blueprint("help", __name__)

    def visible(code: str) -> bool:
        return index.visible(code, lambda p: current_can(p, False), current_is_admin(False))

    @bp.route("/api/help/toc")
    def help_toc():
        lang, out = _lang(), []
        for screen in index.screens():
            if not visible(screen):
                continue
            items = [(it, fb) for it, fb in index.page(screen, lang) if visible(it.code)]
            top, sections = items[0][0], [it for it, _fb in items[1:] if it.level == 2]
            out.append(
                {
                    "screen": screen,
                    "title": top.title,
                    "summary": summary(top.text),
                    "sections": [{"code": s.code, "title": s.title} for s in sections],
                }
            )
        return jsonify({"lang": lang, "screens": out})

    @bp.route("/api/help/page/<screen>")
    def help_page(screen):
        lang = _lang()
        items = [_item(it, fb) for it, fb in index.page(screen, lang) if visible(it.code)]
        if not items or items[0]["code"] != screen:
            raise NotFound()
        return jsonify({"screen": screen, "lang": lang, "items": items})

    @bp.route("/api/help/item/<code>")
    def help_item(code):
        found = index.item(code, _lang())
        if found is None or not visible(code):
            raise NotFound()
        return jsonify(_item(*found))

    @bp.route("/api/help/search")
    def help_search():
        q, lang = (request.args.get("q") or "").strip(), _lang()
        hits = [h for h in index.search(q, lang, limit=200) if visible(h[0].code)][:30]
        return jsonify(
            {
                "q": q,
                "lang": lang,
                "items": [
                    {
                        "code": it.code,
                        "screen": it.screen,
                        "title": it.title,
                        "path": it.path,
                        "snippet": snippet(it.text, q),
                        "untranslated": fb,
                    }
                    for it, fb, _score in hits
                ],
            }
        )

    return bp


def register(app: Flask, c: Container, root: Path = HELP_DIR) -> HelpIndex:
    index = c.register("help", load(root))
    app.register_blueprint(_blueprint(index))
    return index
