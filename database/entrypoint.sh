#!/bin/bash

set -e

echo "Attente de SQL Server..."
for i in {1..30}; do
    if /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "SELECT 1" >/dev/null 2>&1; then
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
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -b -i "$script"
done

echo "Initialisation terminee."