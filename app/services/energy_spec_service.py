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
        default_slot_hours = {"JOUR": 11.0, "SOIR": 2.0, "NUIT": 11.0}

        def _slot_hours(slot_name: str) -> float:
            hours = normalized_hours.get(slot_name, default_slot_hours[slot_name])
            return hours if hours > 0 else default_slot_hours[slot_name]

        day_hours = _slot_hours("JOUR")
        evening_hours = _slot_hours("SOIR")
        night_hours = _slot_hours("NUIT")

        charge_window_hours = normalized_hours.get("JOUR", 0.0) + normalized_hours.get("SOIR", 0.0)
        if charge_window_hours <= 0:
            charge_window_hours = 13.0
        battery_charge_wh = battery_wh
        by_slot_wh = {
            "JOUR": day_wh,
            "SOIR": evening_wh,
            "NUIT": night_wh,
        }
        rows_wh = [(name, by_slot_wh.get(str(name).strip().upper(), 0.0)) for name, _ in slot_rows]

        # Dimensionnement convertisseur: 2x la consommation de la tranche.
        converter_by_slot_w = {
            slot_name: slot_value * 2.0
            for slot_name, slot_value in by_slot_wh.items()
        }
        converter_total_w = sum(converter_by_slot_w.values())
        energy_supplied_w = converter_total_w

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
            "battery_charge_wh": battery_charge_wh,
            "charge_window_hours": charge_window_hours,
            "by_slot": by_slot,
            "by_slot_wh": by_slot_wh,
            "rows": slot_rows,
            "rows_wh": rows_wh,
            "converter_by_slot_w": converter_by_slot_w,
            "converter_total_w": converter_total_w,
            "energy_supplied_w": energy_supplied_w,
        }
