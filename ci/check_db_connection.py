import os
import sys
import time

import pymssql


def get_env(name: str, default: str) -> str:
    # Lit une variable d'environnement avec une valeur par défaut
    # pour rendre le script réutilisable en local et en CI.
    return os.getenv(name, default)


def main() -> int:
    # Paramètres de connexion SQL Server (injectés par le pipeline CI).
    host = get_env("SQL_SERVER_HOST", "127.0.0.1")
    port = int(get_env("SQL_SERVER_PORT", "1433"))
    user = get_env("SQL_USER", "sa")
    password = get_env("SQL_PASSWORD", "SolarDev!2026")
    database = get_env("DATABASE_NAME", "solar")

    last_error = None
    # Réessaie pendant ~60 secondes (12 x 5s) pour laisser le temps
    # au conteneur SQL Server de devenir disponible.
    for attempt in range(1, 13):
        try:
            # Ouvre la connexion avec des timeouts courts pour éviter
            # de bloquer longtemps en cas d'indisponibilité.
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
                    # Vérifie la base cible effectivement utilisée.
                    cursor.execute("SELECT DB_NAME() AS db_name;")
                    db_name = cursor.fetchone()["db_name"]

                    # Vérifie que des données de référence existent
                    # (tables créées + scripts d'initialisation exécutés).
                    cursor.execute("SELECT COUNT(*) AS total FROM Device;")
                    device_count = cursor.fetchone()["total"]

                    cursor.execute("SELECT COUNT(*) AS total FROM TimeSlot;")
                    timeslot_count = cursor.fetchone()["total"]

            # Retour 0 => succès CI.
            print(f"Connexion SQL Server OK (DB: {db_name})")
            print(f"Device count: {device_count}")
            print(f"TimeSlot count: {timeslot_count}")
            return 0
        except Exception as exc:  # pylint: disable=broad-except
            # On capture toute erreur de connexion/SQL pendant la phase
            # de démarrage puis on retente après une courte pause.
            last_error = exc
            print(f"Tentative {attempt}/12: SQL Server indisponible ({exc})")
            time.sleep(5)

    # Retour 1 => échec CI si la base n'est jamais joignable.
    print("Echec connexion SQL Server apres plusieurs tentatives.")
    if last_error:
        print(last_error)
    return 1


if __name__ == "__main__":
    sys.exit(main())
