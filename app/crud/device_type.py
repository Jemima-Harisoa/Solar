from app.crud.base import BaseCrud


class DeviceTypeCrud(BaseCrud):
    def truncate(self) -> bool:
        """Vider la table DeviceType."""
        self.execute("DELETE FROM Device WHERE 1=1")
        self.execute("TRUNCATE TABLE DeviceType")
        return True

    @staticmethod
    def infer_energy_role(type_name: str, category: str) -> str:
        name = (type_name or "").upper()
        cat = (category or "").upper()

        if any(token in name or token in cat for token in ("PANNEAU", "SOLAIRE", "PRODUCT")):
            return "PRODUCTEUR"
        if any(token in name or token in cat for token in ("BATTER", "STOCK")):
            return "STOCKAGE"
        return "CONSOMMATEUR"

    def list_types_with_role(self) -> list[tuple]:
        rows = self.query("SELECT DeviceTypeId, TypeName, Category FROM DeviceType ORDER BY TypeName")
        return [(type_id, type_name, category, self.infer_energy_role(type_name, category)) for type_id, type_name, category in rows]

    def list_types(self) -> list[tuple]:
        return [(type_id, type_name) for type_id, type_name, _, _ in self.list_types_with_role()]
