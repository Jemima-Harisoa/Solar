import os
import sys
import time

import pymssql


def get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def main() -> int:
    host = get_env("SQL_SERVER_HOST", "127.0.0.1")
    port = int(get_env("SQL_SERVER_PORT", "1433"))
    user = get_env("SQL_USER", "sa")
    password = get_env("SQL_PASSWORD", "Dev12345")
    database = get_env("DATABASE_NAME", "solar")

    last_error = None
    for attempt in range(1, 13):
        try:
            conn = pymssql.connect(
                server=host,
                port=port,
                user=user,
                password=password,
                database=database,
                login_timeout=5,
                timeout=10,
                as_dict=True,
            )
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT DB_NAME() AS db_name;")
                    db_name = cursor.fetchone()["db_name"]

                    cursor.execute("SELECT COUNT(*) AS total FROM Device;")
                    device_count = cursor.fetchone()["total"]

                    cursor.execute("SELECT COUNT(*) AS total FROM TimeSlot;")
                    timeslot_count = cursor.fetchone()["total"]

            print(f"Connexion SQL Server OK (DB: {db_name})")
            print(f"Device count: {device_count}")
            print(f"TimeSlot count: {timeslot_count}")
            return 0
        except Exception as exc:  # pylint: disable=broad-except
            last_error = exc
            print(f"Tentative {attempt}/12: SQL Server indisponible ({exc})")
            time.sleep(5)

    print("Echec connexion SQL Server apres plusieurs tentatives.")
    if last_error:
        print(last_error)
    return 1


if __name__ == "__main__":
    sys.exit(main())
