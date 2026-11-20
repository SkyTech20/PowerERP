"""Unit tests of the user rules that need no database."""

import pytest

from powererp.modules.auth.service import AuthError, UserService, check_password, public


def test_user_payload_rules():
    row = UserService.from_payload({"username": " bob ", "name": "Bob", "role": "", "lang": "de", "active": "on"})
    assert row == {"username": "bob", "name": "Bob", "email": "", "role": "user", "lang": "en", "active": True}
    kept = UserService.from_payload({"username": "other", "name": "B"}, existing={"username": "bob"})
    assert kept["username"] == "bob"  # the user name never changes
    for payload, field in (({"name": "x"}, "username"), ({"username": "x"}, "name")):
        with pytest.raises(AuthError) as e:
            UserService.from_payload(payload)
        assert e.value.field == field
    with pytest.raises(AuthError):
        UserService.from_payload({"username": "x", "name": "x", "role": "root"})


def test_password_length():
    check_password("123456")
    with pytest.raises(AuthError) as e:
        check_password("12345", "current")
    assert (e.value.code, e.value.field) == ("password_short", "current")


def test_public_view_has_no_password_hash():
    row = {
        "id": 1,
        "username": "a",
        "name": "A",
        "email": "",
        "role": "user",
        "lang": "fr",
        "active": 1,
        "password_hash": "x",
        "created_at": None,
        "last_login": None,
    }
    assert "password_hash" not in public(row) and public(row)["active"] is True
