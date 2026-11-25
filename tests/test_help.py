"""Help (H1): the manual of the screens in help/<lang>/<screen>.md, its rules, and what each role sees of it."""

from pathlib import Path

import pytest

from powererp.modules.manual import HELP_DIR
from powererp.modules.manual.content import load, screen_of

FILE = """# Invoices {#sales.invoices}
Intro with a link to [Post](#sales.invoices.post).

## Header {#sales.invoices.header}

### Customer {#sales.invoices.cCustomer}
The customer billed.

## Post {#sales.invoices.post}
Posts. Prix, référence.

```
# not a heading {#inside.a.fence}
```
"""


def _write(root: Path, lang: str, name: str, text: str) -> None:
    (root / lang).mkdir(parents=True, exist_ok=True)
    (root / lang / name).write_text(text, encoding="utf-8")


# ------------------------------------------------------------------ the files
def test_the_help_files_follow_the_rules():
    index = load(HELP_DIR)
    assert index.problems == []
    assert "sales.invoices" in index.screens()
    # the same codes in English and French
    en = {c for c in index.items["en"]}
    fr = {c for c in index.items["fr"]}
    assert en == fr


def test_items_of_a_file(tmp_path):
    _write(tmp_path, "en", "sales.invoices.md", FILE)
    index = load(tmp_path)
    assert index.problems == []
    items = index.items["en"]
    assert list(items) == ["sales.invoices", "sales.invoices.header", "sales.invoices.cCustomer", "sales.invoices.post"]
    assert items["sales.invoices.cCustomer"].path == ["Invoices", "Header"]
    assert items["sales.invoices.cCustomer"].level == 3
    assert 'href="#/help/sales.invoices.post"' in items["sales.invoices"].html  # a link to an item opens the Help
    assert "inside.a.fence" in items["sales.invoices.post"].body  # a fenced block is text, not a heading


def test_raw_html_is_not_rendered(tmp_path):
    _write(tmp_path, "en", "sales.invoices.md", "# Invoices {#sales.invoices}\n<script>alert(1)</script>\n")
    html = load(tmp_path).items["en"]["sales.invoices"].html
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_broken_files_are_reported(tmp_path):
    _write(
        tmp_path,
        "en",
        "sales.invoices.md",
        "# Invoices {#sales.invoices}\n## No code\n## Post {#sales.invoices.post}\nSee [x](#sales.invoices.nothing)\n"
        "## Again {#sales.invoices.post}\n## Other {#sales.customers.cCode}\n",
    )
    _write(tmp_path, "en", "nothing.here.md", "# Nothing {#nothing.here}\n")
    _write(tmp_path, "fr", "sales.invoices.md", "# Factures {#sales.invoices}\n## Extra {#sales.invoices.extra}\n")
    problems = "\n".join(load(tmp_path).problems)
    assert "heading without a code" in problems
    assert "code sales.invoices.post used twice" in problems
    assert "does not belong to the screen" in problems
    assert "link to an unknown item #sales.invoices.nothing" in problems
    assert "nothing.here.md: not a screen" in problems
    assert "code sales.invoices.extra only in the fr file" in problems
    assert "code sales.invoices.post only in the English file" in problems


def test_an_item_not_translated_shows_the_english_text(tmp_path):
    _write(tmp_path, "en", "sales.invoices.md", FILE)
    index = load(tmp_path)
    it, fallback = index.item("sales.invoices.post", "fr")
    assert it.lang == "en" and fallback
    assert [i.code for i, _fb in index.page("sales.invoices", "fr")][0] == "sales.invoices"


def test_search_ignores_accents_and_case(tmp_path):
    _write(tmp_path, "en", "sales.invoices.md", FILE)
    index = load(tmp_path)
    assert [h[0].code for h in index.search("REFERENCE prix", "en")] == ["sales.invoices.post"]
    assert index.search("customer", "en")[0][0].code == "sales.invoices.cCustomer"  # the title first
    assert [h[0].code for h in index.search("cCustomer", "en")] == ["sales.invoices.cCustomer"]  # by its code
    assert index.search("   ", "en") == []


def test_summary_is_the_first_sentence():
    from powererp.modules.manual.content import summary

    assert summary("Price × (1 − discount %). Calculated.") == "Price × (1 − discount %)."
    assert summary("No end") == "No end"
    assert summary("x" * 300).endswith(" …") and len(summary("x" * 300)) <= 200


