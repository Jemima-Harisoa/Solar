from app.crud.base import BaseCrud


class DeviceUsageScheduleCrud(BaseCrud):
    def truncate(self) -> bool:
        """Vider la table DeviceUsageSchedule."""
        self.execute("TRUNCATE TABLE DeviceUsageSchedule")
        return True

    def list_usage(self) -> list[tuple]:
        return self.query(
            """
            SELECT dus.UsageScheduleId, d.DeviceName, ts.SlotName, dus.DailyUsageHours,
                   (d.PowerW * dus.DailyUsageHours) AS DailyEnergyConsumptionWh,
                   dus.IsEnabled
            FROM DeviceUsageSchedule dus
            INNER JOIN Device d ON d.DeviceId = dus.DeviceId
            INNER JOIN TimeSlot ts ON ts.TimeSlotId = dus.TimeSlotId
            ORDER BY d.DeviceName, ts.TimeSlotId
            """
        )

    def sum_enabled_usage_hours(self) -> float:
        rows = self.query(
            """
            SELECT ISNULL(SUM(slot_max.MaxHours), 0)
            FROM (
                SELECT TimeSlotId, MAX(DailyUsageHours) AS MaxHours
                FROM DeviceUsageSchedule
                WHERE IsEnabled = 1
                GROUP BY TimeSlotId
            ) AS slot_max
            """
        )
        return float(rows[0][0])

    def upsert_usage(self, device_id: int, timeslot_id: int, daily_usage_hours: float, is_enabled: int) -> None:
        self.execute(
            """
            IF EXISTS (SELECT 1 FROM DeviceUsageSchedule WHERE DeviceId = %s AND TimeSlotId = %s)
                UPDATE DeviceUsageSchedule
                SET DailyUsageHours = %s, IsEnabled = %s
                WHERE DeviceId = %s AND TimeSlotId = %s
            ELSE
                INSERT INTO DeviceUsageSchedule(DeviceId, TimeSlotId, DailyUsageHours, IsEnabled)
                VALUES(%s, %s, %s, %s)
            """,
            (
                device_id,
                timeslot_id,
                daily_usage_hours,
                is_enabled,
                device_id,
                timeslot_id,
                device_id,
                timeslot_id,
                daily_usage_hours,
                is_enabled,
            ),
        )

    def list_consumption_by_slot(self) -> list[tuple]:
        return self.query(
            """
            SELECT ts.SlotName,
                   ISNULL(
                       SUM(
                           CASE WHEN dt.DeviceTypeId IS NULL
                                THEN 0
                                ELSE d.PowerW * dus.DailyUsageHours
                           END
                       ),
                       0
                   ) AS ConsumptionWh
            FROM TimeSlot ts
            LEFT JOIN DeviceUsageSchedule dus ON dus.TimeSlotId = ts.TimeSlotId AND dus.IsEnabled = 1
            LEFT JOIN Device d ON d.DeviceId = dus.DeviceId
            LEFT JOIN DeviceType dt ON dt.DeviceTypeId = d.DeviceTypeId
                                   AND NOT (
                                       UPPER(dt.TypeName) LIKE N'%PANNEAU%'
                                       OR UPPER(dt.TypeName) LIKE N'%SOLAIRE%'
                                       OR UPPER(dt.Category) LIKE N'%PRODUCT%'
                                       OR UPPER(dt.TypeName) LIKE N'%BATTER%'
                                       OR UPPER(dt.TypeName) LIKE N'%STOCK%'
                                       OR UPPER(dt.Category) LIKE N'%STOCK%'
                                   )
            GROUP BY ts.TimeSlotId, ts.SlotName
            ORDER BY ts.TimeSlotId
            """
        )

    def truncate_usage(self) -> None:
        self.execute(
            """
            DELETE FROM DeviceUsageSchedule;
            DBCC CHECKIDENT ('DeviceUsageSchedule', RESEED, 0);
            """
        )
