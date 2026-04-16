import os
import sys
import time

import pymssql


def main() -> int:
    host = os.getenv("SQL_SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SQL_SERVER_PORT", "1433"))
    user = os.getenv("SQL_USER", "sa")
    password = os.getenv("SQL_PASSWORD", "SolarDev!2026")
    database = os.getenv("DATABASE_NAME", "solar")

    last_error = None
    for attempt in range(1, 13):
        try:
            conn = pymssql.connect(
                server=host, port=port, user=user, password=password,
                database=database, login_timeout=5, timeout=10, as_dict=True,
            )
            with conn, conn.cursor() as cursor:
                cursor.execute("SELECT DB_NAME() AS db_name;")
                db_name = cursor.fetchone()["db_name"]
                cursor.execute("SELECT COUNT(*) AS total FROM Device;")
                device_count = cursor.fetchone()["total"]
                cursor.execute("SELECT COUNT(*) AS total FROM TimeSlot;")
                timeslot_count = cursor.fetchone()["total"]

            print(f"Connexion OK (DB: {db_name}) — Device: {device_count}, TimeSlot: {timeslot_count}")
            return 0

        except Exception as exc:
            last_error = exc
            print(f"Tentative {attempt}/12: {exc}")
            time.sleep(5)

    print(f"Echec connexion SQL Server apres 12 tentatives.\n{last_error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())