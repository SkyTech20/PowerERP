"""Who is acting: the user name written on documents and movements."""

from __future__ import annotations


def current_username(outside_request: str = "system", without_user: str = "api") -> str:
    """The logged-in user's name; `without_user` for a call with the API key; `outside_request` at start-up."""
    from powererp.modules.auth import current_user  # the login module keeps the session

    try:
        user = current_user()
    except RuntimeError:  # outside a request (seed)
        return outside_request
    return user["username"] if user else without_user


def current_is_admin(outside_request: bool = True) -> bool:
    """Administrator rights: a logged-in administrator, a call with the API key, or the start-up."""
    from powererp.modules.auth import api_key_ok, current_user

    try:
        if api_key_ok():
            return True
        user = current_user()
    except RuntimeError:  # outside a request (seed)
        return outside_request
    return bool(user) and bool(user["is_admin"])


def current_can(permission: str, outside_request: bool = True) -> bool:
    """A permission ("<screen>:<action>") of the logged-in user's role; the API key and the start-up have all."""
    from powererp.modules.auth import api_key_ok, current_user

    try:
        if api_key_ok():
            return True
        user = current_user()
    except RuntimeError:  # outside a request (seed)
        return outside_request
    return bool(user) and (bool(user["is_admin"]) or permission in user["permissions"])
