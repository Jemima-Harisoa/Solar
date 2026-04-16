from app.crud.base import BaseCrud


class DeviceTypeCrud(BaseCrud):
    def list_types(self) -> list[tuple]:
        return self.query("SELECT DeviceTypeId, TypeName FROM DeviceType ORDER BY TypeName")
