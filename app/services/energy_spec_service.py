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
        evening_solar_ratio = 0.5
        evening_solar_wh = evening_wh * evening_solar_ratio
        evening_battery_wh = evening_wh - evening_solar_wh

        total_wh = day_wh + evening_wh + night_wh

        # La batterie couvre la nuit + 50% du creneau SOIR, avec marge de securite.
        battery_base_wh = night_wh + evening_battery_wh
        battery_wh = battery_base_wh * (1.0 + battery_overcapacity_pct / 100.0)

        # Recharge dynamique uniquement avant 17h sur le creneau JOUR.
        # Si la duree n'est pas disponible, fallback sur la fenetre standard 6h-17h.
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

        charge_window_hours = normalized_hours.get("JOUR", 0.0)
        if charge_window_hours <= 0:
            charge_window_hours = default_slot_hours["JOUR"]
        battery_charge_wh = battery_wh
        by_slot_wh = {
            "JOUR": day_wh,
            "SOIR": evening_wh,
            "NUIT": night_wh,
        }
        rows_wh = [(name, by_slot_wh.get(str(name).strip().upper(), 0.0)) for name, _ in slot_rows]

        # Si slot == Soir quota paneau => energie soir X2 => production en soire -1/2 faible ecelrage lumineu 
        
        # Dimensionnement convertisseur: 2x la consommation de la tranche.
        converter_factor = 2.0
        converter_by_slot_w = {
            slot_name: slot_value * 2.0
            for slot_name, slot_value in by_slot_wh.items()
        }
        converter_total_w = sum(converter_by_slot_w.values())
        energy_supplied_w = converter_total_w
        converter_rows_w = [(name, converter_by_slot_w.get(str(name).strip().upper(), 0.0)) for name, _ in slot_rows]
        if converter_by_slot_w:
            converter_peak_slot, converter_peak_w = max(converter_by_slot_w.items(), key=lambda item: item[1])
        else:
            converter_peak_slot, converter_peak_w = "-", 0.0

        # Besoin pratique pour les panneaux:
        # consommation JOUR + part solaire du SOIR + energie a stocker pour batterie.
        practical_need_wh = day_wh + evening_solar_wh + battery_wh

        # Rendement panneaux applique sur le besoin pratique.
        panel_w = 0.0 if efficiency_pct <= 0 else practical_need_wh * 100.0 / efficiency_pct

        return {
            "total_wh": total_wh,
            "practical_need_wh": practical_need_wh,
            "panel_w": panel_w,
            "battery_wh": battery_wh,
            "battery_charge_wh": battery_charge_wh,
            "charge_window_hours": charge_window_hours,
            "evening_solar_wh": evening_solar_wh,
            "evening_battery_wh": evening_battery_wh,
            "by_slot": by_slot,
            "by_slot_wh": by_slot_wh,
            "rows": slot_rows,
            "rows_wh": rows_wh,
            "converter_by_slot_w": converter_by_slot_w,
            "converter_total_w": converter_total_w,
            "energy_supplied_w": energy_supplied_w,
            "converter_rows_w": converter_rows_w,
            "converter_factor": converter_factor,
            "converter_peak_slot": converter_peak_slot,
            "converter_peak_w": converter_peak_w,
        }
