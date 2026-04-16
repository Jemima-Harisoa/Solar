from app.crud.base import BaseCrud


class DeviceCrud(BaseCrud):
    def list_devices(self) -> list[tuple]:
        return self.query(
            """
            SELECT d.DeviceId,
                   d.DeviceCode,
                   d.DeviceName,
                   dt.TypeName,
                   dt.Category,
                   CASE
                       WHEN UPPER(dt.TypeName) LIKE N'%PANNEAU%'
                         OR UPPER(dt.TypeName) LIKE N'%SOLAIRE%'
                         OR UPPER(dt.Category) LIKE N'%PRODUCT%'
                           THEN N'PRODUCTEUR'
                       WHEN UPPER(dt.TypeName) LIKE N'%BATTER%'
                         OR UPPER(dt.TypeName) LIKE N'%STOCK%'
                         OR UPPER(dt.Category) LIKE N'%STOCK%'
                           THEN N'STOCKAGE'
                       ELSE N'CONSOMMATEUR'
                   END AS EnergyRole,
                   d.PowerW,
                   d.Status,
                   d.InstallationDate
            FROM Device d
            INNER JOIN DeviceType dt ON dt.DeviceTypeId = d.DeviceTypeId
            ORDER BY d.DeviceName
            """
        )

    def list_consumer_devices(self) -> list[tuple]:
        return self.query(
            """
            SELECT d.DeviceId, d.DeviceCode, d.DeviceName
            FROM Device d
            INNER JOIN DeviceType dt ON dt.DeviceTypeId = d.DeviceTypeId
            WHERE NOT (
                UPPER(dt.TypeName) LIKE N'%PANNEAU%'
                OR UPPER(dt.TypeName) LIKE N'%SOLAIRE%'
                OR UPPER(dt.Category) LIKE N'%PRODUCT%'
                OR UPPER(dt.TypeName) LIKE N'%BATTER%'
                OR UPPER(dt.TypeName) LIKE N'%STOCK%'
                OR UPPER(dt.Category) LIKE N'%STOCK%'
            )
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
