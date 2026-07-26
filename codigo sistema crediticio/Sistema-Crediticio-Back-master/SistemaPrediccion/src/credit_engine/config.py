"""Configuration — loads ``.env`` and builds the database connection URL.

The ``.env`` file lives next to this module (one directory above ``main.py``).
On startup ``main.py`` calls ``load_env()``, which reads the file and constructs
``CREDIT_ENGINE_DATABASE_URL`` as an environment variable so the lifespan
handler in ``main.py`` can pick it up unchanged.

The constructed URL uses **``mssql+pyodbc``** (ODBC Driver 18 for SQL Server).
If you prefer **``mssql+pymssql``** (no system ODBC driver needed, but slower),
pass it explicitly before startup::

    set CREDIT_ENGINE_DATABASE_URL=mssql+pymssql://user:pass@host:1433/db

Custom environment variable names in ``.env``
----------------------------------------------

The ``.env`` file uses a flat key-value format (no ``export`` prefix)::

    HOST="server.database.windows.net"
    DB_NAME="database_name"
    USERNAME="user"
    PASSWORD="p@ssw0rd"

These are consumed by ``load_env()`` and **not** exported directly to the
environment — only the final ``CREDIT_ENGINE_DATABASE_URL`` is set.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

_CONFIG_DIR = Path(__file__).resolve().parent
_DOT_ENV_PATH = _CONFIG_DIR / ".env"

# Names of the variables the config reads from .env
_ENV_KEYS = ("HOST_DB", "DB_NAME", "USERNAME_db", "PASSWORD_db")

# The env var the rest of the app (connection.py / main.py) checks
DATABASE_URL_ENV_VAR = "CREDIT_ENGINE_DATABASE_URL"

# LLM configuration
LLM_BASE_URL_ENV_VAR = "LLM_BASE_URL"
LLM_MODEL_ENV_VAR = "LLM_MODEL"

# Driver template — pymssql is a pure-Python driver, no system ODBC needed.
# Ideal for Railway/container deployments where ODBC Driver 18 is unavailable.
_DEFAULT_DRIVER_URL = (
    "mssql+pymssql://{user}:{password}@{host}:1433/{db}"
)


def _parse_dotenv(text: str) -> dict[str, str]:
    """Parse a python-dotenv-style file into a key-value dict.

    Handles ``KEY=value``, ``KEY="quoted value"``, comments (``#``),
    and blank lines. Does **not** support multi-line values.
    """
    result: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, raw_val = stripped.partition("=")
        key = key.strip()
        val = raw_val.strip()
        # Strip surrounding quotes
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
            val = val[1:-1]
        result[key] = val
    return result


def _load_dotenv(path: Path) -> dict[str, str]:
    """Read ``.env`` from disk and return its key-value pairs."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    return _parse_dotenv(text)


def _build_url(values: dict[str, str]) -> str | None:
    """Build a ``mssql+pyodbc`` URL from the config values.

    Falls back to ``os.environ`` for each key so that Railway-injected
    variables are picked up even when the local ``.env`` is empty.

    Returns ``None`` if any required field is missing.
    """
    host = values.get("HOST_DB") or os.environ.get("HOST_DB")
    db = values.get("DB_NAME") or os.environ.get("DB_NAME")
    user = values.get("USERNAME_db") or os.environ.get("USERNAME_db")
    password = values.get("PASSWORD_db") or os.environ.get("PASSWORD_db")

    if not all((host, db, user, password)):
        return None

    encoded_password = quote(password, safe="")
    return _DEFAULT_DRIVER_URL.format(
        user=user,
        password=encoded_password,
        host=host,
        db=db,
    )


def load_env(*, dotenv_path: Path = _DOT_ENV_PATH) -> str | None:
    """Load ``.env`` and set ``CREDIT_ENGINE_DATABASE_URL``.

    If the env var is already set (e.g. from the shell before startup),
    this is a no-op — explicit overrides always win.

    Returns the resolved URL, or ``None`` if no database is configured.
    """
    if os.environ.get(DATABASE_URL_ENV_VAR):
        return os.environ[DATABASE_URL_ENV_VAR]

    values = _load_dotenv(dotenv_path)
    url = _build_url(values)
    if url is not None:
        os.environ[DATABASE_URL_ENV_VAR] = url

    return url
