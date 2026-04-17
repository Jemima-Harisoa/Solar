from app.crud.base import BaseCrud


class ConfigCrud(BaseCrud):
    # Classe pour gerer les methode crud de la table SystemConfiguration

    def create(
        self,
        grid_voltage: float,
        solar_efficiency: float,
        battery_overcapacity: float,
        description: str | None = None,
        is_active: bool = False,
    ) -> int:
        """Créer une configuration système et retourner son identifiant."""
        sql = """
            INSERT INTO SystemConfiguration
                (GridVoltageV, SolarPanelEfficiencyPct, BatteryOvercapacityPct, Description, IsActive)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            grid_voltage,
            solar_efficiency,
            battery_overcapacity,
            description,
            1 if is_active else 0,
        )
        self.execute(sql, params)
        return self.get_last_insert_id()

    def get_all(self) -> list[tuple]:
        """Retourner toutes les configurations triées de la plus récente à la plus ancienne."""
        return self.query(
            """
            SELECT ConfigId, GridVoltageV, SolarPanelEfficiencyPct, BatteryOvercapacityPct,
                   Description, IsActive, CreatedAt, UpdatedAt
            FROM SystemConfiguration
            ORDER BY CreatedAt DESC, ConfigId DESC
            """
        )

    def get_by_id(self, config_id: int) -> tuple | None:
        """Retourner une configuration par identifiant."""
        rows = self.query(
            """
            SELECT ConfigId, GridVoltageV, SolarPanelEfficiencyPct, BatteryOvercapacityPct,
                   Description, IsActive, CreatedAt, UpdatedAt
            FROM SystemConfiguration
            WHERE ConfigId = ?
            """,
            (config_id,),
        )
        return rows[0] if rows else None

    def update(
        self,
        config_id: int,
        grid_voltage: float | None = None,
        solar_efficiency: float | None = None,
        battery_overcapacity: float | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> bool:
        """Modifier une configuration existante."""
        if all(value is None for value in (grid_voltage, solar_efficiency, battery_overcapacity, description, is_active)):
            raise ValueError("Aucune valeur a mettre a jour.")

        fields: list[str] = []
        params: list[object] = []

        if grid_voltage is not None:
            fields.append("GridVoltageV = ?")
            params.append(grid_voltage)
        if solar_efficiency is not None:
            fields.append("SolarPanelEfficiencyPct = ?")
            params.append(solar_efficiency)
        if battery_overcapacity is not None:
            fields.append("BatteryOvercapacityPct = ?")
            params.append(battery_overcapacity)
        if description is not None:
            fields.append("Description = ?")
            params.append(description)
        if is_active is not None:
            fields.append("IsActive = ?")
            params.append(1 if is_active else 0)

        fields.append("UpdatedAt = SYSUTCDATETIME()")
        sql = f"UPDATE SystemConfiguration SET {', '.join(fields)} WHERE ConfigId = ?"
        params.append(config_id)
        self.execute(sql, tuple(params))
        return True

    def delete(self, config_id: int) -> bool:
        """Supprimer une configuration par identifiant."""
        self.execute("DELETE FROM SystemConfiguration WHERE ConfigId = ?", (config_id,))
        return True

    def truncate(self) -> bool:
        """Vider la table SystemConfiguration."""
        self.execute("TRUNCATE TABLE SystemConfiguration")
        return True

    def get_active(self) -> tuple | None:
        """Retourner la configuration active."""
        rows = self.query(
            """
            SELECT ConfigId, GridVoltageV, SolarPanelEfficiencyPct, BatteryOvercapacityPct,
                   Description, IsActive, CreatedAt, UpdatedAt
            FROM SystemConfiguration
            WHERE IsActive = 1
            ORDER BY ConfigId DESC
            """
        )
        return rows[0] if rows else None

    def set_active(self, config_id: int) -> bool:
        """Rendre une configuration active et désactiver les autres."""
        if self.get_by_id(config_id) is None:
            raise ValueError("Configuration introuvable.")

        self.execute("UPDATE SystemConfiguration SET IsActive = 0 WHERE IsActive = 1")
        self.execute(
            """
            UPDATE SystemConfiguration
            SET IsActive = 1, UpdatedAt = SYSUTCDATETIME()
            WHERE ConfigId = ?
            """,
            (config_id,),
        )
        return True

    def get_last_insert_id(self) -> int | None:
        """Retourner l'identifiant de la dernière insertion."""
        rows = self.query("SELECT CAST(SCOPE_IDENTITY() AS INT) AS LastId")
        return int(rows[0][0]) if rows and rows[0][0] is not None else None



