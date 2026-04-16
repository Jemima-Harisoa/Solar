import os
from pathlib import Path

from connection import ServerConnect


def load_dotenv_file(dotenv_path: str = ".env") -> None:
	"""Load .env key/value pairs into process environment."""
	path = Path(dotenv_path)
	if not path.is_absolute():
		path = Path(__file__).resolve().parent / dotenv_path

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


def run_connection_check() -> None:
	"""Try a minimal query to validate SQL Server access."""
	connector = ServerConnect()
	try:
		connection = connector.getConnection()
		with connection.cursor() as cursor:
			cursor.execute("SELECT DB_NAME()")
			row = cursor.fetchone()
		db_name = row[0] if row else "unknown"
		print(f"Connexion OK sur la base: {db_name}")
	except Exception as exc:
		print(f"Connexion KO: {exc}")
		raise
	finally:
		connector.Disconnect()


if __name__ == "__main__":
	load_dotenv_file()
	normalize_sql_host_for_local_run()
	run_connection_check()
