FROM mcr.microsoft.com/mssql/server:2019-latest

USER root

COPY database/init /scripts/init
COPY docker/sqlserver/init-and-run.sh /usr/local/bin/init-and-run.sh
RUN chmod +x /usr/local/bin/init-and-run.sh

USER mssql

ENTRYPOINT ["/usr/local/bin/init-and-run.sh"]
