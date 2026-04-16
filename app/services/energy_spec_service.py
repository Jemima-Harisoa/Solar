class EnergySpecService:
    @staticmethod
    def build_spec(slot_rows: list[tuple], efficiency_pct: float, battery_overcapacity_pct: float) -> dict:
        by_slot = {name: float(wh) for name, wh in slot_rows}
        total_wh = sum(by_slot.values())
        night_wh = by_slot.get("NUIT", 0.0)

        panel_w = 0.0 if efficiency_pct <= 0 else total_wh * 100.0 / efficiency_pct
        battery_wh = night_wh * (1.0 + battery_overcapacity_pct / 100.0)

        return {
            "total_wh": total_wh,
            "panel_w": panel_w,
            "battery_wh": battery_wh,
            "by_slot": by_slot,
            "rows": slot_rows,
        }
