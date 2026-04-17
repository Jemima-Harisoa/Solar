class EnergySpecService:
    @staticmethod
    def build_spec(
        slot_rows: list[tuple],
        efficiency_pct: float,
        battery_overcapacity_pct: float,
        slot_hours_by_name: dict[str, float] | None = None,
    ) -> dict:
        by_slot = {str(name).strip().upper(): float(wh) for name, wh in slot_rows}

        # Tranches metier fixes:
        # - JOUR (6h-17h): production solaire
        # - SOIR (17h-19h): production solaire reduite mais disponible
        # - NUIT (19h-6h): alimentation via batterie
        day_wh = by_slot.get("JOUR", 0.0)
        evening_wh = by_slot.get("SOIR", 0.0)
        night_wh = by_slot.get("NUIT", 0.0)

        total_wh = day_wh + evening_wh + night_wh

        # La batterie est dimensionnee pour couvrir toute la nuit (+ marge de securite).
        battery_wh = night_wh * (1.0 + battery_overcapacity_pct / 100.0)

        # Recharge dynamique sur les creneaux de production (JOUR + SOIR).
        # Si les durees ne sont pas disponibles, fallback sur la fenetre standard 6h-19h.
        normalized_hours = {
            str(name).strip().upper(): float(hours)
            for name, hours in (slot_hours_by_name or {}).items()
        }
        charge_window_hours = normalized_hours.get("JOUR", 0.0) + normalized_hours.get("SOIR", 0.0)
        if charge_window_hours <= 0:
            charge_window_hours = 13.0
        battery_charge_power_w = 0.0 if charge_window_hours <= 0 else battery_wh / charge_window_hours

        # Besoin pratique pour les panneaux:
        # consommation jour+soir + energie a stocker pour la nuit.
        practical_need_wh = day_wh + evening_wh + battery_wh

        # Rendement panneaux applique sur le besoin pratique.
        panel_w = 0.0 if efficiency_pct <= 0 else practical_need_wh * 100.0 / efficiency_pct

        return {
            "total_wh": total_wh,
            "practical_need_wh": practical_need_wh,
            "panel_w": panel_w,
            "battery_wh": battery_wh,
            "battery_charge_power_w": battery_charge_power_w,
            "charge_window_hours": charge_window_hours,
            "by_slot": by_slot,
            "rows": slot_rows,
        }
