from app.crud.base import BaseCrud


class PanelTypeCrud(BaseCrud):

    # reinitialiser la table type panel pour mettre de nouvel donne  
    def truncate(self):
        """Vider la table PanelType."""
        self.execute("TRUNCATE TABLE PanelType")
        return True

    def create_panel_type(
        self,
        type_name: str,
        exploitable_pct: float,
        unit_energy_w: float,
        unit_price_ar: float,
        description: str | None = None,
    ) -> int:
        sql = """
            INSERT INTO PanelType
                (TypeName, ExploitablePct, UnitEnergyW, UnitPriceAr, Description)
            VALUES (?, ?, ?, ?, ?)
        """
        self.execute(sql, (type_name, exploitable_pct, unit_energy_w, unit_price_ar, description))
        return self.get_last_insert_id()

    def list_panel_types(self) -> list[tuple]:
        return self.query(
            """
            SELECT PanelTypeId, TypeName, ExploitablePct, UnitEnergyW, UnitPriceAr,
                   UsableEnergyW, Description, CreatedAt
            FROM PanelType
            ORDER BY TypeName
            """
        )

    def get_last_insert_id(self) -> int | None:
        rows = self.query("SELECT CAST(SCOPE_IDENTITY() AS INT) AS LastId")
        return int(rows[0][0]) if rows and rows[0][0] is not None else None
