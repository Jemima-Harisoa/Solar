from app.crud.base import BaseCrud


class TimeSlotCrud(BaseCrud):
    def truncate(self) -> bool:
        """Vider la table TimeSlot."""
        self.execute("DELETE FROM DeviceUsageSchedule WHERE 1=1")
        self.execute("DELETE FROM EnergyConsumption WHERE 1=1")
        self.execute("TRUNCATE TABLE TimeSlot")
        return True

    def list_timeslots(self) -> list[tuple]:
        return self.query("SELECT TimeSlotId, SlotName, StartHour, EndHour, ISNULL(Description, '') FROM TimeSlot ORDER BY TimeSlotId")

    def count_timeslots(self) -> int:
        return int(self.query("SELECT COUNT(*) FROM TimeSlot")[0][0])

    def create_timeslot(self, name: str, start_hour: int, end_hour: int, description: str | None) -> None:
        self.execute(
            "INSERT INTO TimeSlot(SlotName, StartHour, EndHour, Description) VALUES(%s, %s, %s, %s)",
            (name, start_hour, end_hour, description),
        )

    def truncate_timeslots_with_dependents(self) -> None:
        self.execute(
            """
            SET XACT_ABORT ON;
            BEGIN TRANSACTION;

            DELETE FROM BatteryMovement;
            DELETE FROM SolarPanelProduction;
            DELETE FROM EnergyConsumption;
            DELETE FROM DeviceUsageSchedule;
            DELETE FROM TimeSlot;

            DBCC CHECKIDENT ('BatteryMovement', RESEED, 0);
            DBCC CHECKIDENT ('SolarPanelProduction', RESEED, 0);
            DBCC CHECKIDENT ('EnergyConsumption', RESEED, 0);
            DBCC CHECKIDENT ('DeviceUsageSchedule', RESEED, 0);
            DBCC CHECKIDENT ('TimeSlot', RESEED, 0);

            COMMIT TRANSACTION;
            """
        )