def test_screen_and_permission_of_a_code():
    assert screen_of("sales.invoices.lines.dQty") == "sales.invoices"
    assert screen_of("_intro.find") == "_intro"
    assert screen_of("admin.roles.cCode") == "admin.roles"
    index = load(HELP_DIR)
    assert index.permission("sales.invoices.post") == ("sales.invoices", "post")
    assert index.permission("sales.invoices.credit") == ("sales.invoices", "credit")
    assert index.permission("sales.invoices.cCustomer") == ("sales.invoices", "view")
    assert index.permission("_intro.find") is None


# ------------------------------------------------------------------ the API and the roles
@pytest.fixture
def login(app, admin):
    """login(perms) -> a client logged in as a new user whose role has exactly these permissions."""
    from powererp import database
    from powererp.models import Role, RolePermission

    count = {"n": 0}

    def make(perms):
        count["n"] += 1
        code, name = f"H{count['n']}", f"help{count['n']}"
        with database.session_scope() as s:
            s.add(Role(code=code, desc_fr=code, desc_en=code, active=True, is_admin=False))
            s.flush()
            s.add_all(RolePermission(role_code=code, permission=p) for p in perms)
        r = admin.post("/api/users", json={"username": name, "name": name, "role": code, "password": "secret1"})
        assert r.status_code == 201, r.get_json()
        c = app.test_client()
        assert c.post("/api/auth/login", json={"username": name, "password": "secret1"}).status_code == 200
        return c

    return make


def test_needs_a_login(anon):
    assert anon.get("/api/help/toc").status_code == 401


def test_the_administrator_sees_every_page(admin):
    toc = admin.get("/api/help/toc?lang=fr").get_json()
    assert toc["lang"] == "fr"
    screens = [s["screen"] for s in toc["screens"]]
    assert screens[0] == "_intro" and "sales.invoices" in screens
    inv = next(s for s in toc["screens"] if s["screen"] == "sales.invoices")
    assert inv["title"] == "Factures clients"
    assert inv["summary"].startswith("Les factures et notes de crédit")  # the card of the home page
    assert {"code": "sales.invoices.buttons", "title": "Boutons"} in inv["sections"]  # the level-2 headings
    page = admin.get("/api/help/page/sales.invoices?lang=en").get_json()
    codes = [i["code"] for i in page["items"]]
    assert codes[0] == "sales.invoices" and "sales.invoices.post" in codes and "sales.invoices.credit" in codes
    item = admin.get("/api/help/item/sales.invoices.lines.lReturn?lang=en").get_json()
    assert item["screen"] == "sales.invoices" and item["path"] == ["Sales invoices", "Lines"]
    assert item["untranslated"] is False
    assert item["summary"].startswith("Credit notes only.")  # the tip of the field's ⓘ
    assert admin.get("/api/help/page/nothing").status_code == 404
    assert admin.get("/api/help/item/sales.invoices.nothing").status_code == 404


def test_an_unknown_language_is_english(admin):
    assert admin.get("/api/help/toc?lang=pt").get_json()["lang"] == "en"


def test_a_role_without_the_screen_sees_only_the_general_pages(login):
    c = login(["inv.items:view"])
    screens = [s["screen"] for s in c.get("/api/help/toc").get_json()["screens"]]
    assert screens == ["_intro"]
    assert c.get("/api/help/page/sales.invoices").status_code == 404
    assert c.get("/api/help/item/sales.invoices.cCustomer").status_code == 404
    assert c.get("/api/help/item/_intro.find").status_code == 200
    found = [i["screen"] for i in c.get("/api/help/search?q=invoice").get_json()["items"]]
    assert found and set(found) == {"_intro"}


def test_a_role_sees_only_the_actions_it_has(login):
    c = login(["sales.invoices:view", "sales.invoices:create", "sales.invoices:edit", "sales.invoices:post"])
    codes = [i["code"] for i in c.get("/api/help/page/sales.invoices").get_json()["items"]]
    assert "sales.invoices.post" in codes and "sales.invoices.cCustomer" in codes
    assert "sales.invoices.credit" not in codes and "sales.invoices.delete" not in codes
    assert c.get("/api/help/item/sales.invoices.credit").status_code == 404
    found = [i["code"] for i in c.get("/api/help/search?q=credit note").get_json()["items"]]
    assert found and "sales.invoices.credit" not in found


def test_search(admin):
    res = admin.get("/api/help/search?q=prix minimum&lang=fr").get_json()
    first = res["items"][0]
    assert first["code"] == "sales.invoices.lines.dNetPrice"
    assert first["path"] == ["Factures clients", "Lignes"]
    assert "minimum" in first["snippet"].lower()
    assert admin.get("/api/help/search?q=sales.invoices.post").get_json()["items"][0]["code"] == "sales.invoices.post"
    assert admin.get("/api/help/search?q=").get_json()["items"] == []
