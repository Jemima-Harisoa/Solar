from app.crud.base import BaseCrud


class EnergyConsumptionCrud(BaseCrud):
    def truncate(self) -> bool:
        """Vider la table EnergyConsumption."""
        self.execute("TRUNCATE TABLE EnergyConsumption")
        return True

    def list_history(self, limit: int = 200) -> list[tuple]:
        return self.query(
            f"""
            SELECT TOP {limit} ec.ConsumptionId, ec.ConsumptionDate, d.DeviceName, ts.SlotName,
                   ec.EnergyConsumedWh, ec.DurationHours, ISNULL(ec.Notes, '')
            FROM EnergyConsumption ec
            INNER JOIN Device d ON d.DeviceId = ec.DeviceId
            INNER JOIN TimeSlot ts ON ts.TimeSlotId = ec.TimeSlotId
            ORDER BY ec.ConsumptionDate DESC, ec.ConsumptionId DESC
            """
        )

    def truncate_history(self) -> None:
        self.execute(
            """
            DELETE FROM EnergyConsumption;
            DBCC CHECKIDENT ('EnergyConsumption', RESEED, 0);
            """
        )
