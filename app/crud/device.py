from app.crud.base import BaseCrud


class DeviceCrud(BaseCrud):
    def list_devices(self) -> list[tuple]:
        return self.query(
            """
            SELECT d.DeviceId, d.DeviceCode, d.DeviceName, dt.TypeName, d.PowerW, d.Status, d.InstallationDate
            FROM Device d
            INNER JOIN DeviceType dt ON dt.DeviceTypeId = d.DeviceTypeId
            ORDER BY d.DeviceName
            """
        )

    def count_devices(self) -> int:
        return int(self.query("SELECT COUNT(*) FROM Device")[0][0])

    def create_device(
        self,
        code: str,
        name: str,
        device_type_id: int,
        power_w: float,
        description: str | None,
        installation_date: str,
        status: str,
    ) -> None:
        self.execute(
            """
            INSERT INTO Device(DeviceCode, DeviceName, DeviceTypeId, PowerW, Description, InstallationDate, Status)
            VALUES(%s, %s, %s, %s, %s, %s, %s)
            """,
            (code, name, device_type_id, power_w, description, installation_date, status),
        )
