import math


class EnergySpecService:
    @staticmethod
    def _normalize_slot_name(name: str) -> str:
        normalized = str(name).strip().upper()
        mapping = {
            "T1": "JOUR",
            "T2": "SOIR",
            "T3": "NUIT",
            "DAY": "JOUR",
            "EVENING": "SOIR",
            "NIGHT": "NUIT",
        }
        return mapping.get(normalized, normalized)

    # [SOLAR-DEFERRED] Mini-fonctions pour calcul batterie (Étape 2: Refactoring)
    @staticmethod
    def _calculer_part_batterie_soir(evening_wh: float, solar_ratio: float = 0.5) -> tuple[float, float]:
        """
        Détermine la part de consommation soir alimentée par batterie vs panneaux.
        Retourne: (evening_solar_wh, evening_battery_wh)
        """
        evening_solar_wh = evening_wh * solar_ratio
        evening_battery_wh = evening_wh - evening_solar_wh
        return evening_solar_wh, evening_battery_wh

    @staticmethod
    def _calculer_couverture_nuit(night_wh: float, evening_battery_wh: float) -> float:
        """
        Calcule l'énergie totale à stocker en batterie pour couvrir la nuit + part soir.
        """
        battery_base_wh = night_wh + evening_battery_wh
        return battery_base_wh

    @staticmethod
    def _calculer_capacite_batterie(battery_base_wh: float, battery_overcapacity_pct: float) -> float:
        """
        Dimensionne la capacité batterie en appliquant la marge de sécurité.
        """
        battery_wh = battery_base_wh * (1.0 + battery_overcapacity_pct / 100.0)
        return battery_wh

    @staticmethod
    def build_spec(
        slot_rows: list[tuple],
        efficiency_pct: float,
        battery_overcapacity_pct: float,
        slot_hours_by_name: dict[str, float] | None = None,
    ) -> dict:
        by_slot = {}
        for name, wh in slot_rows:
            slot_name = EnergySpecService._normalize_slot_name(name)
            by_slot[slot_name] = by_slot.get(slot_name, 0.0) + float(wh)

        # Tranches metier fixes:
        # - JOUR (6h-17h): production solaire
        # - SOIR (17h-19h): production solaire reduite mais disponible
        # - NUIT (19h-6h): alimentation via batterie
        day_wh = by_slot.get("JOUR", 0.0)
        evening_wh = by_slot.get("SOIR", 0.0)
        night_wh = by_slot.get("NUIT", 0.0)
        # [SOLAR-DEFERRED] Appel mini-fonction _calculer_part_batterie_soir
        evening_solar_wh, evening_battery_wh = EnergySpecService._calculer_part_batterie_soir(evening_wh)

        total_wh = day_wh + evening_wh + night_wh

        # [SOLAR-DEFERRED] Appel mini-fonction _calculer_couverture_nuit
        battery_base_wh = EnergySpecService._calculer_couverture_nuit(night_wh, evening_battery_wh)
        # [SOLAR-DEFERRED] Appel mini-fonction _calculer_capacite_batterie
        battery_wh = EnergySpecService._calculer_capacite_batterie(battery_base_wh, battery_overcapacity_pct)

        # Recharge dynamique uniquement avant 17h sur le creneau JOUR.
        # Si la duree n'est pas disponible, fallback sur la fenetre standard 6h-17h.
        normalized_hours = {
            EnergySpecService._normalize_slot_name(name): float(hours)
            for name, hours in (slot_hours_by_name or {}).items()
        }
        default_slot_hours = {"JOUR": 11.0, "SOIR": 2.0, "NUIT": 11.0}

        def _slot_hours(slot_name: str) -> float:
            hours = normalized_hours.get(slot_name, default_slot_hours[slot_name])
            return hours if hours > 0 else default_slot_hours[slot_name]

        slot_hours = {
            "JOUR": _slot_hours("JOUR"),
            "SOIR": _slot_hours("SOIR"),
            "NUIT": _slot_hours("NUIT"),
        }

        charge_window_hours = normalized_hours.get("JOUR", 0.0)
        if charge_window_hours <= 0:
            charge_window_hours = default_slot_hours["JOUR"]
        battery_charge_wh = battery_wh
        by_slot_wh = {
            "JOUR": day_wh,
            "SOIR": evening_wh,
            "NUIT": night_wh,
        }
        rows_wh = [(EnergySpecService._normalize_slot_name(name), float(wh)) for name, wh in slot_rows]

        # Si slot == Soir quota paneau => energie soir X2 => production en soire -1/2 faible ecelrage lumineu 
        
        # Dimensionnement convertisseur: 2x la puissance moyenne de la tranche.
        # La conso est en Wh, donc conversion en W via division par la duree du creneau.
        converter_factor = 2.0
        converter_by_slot_w = {
            slot_name: (slot_value / slot_hours[slot_name]) * converter_factor if slot_hours[slot_name] > 0 else 0.0
            for slot_name, slot_value in by_slot_wh.items()
        }
        converter_total_w = sum(converter_by_slot_w.values())
        energy_supplied_w = converter_total_w
        converter_rows_w = [
            (name, converter_by_slot_w.get(EnergySpecService._normalize_slot_name(name), 0.0))
            for name, _ in slot_rows
        ]
        if converter_by_slot_w:
            converter_peak_slot, converter_peak_w = max(converter_by_slot_w.items(), key=lambda item: item[1])
        else:
            converter_peak_slot, converter_peak_w = "-", 0.0

        # Besoin pratique pour les panneaux:
        # consommation JOUR + part solaire du SOIR + energie a stocker pour batterie.
        practical_need_wh = day_wh + evening_solar_wh + battery_wh

        # Dimensionnement panneaux en puissance (W):
        # besoin journalier (Wh) / fenetre de production (h).
        # Le rendement est applique par type de panneau via ExploitablePct (UsableEnergyW).
        _ = efficiency_pct  # Conservé pour compatibilite des appels existants.
        panel_w = 0.0
        if charge_window_hours > 0:
            panel_w = practical_need_wh / charge_window_hours

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

    # [SOLAR-DEFERRED] Étape 3: Calcul surplus monétisable
    @staticmethod
    def calculer_surplus_monetisable(
        fenetre_solaire: tuple[float, float],
        production_par_creneau: dict[str, float],
        usages: list[dict],
        prix_vente_ar_wh: float,
    ) -> dict:
        """
        Calcule l'énergie monétisable (surplus solaire) par créneau.
        
        Args:
            fenetre_solaire: (heure_debut, heure_fin) de la fenêtre active (e.g., (8, 17))
            production_par_creneau: {"JOUR": Wh, "SOIR": Wh, "NUIT": Wh}
            usages: list[{"creneau": str, "energie_wh": float, "heure_debut": float, "heure_fin": float}]
            prix_vente_ar_wh: prix de vente en Ar/Wh
        
        Returns:
            dict with per-créneau breakdown:
            {
                "JOUR": {
                    "production_wh": float,
                    "consommation_wh": float,
                    "surplus_wh": float,
                    "revenu_ar": float,
                },
                "SOIR": {...},
                "NUIT": {...},
                "total": {
                    "production_wh": float,
                    "consommation_wh": float,
                    "surplus_wh": float,
                    "revenu_ar": float,
                }
            }
        """
        # Fenêtre de monétisation: seule la production DANS fenetre_solaire compte
        fenetre_debut, fenetre_fin = fenetre_solaire
        
        # Créneau fixes per business logic
        creneaux_ranges = {
            "JOUR": (6.0, 17.0),      # 6h-17h: production maximale
            "SOIR": (17.0, 19.0),     # 17h-19h: production réduite mais possible
            "NUIT": (19.0, 6.0),      # 19h-6h: batterie uniquement
        }
        
        # Normaliser créneau d'usage
        def normaliser_creneau(nom: str) -> str:
            return EnergySpecService._normalize_slot_name(nom)
        
        # Calculer consommation par créneau (en dehors de la fenêtre = 0 revenu potentiel)
        consommation_par_creneau = {"JOUR": 0.0, "SOIR": 0.0, "NUIT": 0.0}
        for usage in usages:
            creneau_nom = normaliser_creneau(usage.get("creneau", ""))
            if creneau_nom in consommation_par_creneau:
                # Énergie utilisée dans le créneau
                energie_wh = float(usage.get("energie_wh", 0.0))
                consommation_par_creneau[creneau_nom] += energie_wh
        
        # Calculer surplus ET revenu par créneau
        resultats_par_creneau = {}
        production_totale = 0.0
        consommation_totale = 0.0
        surplus_total = 0.0
        revenu_total = 0.0
        
        for creneau_nom in ["JOUR", "SOIR", "NUIT"]:
            production_wh = float(production_par_creneau.get(creneau_nom, 0.0))
            consommation_wh = float(consommation_par_creneau.get(creneau_nom, 0.0))
            
            # Surplus = production - consommation (min 0)
            surplus_wh = max(0.0, production_wh - consommation_wh)
            
            # Seul le surplus DANS la fenêtre solaire génère du revenu
            # Si créneau en dehors fenêtre => revenu = 0
            creneau_debut, creneau_fin = creneaux_ranges[creneau_nom]
            
            # Déterminer si créneau chevauche fenêtre de monétisation
            revenu_ar = 0.0
            if (creneau_debut < fenetre_fin and creneau_fin > fenetre_debut):
                # Créneau chevauche fenêtre solaire => revenu possible
                revenu_ar = surplus_wh * prix_vente_ar_wh
            
            resultats_par_creneau[creneau_nom] = {
                "production_wh": production_wh,
                "consommation_wh": consommation_wh,
                "surplus_wh": surplus_wh,
                "revenu_ar": revenu_ar,
            }
            
            production_totale += production_wh
            consommation_totale += consommation_wh
            surplus_total += surplus_wh
            revenu_total += revenu_ar
        
        resultats_par_creneau["total"] = {
            "production_wh": production_totale,
            "consommation_wh": consommation_totale,
            "surplus_wh": surplus_total,
            "revenu_ar": revenu_total,
        }
        
        return resultats_par_creneau
