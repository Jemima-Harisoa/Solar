#!/bin/bash
set -euo pipefail

/opt/mssql/bin/sqlservr &
sql_pid=$!

if [ "${SKIP_INIT_ON_START:-0}" = "1" ]; then
  wait "$sql_pid"
  exit 0
fi

for i in {1..60}; do
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "${SA_PASSWORD}" -C -Q "SELECT 1" >/dev/null 2>&1 && break
  sleep 2
done

if /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "${SA_PASSWORD}" -d solar -C -h -1 -W -Q "SET NOCOUNT ON; IF OBJECT_ID('dbo.SystemConfiguration', 'U') IS NOT NULL AND EXISTS (SELECT 1 FROM dbo.SystemConfiguration) SELECT 1 ELSE SELECT 0" 2>/dev/null | tr -d '\r' | grep -q '^1$'; then
  echo "Seed already present, skipping init scripts."
else
  for script in /scripts/init/*.sql; do
    [ -f "$script" ] || continue
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "${SA_PASSWORD}" -C -b -i "$script"
  done
fi

wait "$sql_pid"
