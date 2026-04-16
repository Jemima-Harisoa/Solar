from app.crud.base import BaseCrud


class SystemConfigurationCrud(BaseCrud):
    def get_active_config(self) -> tuple[float, float] | None:
        rows = self.query(
            """
            SELECT TOP 1 SolarPanelEfficiencyPct, BatteryOvercapacityPct
            FROM SystemConfiguration
            WHERE IsActive = 1
            ORDER BY ConfigId DESC
            """
        )
        if not rows:
            return None
        return float(rows[0][0]), float(rows[0][1])
