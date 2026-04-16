"""Reusable SQL Server connection module."""

from __future__ import annotations

import os
from typing import Optional

import pymssql


class ServerConnectionError(Exception):
    """Raised when SQL Server connection operations fail."""


class ServerTransactionError(Exception):
    """Raised when a transaction operation fails."""


class ServerConnect:
    """Small reusable wrapper around a pymssql connection."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        autocommit: bool = False,
    ) -> None:
        self.host = host or os.getenv("SQL_SERVER_HOST", "127.0.0.1")
        self.port = int(port or os.getenv("SQL_SERVER_PORT", "1433"))
        self.user = user or os.getenv("SQL_USER", "sa")
        self.password = password or os.getenv("SQL_PASSWORD") or os.getenv("SA_PASSWORD", "SolarDev!2026")
        self.database = database or os.getenv("DATABASE_NAME", "solar")
        self.autocommit = autocommit
        self._connection: Optional[pymssql.Connection] = None

    def getConnection(self) -> pymssql.Connection:
        """Open and return the current connection."""
        if self._connection is None:
            try:
                self._connection = pymssql.connect(
                    server=f"{self.host}:{self.port}",
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    autocommit=self.autocommit,
                    login_timeout=8,
                    timeout=15,
                )
            except Exception as exc:
                raise ServerConnectionError(
                    f"Impossible d'ouvrir la connexion SQL Server ({self.host}:{self.port}/{self.database}): {exc}"
                ) from exc
        return self._connection

    def commit(self) -> None:
        """Commit current transaction when autocommit is disabled."""
        if not self.autocommit:
            try:
                connection = self.getConnection()
                connection.commit()
            except Exception as exc:
                raise ServerTransactionError("Echec du commit de transaction.") from exc

    def rollback(self) -> None:
        """Rollback current transaction when autocommit is disabled."""
        if not self.autocommit:
            try:
                connection = self.getConnection()
                connection.rollback()
            except Exception as exc:
                raise ServerTransactionError("Echec du rollback de transaction.") from exc

    def Disconnect(self) -> None:
        """Close current connection if it exists."""
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                # Avoid a hard crash on shutdown/cleanup paths.
                pass
            finally:
                self._connection = None
