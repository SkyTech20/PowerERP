"""The UI files: the page loads the ES modules, served with a JavaScript type, and every import resolves."""

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "static"


def test_index_loads_the_entry_module(client):
    html = client.get("/").get_data(as_text=True)
    assert '<script type="module" src="assets/js/main.js"></script>' in html


def test_modules_are_served_as_javascript(client):
    for path in sorted((STATIC / "js").rglob("*.js")):
        res = client.get("/assets/" + path.relative_to(STATIC).as_posix())
        assert res.status_code == 200, path
        assert res.mimetype == "text/javascript", path  # browsers refuse modules sent as text/plain


def test_every_import_points_to_an_existing_export():
    files = {p: p.read_text(encoding="utf-8") for p in (STATIC / "js").rglob("*.js")}
    exports = {
        p: set(re.findall(r"^export (?:async )?(?:function|const|let) ([\w$]+)", text, re.M))
        for p, text in files.items()
    }
    for path, text in files.items():
        for names, target in re.findall(r'^import \{ ([^}]+) \} from "([^"]+)";', text, re.M):
            module = (path.parent / target).resolve()
            assert module in exports, (path.name, target)
            missing = {n.strip() for n in names.split(",")} - exports[module]
            assert not missing, (path.name, target, missing)


def _messages():
    """The keys of the English and French texts, from every translation file."""
    keys = {"en": set(), "fr": set()}
    for path in sorted(STATIC.glob("i18n*.js")):
        text = path.read_text(encoding="utf-8")
        split = re.search(r"^\s*(?:Object\.assign\(I\.fr, \{|fr: \{)", text, re.M)
        assert split, path.name
        keys["en"] |= set(re.findall(r'^\s*"([\w.]+)":', text[: split.start()], re.M))
        keys["fr"] |= set(re.findall(r'^\s*"([\w.]+)":', text[split.start() :], re.M))
    return keys


def test_every_server_error_has_a_message_in_both_languages():
    # without one, the user only sees "Something went wrong" and cannot tell which field to fix
    root = STATIC.parent / "powererp"
    codes = set()
    for path in root.rglob("*.py"):
        codes |= set(re.findall(r'AppError\(\s*"([a-z0-9_]+)"', path.read_text(encoding="utf-8")))
    assert len(codes) > 40
    keys = _messages()
    for lang in ("en", "fr"):
        missing = sorted(c for c in codes if "err." + c not in keys[lang])
        assert not missing, (lang, missing)
