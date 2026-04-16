from app.crud.base import BaseCrud


class DeviceUsageScheduleCrud(BaseCrud):
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
        return float(self.query("SELECT ISNULL(SUM(DailyUsageHours), 0) FROM DeviceUsageSchedule WHERE IsEnabled = 1")[0][0])

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
            SELECT ts.SlotName, ISNULL(SUM(d.PowerW * dus.DailyUsageHours), 0) AS ConsumptionWh
            FROM TimeSlot ts
            LEFT JOIN DeviceUsageSchedule dus ON dus.TimeSlotId = ts.TimeSlotId AND dus.IsEnabled = 1
            LEFT JOIN Device d ON d.DeviceId = dus.DeviceId
            GROUP BY ts.TimeSlotId, ts.SlotName
            ORDER BY ts.TimeSlotId
            """
        )
