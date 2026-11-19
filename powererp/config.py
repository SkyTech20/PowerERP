"""Settings read from the environment."""
import os

# Local development database (docker-compose.yml in this folder publishes PostgreSQL on port 5433).
DEFAULT_DATABASE_URL = "postgresql+psycopg://powererp:powererp@localhost:5433/powererp"


def database_url(url=None):
    """DATABASE_URL, normalized for SQLAlchemy + psycopg 3 (postgres:// and postgresql:// are accepted)."""
    url = (url or os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL).strip()
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def masked(url):
    """The URL without its password, for logs."""
    head, sep, tail = url.rpartition("@")
    if not sep:
        return url
    scheme, _, cred = head.partition("://")
    user = cred.split(":", 1)[0]
    return f"{scheme}://{user}:***@{tail}"
