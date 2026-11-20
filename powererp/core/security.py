"""Who is acting: the user name written on documents and movements."""

from __future__ import annotations


def current_username(outside_request: str = "system", without_user: str = "api") -> str:
    """The logged-in user's name; `without_user` for a call with the API key; `outside_request` at start-up."""
    from auth import current_user  # the login module (auth.py) keeps the session

    try:
        user = current_user()
    except RuntimeError:  # outside a request (seed)
        return outside_request
    return user["username"] if user else without_user
