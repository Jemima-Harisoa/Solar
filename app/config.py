import os
from pathlib import Path


def load_dotenv_file(dotenv_path: str = ".env") -> None:
    """Load .env key/value pairs into process environment if available."""
    path = Path(dotenv_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / dotenv_path

    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


def normalize_sql_host_for_local_run() -> None:
    """Use localhost when docker service hostname is loaded on host OS."""
    host = os.getenv("SQL_SERVER_HOST", "").strip().lower()
    if host == "sqlserver":
        os.environ["SQL_SERVER_HOST"] = "127.0.0.1"
