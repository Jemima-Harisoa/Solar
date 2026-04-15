#!/bin/bash

set -euo pipefail

SQL_USER="${SQL_USER:-sa}"

if [ -z "${SA_PASSWORD:-}" ]; then
    echo "SA_PASSWORD est requis pour initialiser SQL Server."
    exit 1
fi

# En CI, l'initialisation est geree explicitement dans le workflow.
if [ "${SKIP_INIT_ON_START:-0}" = "1" ]; then
    echo "Initialisation auto ignoree (SKIP_INIT_ON_START=1)."
    exit 0
fi

echo "Attente de SQL Server..."
for i in {1..30}; do
    if /opt/mssql-tools18/bin/sqlcmd -c "GO" -I -S localhost -U "$SQL_USER" -P "$SA_PASSWORD" -C -Q "SELECT 1" >/dev/null 2>&1; then
        echo "SQL Server est pret."
        break
    fi

    if [ "$i" -eq 30 ]; then
        echo "SQL Server n'est pas pret apres 60s."
        exit 1
    fi

    sleep 2
done

echo "Execution des scripts d'initialisation..."
for script in /scripts/init/*.sql; do
    [ -f "$script" ] || continue
    echo "Running $script..."
    /opt/mssql-tools18/bin/sqlcmd -c "GO" -I -S localhost -U "$SQL_USER" -P "$SA_PASSWORD" -C -b -i "$script"
done

echo "Initialisation terminee."