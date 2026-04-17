import math


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

    @staticmethod
    def build_panel_options(panel_type_rows: list[tuple], required_energy_w: float) -> dict:
        options: list[dict] = []

        for row in panel_type_rows:
            panel_type_id = row[0]
            type_name = str(row[1])
            exploitable_pct = float(row[2])
            unit_energy_w = float(row[3])
            unit_price_ar = float(row[4])
            usable_energy_w = float(row[5]) if len(row) > 5 and row[5] is not None else unit_energy_w * exploitable_pct / 100.0
            description = row[6] if len(row) > 6 else None

            panel_count = math.ceil(required_energy_w / usable_energy_w) if required_energy_w > 0 and usable_energy_w > 0 else 0
            supplied_energy_w = panel_count * usable_energy_w
            total_cost_ar = panel_count * unit_price_ar
            ratio_price_per_energy = total_cost_ar / supplied_energy_w if supplied_energy_w > 0 else 0.0

            options.append(
                {
                    "panel_type_id": panel_type_id,
                    "type_name": type_name,
                    "exploitable_pct": exploitable_pct,
                    "unit_energy_w": unit_energy_w,
                    "usable_energy_w": usable_energy_w,
                    "unit_price_ar": unit_price_ar,
                    "panel_count": panel_count,
                    "supplied_energy_w": supplied_energy_w,
                    "total_cost_ar": total_cost_ar,
                    "ratio_price_per_energy": ratio_price_per_energy,
                    "description": description or "",
                }
            )

        best_option = None
        if options and required_energy_w > 0:
            best_option = min(
                options,
                key=lambda item: (
                    item["ratio_price_per_energy"],
                    item["total_cost_ar"],
                    item["panel_count"],
                    item["type_name"],
                ),
            )

        return {
            "required_energy_w": required_energy_w,
            "options": options,
            "best_option": best_option,
        }
