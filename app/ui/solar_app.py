from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk

from app.crud.device import DeviceCrud
from app.crud.device_type import DeviceTypeCrud
from app.crud.device_usage_schedule import DeviceUsageScheduleCrud
from app.crud.energy_consumption import EnergyConsumptionCrud
from app.crud.config import ConfigCrud
from app.crud.panel_type import PanelTypeCrud
from app.crud.timeslot import TimeSlotCrud
from app.services.energy_spec_service import EnergySpecService
from connection import ServerConnect


class SolarApp:
    def __init__(self, root: tk.Tk, connector: ServerConnect) -> None:
        self.root = root
        self.root.title("Solar - Gestion energetique")
        self.root.geometry("1220x760")

        self.connector = connector
        self.device_type_crud = DeviceTypeCrud(connector)
        self.device_crud = DeviceCrud(connector)
        self.timeslot_crud = TimeSlotCrud(connector)
        self.usage_crud = DeviceUsageScheduleCrud(connector)
        self.history_crud = EnergyConsumptionCrud(connector)
        self.config_crud = ConfigCrud(connector)
        self.panel_type_crud = PanelTypeCrud(connector)
        self.spec_service = EnergySpecService()

        self.device_map: dict[str, int] = {}
        self.slot_map: dict[str, int] = {}
        self.device_type_map: dict[str, int] = {}
        self.device_type_role_map: dict[str, str] = {}
        self.slot_duration_map: dict[str, float] = {}
        self.config_map: dict[str, int] = {}
        self.selected_config_id: int | None = None
        self.last_panel_need_w: float = 0.0
        self.panel_options: list[dict] = []
        self.panel_best_option: dict | None = None
        self.panel_need_reference_var = tk.StringVar(value="0 W")
        self.panel_recommendation_var = tk.StringVar(value="Aucune recommandation")
        self.panel_ratio_var = tk.StringVar(value="0.00 Ar/W")

        self.status_var = tk.StringVar(value="Pret")

        self._build_ui()
        self._safe(self.refresh_all)

    def _build_ui(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        header = ttk.Frame(self.root, padding=(12, 10))
        header.pack(fill="x")

        ttk.Label(header, text="Gestion Energie Solaire", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Button(header, text="Generer les besoins energetiques", command=lambda: self._safe(self.generate_spec)).pack(side="right")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.tab_devices = ttk.Frame(self.notebook, padding=10)
        self.tab_slots = ttk.Frame(self.notebook, padding=10)
        self.tab_usage = ttk.Frame(self.notebook, padding=10)
        self.tab_history = ttk.Frame(self.notebook, padding=10)
        self.tab_balance = ttk.Frame(self.notebook, padding=10)
        self.tab_config = ttk.Frame(self.notebook, padding=10)
        self.tab_panels = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_devices, text="Materiels")
        self.notebook.add(self.tab_slots, text="Creneaux")
        self.notebook.add(self.tab_usage, text="Usage")
        self.notebook.add(self.tab_history, text="Historique")
        self.notebook.add(self.tab_balance, text="Bilan")
        self.notebook.add(self.tab_config, text="Configurations")
        self.notebook.add(self.tab_panels, text="Types panneaux")

        self._build_config_tab()
        self._build_devices_tab()
        self._build_slots_tab()
        self._build_usage_tab()
        self._build_history_tab()
        self._build_balance_tab()
        self._build_panel_types_tab()

        ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(12, 6)).pack(fill="x")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_devices_tab(self) -> None:
        left = ttk.LabelFrame(self.tab_devices, text="Declaration de materiel", padding=10)
        left.pack(side="left", fill="y", padx=(0, 8))

        right = ttk.LabelFrame(self.tab_devices, text="Liste des materiels", padding=10)
        right.pack(side="left", fill="both", expand=True)

        self.device_code_var = tk.StringVar()
        self.device_name_var = tk.StringVar()
        self.device_type_var = tk.StringVar()
        self.device_power_var = tk.StringVar()
        self.device_date_var = tk.StringVar(value=date.today().isoformat())
        self.device_status_var = tk.StringVar(value="ACTIF")
        self.device_desc_var = tk.StringVar()
        self.device_role_var = tk.StringVar(value="-")

        self._entry(left, "Code", self.device_code_var)
        self._entry(left, "Nom", self.device_name_var)
        self.device_type_combo = self._combo(left, "Type", self.device_type_var)
        self.device_type_combo.bind("<<ComboboxSelected>>", lambda _event: self._update_selected_type_role())
        ttk.Label(left, text="Role energetique").pack(anchor="w", pady=(4, 0))
        ttk.Label(left, textvariable=self.device_role_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self._entry(left, "Puissance (W)", self.device_power_var)
        self._entry(left, "Date installation (YYYY-MM-DD)", self.device_date_var)
        self._combo(left, "Statut", self.device_status_var, ["ACTIF", "INACTIF", "MAINTEN"])
        self._entry(left, "Description", self.device_desc_var)

        act = ttk.Frame(left)
        act.pack(fill="x", pady=(8, 0))
        ttk.Button(act, text="Ajouter", command=lambda: self._safe(self.add_device)).pack(side="left")
        ttk.Button(act, text="Rafraichir", command=lambda: self._safe(self.refresh_devices)).pack(side="left", padx=6)
        ttk.Button(act, text="Reinitialiser", command=lambda: self._safe(self.truncate_devices)).pack(side="left", padx=6)

        cols = ("id", "code", "name", "type", "role", "power", "status", "date")
        self.device_tree = ttk.Treeview(right, columns=cols, show="headings", height=18)
        for col, title, width in [
            ("id", "ID", 60),
            ("code", "Code", 100),
            ("name", "Materiel", 220),
            ("type", "Type", 140),
            ("role", "Role", 120),
            ("power", "Puissance W", 110),
            ("status", "Statut", 100),
            ("date", "Installation", 110),
        ]:
            self.device_tree.heading(col, text=title)
            self.device_tree.column(col, width=width, anchor="w")
        self.device_tree.pack(fill="both", expand=True)

    def _build_slots_tab(self) -> None:
        left = ttk.LabelFrame(self.tab_slots, text="Choix des creneaux", padding=10)
        left.pack(side="left", fill="y", padx=(0, 8))

        right = ttk.LabelFrame(self.tab_slots, text="Liste des creneaux", padding=10)
        right.pack(side="left", fill="both", expand=True)

        self.slot_name_var = tk.StringVar()
        self.slot_start_var = tk.StringVar()
        self.slot_end_var = tk.StringVar()
        self.slot_desc_var = tk.StringVar()

        self._entry(left, "Nom", self.slot_name_var)
        self._entry(left, "Debut (0-23)", self.slot_start_var)
        self._entry(left, "Fin (1-24)", self.slot_end_var)
        self._entry(left, "Description", self.slot_desc_var)

        act = ttk.Frame(left)
        act.pack(fill="x", pady=(8, 0))
        ttk.Button(act, text="Ajouter", command=lambda: self._safe(self.add_slot)).pack(side="left")
        ttk.Button(act, text="Rafraichir", command=lambda: self._safe(self.refresh_slots)).pack(side="left", padx=6)
        ttk.Button(act, text="Reinitialiser", command=lambda: self._safe(self.truncate_slots)).pack(side="left", padx=6)

        cols = ("id", "name", "start", "end", "desc")
        self.slot_tree = ttk.Treeview(right, columns=cols, show="headings", height=18)
        for col, title, width in [
            ("id", "ID", 60),
            ("name", "Nom", 130),
            ("start", "Debut", 80),
            ("end", "Fin", 80),
            ("desc", "Description", 360),
        ]:
            self.slot_tree.heading(col, text=title)
            self.slot_tree.column(col, width=width, anchor="w")
        self.slot_tree.pack(fill="both", expand=True)

    def _build_usage_tab(self) -> None:
        left = ttk.LabelFrame(self.tab_usage, text="Temps d'usage", padding=10)
        left.pack(side="left", fill="y", padx=(0, 8))

        right = ttk.LabelFrame(self.tab_usage, text="Programme d'usage", padding=10)
        right.pack(side="left", fill="both", expand=True)

        self.usage_device_var = tk.StringVar()
        self.usage_slot_var = tk.StringVar()
        self.usage_hours_var = tk.StringVar()
        self.usage_enabled_var = tk.BooleanVar(value=True)

        self.usage_device_combo = self._combo(left, "Materiel", self.usage_device_var)
        self.usage_slot_combo = self._combo(left, "Creneau", self.usage_slot_var)
        self._entry(left, "Heures/jour (h)", self.usage_hours_var)
        ttk.Checkbutton(left, text="Actif", variable=self.usage_enabled_var).pack(anchor="w", pady=(4, 8))

        act = ttk.Frame(left)
        act.pack(fill="x", pady=(8, 0))
        ttk.Button(act, text="Ajouter / Mettre a jour", command=lambda: self._safe(self.upsert_usage)).pack(side="left")
        ttk.Button(act, text="Rafraichir", command=lambda: self._safe(self.refresh_usage)).pack(side="left", padx=6)
        ttk.Button(act, text="Reinitialiser", command=lambda: self._safe(self.truncate_usage)).pack(side="left", padx=6)

        cols = ("id", "device", "slot", "hours", "consumption", "enabled")
        self.usage_tree = ttk.Treeview(right, columns=cols, show="headings", height=18)
        for col, title, width in [
            ("id", "ID", 60),
            ("device", "Materiel", 220),
            ("slot", "Creneau", 130),
            ("hours", "Heures", 90),
            ("consumption", "Conso Wh", 110),
            ("enabled", "Actif", 80),
        ]:
            self.usage_tree.heading(col, text=title)
            self.usage_tree.column(col, width=width, anchor="w")
        self.usage_tree.pack(fill="both", expand=True)

    def _build_history_tab(self) -> None:
        top = ttk.Frame(self.tab_history)
        top.pack(fill="x", pady=(0, 8))

        ttk.Label(top, text="Historique des depenses energetiques", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(top, text="Reinitialiser", command=lambda: self._safe(self.truncate_history)).pack(side="right", padx=(0, 6))
        ttk.Button(top, text="Rafraichir", command=lambda: self._safe(self.refresh_history)).pack(side="right")
        ttk.Button(top, text="Reinitialiser", command=lambda: self._safe(self.reset_history_data)).pack(side="right", padx=(0, 6))

        cols = ("id", "date", "device", "slot", "energy", "duration", "notes")
        self.history_tree = ttk.Treeview(self.tab_history, columns=cols, show="headings", height=20)
        for col, title, width in [
            ("id", "ID", 60),
            ("date", "Date", 100),
            ("device", "Materiel", 220),
            ("slot", "Creneau", 120),
            ("energy", "Energy Wh", 100),
            ("duration", "Duree h", 90),
            ("notes", "Notes", 320),
        ]:
            self.history_tree.heading(col, text=title)
            self.history_tree.column(col, width=width, anchor="w")
        self.history_tree.pack(fill="both", expand=True)

    def _build_panel_types_tab(self) -> None:
        left = ttk.LabelFrame(self.tab_panels, text="Type de panneau solaire", padding=10)
        left.pack(side="left", fill="y", padx=(0, 8))

        right = ttk.LabelFrame(self.tab_panels, text="Types et dimensionnement", padding=10)
        right.pack(side="left", fill="both", expand=True)

        self.panel_type_name_var = tk.StringVar()
        self.panel_type_pct_var = tk.StringVar()
        self.panel_type_energy_var = tk.StringVar()
        self.panel_type_price_var = tk.StringVar()
        self.panel_type_desc_var = tk.StringVar()

        self._entry(left, "Nom du type", self.panel_type_name_var)
        self._entry(left, "Capacite exploitable (%)", self.panel_type_pct_var)
        self._entry(left, "Energie unitaire (W)", self.panel_type_energy_var)
        self._entry(left, "Prix unitaire (Ar)", self.panel_type_price_var)
        self._entry(left, "Description", self.panel_type_desc_var)

        actions = ttk.Frame(left)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Ajouter", command=lambda: self._safe(self.add_panel_type)).pack(side="left")
        ttk.Button(actions, text="Rafraichir", command=lambda: self._safe(self.refresh_panel_types)).pack(side="left", padx=6)
        ttk.Button(actions, text="Reinitialiser", command=lambda: self._safe(self.truncate_panel_types)).pack(side="left", padx=6)

        ttk.Label(left, text="Besoin de reference (W)").pack(anchor="w", pady=(10, 0))
        ttk.Label(left, textvariable=self.panel_need_reference_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(left, text="Meilleure option").pack(anchor="w", pady=(10, 0))
        ttk.Label(left, textvariable=self.panel_recommendation_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(left, text="Ratio prix / energie").pack(anchor="w", pady=(10, 0))
        ttk.Label(left, textvariable=self.panel_ratio_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

        cols = ("id", "name", "pct", "energy", "usable", "price", "count", "supplied", "cost", "ratio", "best", "desc")
        self.panel_type_tree = ttk.Treeview(right, columns=cols, show="headings", height=18)
        for col, title, width in [
            ("id", "ID", 60),
            ("name", "Type", 150),
            ("pct", "Exploitable %", 110),
            ("energy", "Energie unitaire W", 130),
            ("usable", "Energie utile W", 130),
            ("price", "Prix unitaire Ar", 130),
            ("count", "Nb panneaux", 100),
            ("supplied", "Energie totale W", 130),
            ("cost", "Cout total Ar", 120),
            ("ratio", "Ratio Ar/W", 100),
            ("best", "Best", 70),
            ("desc", "Description", 240),
        ]:
            self.panel_type_tree.heading(col, text=title)
            self.panel_type_tree.column(col, width=width, anchor="w")
        self.panel_type_tree.pack(fill="both", expand=True)

    def _build_balance_tab(self) -> None:
        recap = ttk.LabelFrame(self.tab_balance, text="Recapitulatif avant calcul", padding=10)
        recap.pack(fill="x", pady=(0, 8))

        self.recap_device_var = tk.StringVar(value="0")
        self.recap_slot_var = tk.StringVar(value="0")
        self.recap_hours_var = tk.StringVar(value="0")

        ttk.Label(recap, text="Nombre d'appareils").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(recap, textvariable=self.recap_device_var, font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(recap, text="Creneaux configures").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(recap, textvariable=self.recap_slot_var, font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky="w")
        ttk.Label(recap, text="Duree totale usage (h)").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(recap, textvariable=self.recap_hours_var, font=("Segoe UI", 10, "bold")).grid(row=2, column=1, sticky="w")

        ttk.Button(recap, text="Generer les besoins energetiques", command=lambda: self._safe(self.generate_spec)).grid(
            row=0, column=2, rowspan=3, padx=(20, 0), sticky="nsew"
        )
        ttk.Button(recap, text="Reinitialiser tout", command=lambda: self._safe(self.reset_all_data)).grid(
            row=0, column=3, rowspan=3, padx=(8, 0), sticky="nsew"
        )

        cards = ttk.LabelFrame(self.tab_balance, text="Sorties principales", padding=10)
        cards.pack(fill="x", pady=(0, 8))

        self.total_var = tk.StringVar(value="0 Wh")
        self.panel_var = tk.StringVar(value="0 W")
        self.battery_var = tk.StringVar(value="0 Wh")
        self.day_need_var = tk.StringVar(value="0 Wh")
        self.evening_need_var = tk.StringVar(value="0 Wh")
        self.evening_solar_var = tk.StringVar(value="0 Wh")
        self.evening_battery_var = tk.StringVar(value="0 Wh")
        self.night_need_var = tk.StringVar(value="0 Wh")
        self.charge_window_var = tk.StringVar(value="0 h")
        self.charge_energy_var = tk.StringVar(value="0 W")
        self.panel_best_cost_var = tk.StringVar(value="0 Ar")
        self.panel_best_count_var = tk.StringVar(value="0")
        self.panel_best_energy_var = tk.StringVar(value="0 W")

        self._metric(cards, 0, "Depense totale", self.total_var)
        self._metric(cards, 1, "Panneaux requis", self.panel_var)
        self._metric(cards, 2, "Capacite batterie", self.battery_var)
        self._metric(cards, 3, "Cout option retenue", self.panel_best_cost_var)
        self._metric(cards, 4, "Energie retenue", self.panel_best_energy_var)

        calc_detail = ttk.LabelFrame(self.tab_balance, text="Detail des calculs", padding=10)
        calc_detail.pack(fill="x", pady=(0, 8))

        ttk.Label(calc_detail, text="Consommation JOUR").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.day_need_var, font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", pady=2)
        ttk.Label(calc_detail, text="Consommation SOIR").grid(row=0, column=2, sticky="w", padx=(20, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.evening_need_var, font=("Segoe UI", 10, "bold")).grid(row=0, column=3, sticky="w", pady=2)

        ttk.Label(calc_detail, text="SOIR fourni par panneaux (50%)").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.evening_solar_var, font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky="w", pady=2)
        ttk.Label(calc_detail, text="SOIR fourni par batterie (50%)").grid(row=1, column=2, sticky="w", padx=(20, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.evening_battery_var, font=("Segoe UI", 10, "bold")).grid(row=1, column=3, sticky="w", pady=2)

        ttk.Label(calc_detail, text="Consommation NUIT").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.night_need_var, font=("Segoe UI", 10, "bold")).grid(row=2, column=1, sticky="w", pady=2)
        ttk.Label(calc_detail, text="Besoin panneau a couvrir (W)").grid(row=2, column=2, sticky="w", padx=(20, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.panel_need_reference_var, font=("Segoe UI", 10, "bold")).grid(row=2, column=3, sticky="w", pady=2)

        ttk.Label(calc_detail, text="Fenetre de recharge batterie").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.charge_window_var, font=("Segoe UI", 10, "bold")).grid(row=3, column=1, sticky="w", pady=2)
        ttk.Label(calc_detail, text="Puissance de recharge batterie (W)").grid(row=3, column=2, sticky="w", padx=(20, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.charge_energy_var, font=("Segoe UI", 10, "bold")).grid(row=3, column=3, sticky="w", pady=2)

        ttk.Label(calc_detail, text="Option retenue").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.panel_recommendation_var, font=("Segoe UI", 10, "bold")).grid(row=4, column=1, sticky="w", pady=2)
        ttk.Label(calc_detail, text="Ratio prix / energie").grid(row=4, column=2, sticky="w", padx=(20, 8), pady=2)
        ttk.Label(calc_detail, textvariable=self.panel_ratio_var, font=("Segoe UI", 10, "bold")).grid(row=4, column=3, sticky="w", pady=2)

        detail = ttk.LabelFrame(self.tab_balance, text="Besoin en energie par tranche", padding=10)
        detail.pack(fill="both", expand=True)

        cols = ("slot", "need")
        self.balance_tree = ttk.Treeview(detail, columns=cols, show="headings", height=8)
        self.balance_tree.heading("slot", text="Tranche")
        self.balance_tree.heading("need", text="Besoin Wh")
        self.balance_tree.column("slot", width=220, anchor="w")
        self.balance_tree.column("need", width=200, anchor="w")
        self.balance_tree.pack(fill="both", expand=True)

    def _build_config_tab(self) -> None:
        left = ttk.LabelFrame(self.tab_config, text="Gestion des configurations", padding=10)
        left.pack(side="left", fill="y", padx=(0, 8))

        right = ttk.LabelFrame(self.tab_config, text="Liste des configurations", padding=10)
        right.pack(side="left", fill="both", expand=True)

        self.config_grid_voltage_var = tk.StringVar()
        self.config_efficiency_var = tk.StringVar()
        self.config_battery_var = tk.StringVar()
        self.config_desc_var = tk.StringVar()
        self.config_active_var = tk.BooleanVar(value=False)

        self._entry(left, "Tension secteur (V)", self.config_grid_voltage_var)
        self._entry(left, "Rendement global (%) - info", self.config_efficiency_var)
        self._entry(left, "Marge batterie (%)", self.config_battery_var)
        self._entry(left, "Description", self.config_desc_var)
        ttk.Checkbutton(left, text="Activer cette configuration", variable=self.config_active_var).pack(anchor="w", pady=(4, 8))

        actions = ttk.Frame(left)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Ajouter", command=lambda: self._safe(self.add_configuration)).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=2)
        ttk.Button(actions, text="Mettre a jour", command=lambda: self._safe(self.update_configuration)).grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=2)
        ttk.Button(actions, text="Supprimer", command=lambda: self._safe(self.delete_configuration)).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=2)
        ttk.Button(actions, text="Activer", command=lambda: self._safe(self.set_active_configuration)).grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=2)
        ttk.Button(actions, text="Reinitialiser", command=lambda: self._safe(self.truncate_configurations)).grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=2)
        ttk.Button(actions, text="Rafraichir", command=lambda: self._safe(self.refresh_configurations)).grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=2)
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        cols = ("id", "voltage", "efficiency", "battery", "active", "created", "updated", "desc")
        self.config_tree = ttk.Treeview(right, columns=cols, show="headings", height=18)
        for col, title, width in [
            ("id", "ID", 60),
            ("voltage", "Voltage V", 90),
            ("efficiency", "Rendement %", 100),
            ("battery", "Batterie %", 100),
            ("active", "Active", 80),
            ("created", "Creee le", 150),
            ("updated", "Modifiee le", 150),
            ("desc", "Description", 280),
        ]:
            self.config_tree.heading(col, text=title)
            self.config_tree.column(col, width=width, anchor="w")
        self.config_tree.pack(fill="both", expand=True)
        self.config_tree.bind("<<TreeviewSelect>>", lambda _event: self._on_config_select())

    def _entry(self, parent: ttk.Frame, label: str, var: tk.StringVar) -> ttk.Entry:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(4, 0))
        entry = ttk.Entry(parent, textvariable=var, width=36)
        entry.pack(fill="x")
        return entry

    def _combo(
        self,
        parent: ttk.Frame,
        label: str,
        var: tk.StringVar,
        values: list[str] | None = None,
    ) -> ttk.Combobox:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(4, 0))
        combo = ttk.Combobox(parent, textvariable=var, values=values or [], state="readonly", width=33)
        combo.pack(fill="x")
        return combo

    def _metric(self, parent: ttk.Frame, col: int, title: str, value_var: tk.StringVar) -> None:
        box = ttk.Frame(parent, padding=(12, 10))
        box.grid(row=0, column=col, sticky="nsew", padx=6)
        parent.grid_columnconfigure(col, weight=1)
        ttk.Label(box, text=title).pack(anchor="w")
        ttk.Label(box, textvariable=value_var, font=("Segoe UI", 14, "bold")).pack(anchor="w")

    def _on_config_select(self) -> None:
        selection = self.config_tree.selection()
        if not selection:
            return
        values = self.config_tree.item(selection[0], "values")
        if not values:
            return
        self.selected_config_id = int(values[0])
        self.config_grid_voltage_var.set(str(values[1]))
        self.config_efficiency_var.set(str(values[2]))
        self.config_battery_var.set(str(values[3]))
        self.config_active_var.set(str(values[4]).strip().upper() in {"1", "TRUE", "YES", "OUI"})
        self.config_desc_var.set(values[7] if len(values) > 7 and values[7] is not None else "")

    def _clear_config_form(self) -> None:
        self.selected_config_id = None
        self.config_grid_voltage_var.set("")
        self.config_efficiency_var.set("")
        self.config_battery_var.set("")
        self.config_desc_var.set("")
        self.config_active_var.set(False)

    @staticmethod
    def _timeslot_duration_hours(start_hour: int, end_hour: int) -> float:
        if end_hour > start_hour:
            return float(end_hour - start_hour)
        return float((24 - start_hour) + end_hour)

    def _safe(self, fn) -> None:
        try:
            fn()
        except Exception as exc:
            try:
                self.connector.rollback()
            except Exception:
                pass
            self.status_var.set(f"Erreur: {exc}")
            messagebox.showerror("Erreur", str(exc))

    def refresh_all(self) -> None:
        self.refresh_device_types()
        self.refresh_devices()
        self.refresh_slots()
        self.refresh_usage()
        self.refresh_history()
        self.refresh_configurations()
        self.refresh_panel_types()
        self.refresh_recap()
        self._update_step_lock()
        self.status_var.set("Donnees chargees")

    def _update_step_lock(self) -> None:
        devices = int(self.recap_device_var.get())
        slots = int(self.recap_slot_var.get())
        if devices == 0:
            self.notebook.tab(2, state="disabled")
            self.notebook.tab(3, state="disabled")
            self.notebook.tab(4, state="disabled")
        elif slots == 0:
            self.notebook.tab(2, state="disabled")
            self.notebook.tab(3, state="normal")
            self.notebook.tab(4, state="disabled")
        else:
            self.notebook.tab(2, state="normal")
            self.notebook.tab(3, state="normal")
            self.notebook.tab(4, state="normal")

    def refresh_device_types(self) -> None:
        rows = self.device_type_crud.list_types_with_role()
        self.device_type_map = {name: type_id for type_id, name, _, _ in rows}
        self.device_type_role_map = {name: role for _, name, _, role in rows}
        names = list(self.device_type_map.keys())
        self.device_type_combo["values"] = names
        if names and not self.device_type_var.get():
            self.device_type_var.set(names[0])
        self._update_selected_type_role()

    def _update_selected_type_role(self) -> None:
        selected = self.device_type_var.get().strip()
        self.device_role_var.set(self.device_type_role_map.get(selected, "-"))

    def refresh_devices(self) -> None:
        rows = self.device_crud.list_devices()
        self.device_tree.delete(*self.device_tree.get_children())
        for row in rows:
            display_row = (row[0], row[1], row[2], row[3], row[5], row[6], row[7], row[8])
            self.device_tree.insert("", "end", values=display_row)

        usage_rows = self.device_crud.list_consumer_devices()
        self.device_map.clear()
        labels = []
        for device_id, device_code, device_name in usage_rows:
            label = f"{device_name} ({device_code})"
            self.device_map[label] = device_id
            labels.append(label)
        self.usage_device_combo["values"] = labels
        if labels and not self.usage_device_var.get():
            self.usage_device_var.set(labels[0])

    def refresh_slots(self) -> None:
        rows = self.timeslot_crud.list_timeslots()
        self.slot_tree.delete(*self.slot_tree.get_children())
        self.slot_map.clear()
        self.slot_duration_map.clear()
        labels = []
        for row in rows:
            self.slot_tree.insert("", "end", values=row)
            label = f"{row[1]} ({row[2]}-{row[3]})"
            self.slot_map[label] = row[0]
            self.slot_duration_map[label] = self._timeslot_duration_hours(int(row[2]), int(row[3]))
            labels.append(label)
        self.usage_slot_combo["values"] = labels
        if labels and not self.usage_slot_var.get():
            self.usage_slot_var.set(labels[0])

    def refresh_usage(self) -> None:
        rows = self.usage_crud.list_usage()
        self.usage_tree.delete(*self.usage_tree.get_children())
        for row in rows:
            self.usage_tree.insert("", "end", values=row)

    def refresh_history(self) -> None:
        rows = self.history_crud.list_history(limit=200)
        self.history_tree.delete(*self.history_tree.get_children())
        for row in rows:
            self.history_tree.insert("", "end", values=row)

    def refresh_panel_types(self) -> None:
        rows = self.panel_type_crud.list_panel_types()
        self.panel_type_tree.delete(*self.panel_type_tree.get_children())
        self.panel_need_reference_var.set(f"{self.last_panel_need_w:.2f} W")
        comparison = self.spec_service.build_panel_options(rows, self.last_panel_need_w)
        self.panel_options = comparison.get("options", [])
        self.panel_best_option = comparison.get("best_option")

        if self.panel_best_option:
            self.panel_recommendation_var.set(
                f"{self.panel_best_option['type_name']} | {int(self.panel_best_option['panel_count'])} panneaux | {float(self.panel_best_option['total_cost_ar']):.2f} Ar"
            )
            self.panel_ratio_var.set(f"{float(self.panel_best_option['ratio_price_per_energy']):.2f} Ar/W")
            self.panel_best_cost_var.set(f"{float(self.panel_best_option['total_cost_ar']):.2f} Ar")
            self.panel_best_count_var.set(str(int(self.panel_best_option['panel_count'])))
            self.panel_best_energy_var.set(f"{float(self.panel_best_option['supplied_energy_w']):.2f} W")
        else:
            self.panel_recommendation_var.set("Aucune recommandation")
            self.panel_ratio_var.set("0.00 Ar/W")
            self.panel_best_cost_var.set("0 Ar")
            self.panel_best_count_var.set("0")
            self.panel_best_energy_var.set("0 W")

        for option in self.panel_options:
            self.panel_type_tree.insert(
                "",
                "end",
                values=(
                    option["panel_type_id"],
                    option["type_name"],
                    f"{float(option['exploitable_pct']):.2f}",
                    f"{float(option['unit_energy_w']):.2f}",
                    f"{float(option['usable_energy_w']):.2f}",
                    f"{float(option['unit_price_ar']):.2f}",
                    str(int(option["panel_count"])),
                    f"{float(option['supplied_energy_w']):.2f}",
                    f"{float(option['total_cost_ar']):.2f}",
                    f"{float(option['ratio_price_per_energy']):.2f}",
                    "Oui" if self.panel_best_option and option["panel_type_id"] == self.panel_best_option["panel_type_id"] else "",
                    option["description"],
                ),
            )

    def add_panel_type(self) -> None:
        type_name = self.panel_type_name_var.get().strip()
        exploitable_pct = float(self.panel_type_pct_var.get())
        unit_energy_w = float(self.panel_type_energy_var.get())
        unit_price_ar = float(self.panel_type_price_var.get())
        description = self.panel_type_desc_var.get().strip() or None

        if not type_name:
            raise ValueError("Le nom du type de panneau est obligatoire.")
        if exploitable_pct <= 0 or exploitable_pct > 100:
            raise ValueError("La capacite exploitable doit etre comprise entre 0 et 100.")
        if unit_energy_w <= 0:
            raise ValueError("L'energie unitaire doit etre superieure a 0.")
        if unit_price_ar < 0:
            raise ValueError("Le prix unitaire doit etre superieur ou egal a 0.")

        self.panel_type_crud.create_panel_type(
            type_name=type_name,
            exploitable_pct=exploitable_pct,
            unit_energy_w=unit_energy_w,
            unit_price_ar=unit_price_ar,
            description=description,
        )

        self.refresh_panel_types()
        self.status_var.set("Type de panneau ajoute")

    def refresh_configurations(self) -> None:
        rows = self.config_crud.get_all()
        self.config_tree.delete(*self.config_tree.get_children())
        active_item = None

        for row in rows:
            active_text = "Oui" if row[5] else "Non"
            created_at = row[6].strftime("%Y-%m-%d %H:%M") if row[6] else ""
            updated_at = row[7].strftime("%Y-%m-%d %H:%M") if row[7] else ""
            item_id = self.config_tree.insert(
                "",
                "end",
                values=(row[0], f"{float(row[1]):.2f}", f"{float(row[2]):.2f}", f"{float(row[3]):.2f}", active_text, created_at, updated_at, row[4] or ""),
            )
            if row[5]:
                active_item = item_id

        if active_item is not None:
            self.config_tree.selection_set(active_item)
            self.config_tree.focus(active_item)
            self._on_config_select()
        elif rows:
            first_item = self.config_tree.get_children()[0]
            self.config_tree.selection_set(first_item)
            self.config_tree.focus(first_item)
            self._on_config_select()
        else:
            self._clear_config_form()

    def refresh_recap(self) -> None:
        self.recap_device_var.set(str(self.device_crud.count_devices()))
        self.recap_slot_var.set(str(self.timeslot_crud.count_timeslots()))
        self.recap_hours_var.set(f"{self.usage_crud.sum_enabled_usage_hours():.2f}")

    def add_configuration(self) -> None:
        grid_voltage = float(self.config_grid_voltage_var.get())
        solar_efficiency = float(self.config_efficiency_var.get())
        battery_overcapacity = float(self.config_battery_var.get())
        description = self.config_desc_var.get().strip() or None

        if grid_voltage <= 0:
            raise ValueError("La tension secteur doit etre superieure a 0.")
        if solar_efficiency <= 0 or solar_efficiency > 100:
            raise ValueError("Le rendement panneaux doit etre compris entre 0 et 100.")
        if battery_overcapacity <= 0:
            raise ValueError("La marge batterie doit etre superieure a 0.")

        config_id = self.config_crud.create(
            grid_voltage=grid_voltage,
            solar_efficiency=solar_efficiency,
            battery_overcapacity=battery_overcapacity,
            description=description,
            is_active=False,
        )

        if self.config_active_var.get():
            self.config_crud.set_active(config_id)

        self.refresh_configurations()
        self.status_var.set("Configuration ajoutee")

    def update_configuration(self) -> None:
        if self.selected_config_id is None:
            raise ValueError("Selectionne une configuration dans la liste.")

        grid_voltage = float(self.config_grid_voltage_var.get())
        solar_efficiency = float(self.config_efficiency_var.get())
        battery_overcapacity = float(self.config_battery_var.get())
        description = self.config_desc_var.get().strip() or None

        if grid_voltage <= 0:
            raise ValueError("La tension secteur doit etre superieure a 0.")
        if solar_efficiency <= 0 or solar_efficiency > 100:
            raise ValueError("Le rendement panneaux doit etre compris entre 0 et 100.")
        if battery_overcapacity <= 0:
            raise ValueError("La marge batterie doit etre superieure a 0.")

        self.config_crud.update(
            self.selected_config_id,
            grid_voltage=grid_voltage,
            solar_efficiency=solar_efficiency,
            battery_overcapacity=battery_overcapacity,
            description=description,
        )

        if self.config_active_var.get():
            self.config_crud.set_active(self.selected_config_id)
        else:
            self.config_crud.update(self.selected_config_id, is_active=False)

        self.refresh_configurations()
        self.status_var.set("Configuration mise a jour")

    def delete_configuration(self) -> None:
        if self.selected_config_id is None:
            raise ValueError("Selectionne une configuration dans la liste.")

        config = self.config_crud.get_by_id(self.selected_config_id)
        if config is None:
            raise ValueError("Configuration introuvable.")

        if not messagebox.askyesno("Confirmation", "Supprimer cette configuration ?"):
            return

        was_active = bool(config[5])
        self.config_crud.delete(self.selected_config_id)
        self.refresh_configurations()

        if was_active:
            remaining = self.config_crud.get_all()
            if remaining:
                self.config_crud.set_active(int(remaining[0][0]))
                self.refresh_configurations()

        self.status_var.set("Configuration supprimee")

    def set_active_configuration(self) -> None:
        if self.selected_config_id is None:
            raise ValueError("Selectionne une configuration dans la liste.")

        self.config_crud.set_active(self.selected_config_id)
        self.refresh_configurations()
        self.status_var.set("Configuration activee")

    def truncate_configurations(self) -> None:
        if not messagebox.askyesno("Confirmation", "Vider toutes les configurations ?"):
            return

        self.config_crud.truncate()
        self.refresh_configurations()
        self.status_var.set("Table des configurations reinitialisee")

    def truncate_devices(self) -> None:
        if not messagebox.askyesno("Confirmation", "Vider tous les materiels et leurs dependances (usage, historique) ?"):
            return

        self.device_crud.truncate()
        self.refresh_devices()
        self.refresh_usage()
        self.refresh_history()
        self.status_var.set("Table des materiels et dependances reinitialisee")

    def truncate_slots(self) -> None:
        if not messagebox.askyesno("Confirmation", "Vider tous les creneaux et leurs dependances (usage, historique) ?"):
            return

        self.timeslot_crud.truncate()
        self.refresh_slots()
        self.refresh_usage()
        self.refresh_history()
        self.status_var.set("Table des creneaux et dependances reinitialisee")

    def truncate_usage(self) -> None:
        if not messagebox.askyesno("Confirmation", "Vider tous les usages ?"):
            return

        self.usage_crud.truncate()
        self.refresh_usage()
        self.status_var.set("Table des usages reinitialisee")

    def truncate_history(self) -> None:
        if not messagebox.askyesno("Confirmation", "Vider tout l'historique de consommation ?"):
            return

        self.history_crud.truncate()
        self.refresh_history()
        self.status_var.set("Table d'historique reinitialisee")

    def truncate_panel_types(self) -> None:
        if not messagebox.askyesno("Confirmation", "Vider tous les types de panneaux ?"):
            return

        self.panel_type_crud.truncate()
        self.refresh_panel_types()
        self.status_var.set("Table des types de panneaux reinitialisee")

    def add_device(self) -> None:
        code = self.device_code_var.get().strip()
        name = self.device_name_var.get().strip()
        dtype_name = self.device_type_var.get().strip()
        power = float(self.device_power_var.get())
        install_date = self.device_date_var.get().strip()
        status = self.device_status_var.get().strip()

        if not code or not name:
            raise ValueError("Code et nom sont obligatoires.")
        if dtype_name not in self.device_type_map:
            raise ValueError("Type de materiel invalide.")
        if power <= 0:
            raise ValueError("Puissance invalide.")

        self.device_crud.create_device(
            code=code,
            name=name,
            device_type_id=self.device_type_map[dtype_name],
            power_w=power,
            description=self.device_desc_var.get().strip() or None,
            installation_date=install_date,
            status=status,
        )

        self.refresh_devices()
        self.refresh_recap()
        self._update_step_lock()
        self.status_var.set("Materiel ajoute")

    def add_slot(self) -> None:
        name = self.slot_name_var.get().strip()
        start = int(self.slot_start_var.get())
        end = int(self.slot_end_var.get())

        if not name:
            raise ValueError("Nom du creneau obligatoire.")
        if start < 0 or start > 23 or end < 1 or end > 24:
            raise ValueError("Heures invalides: debut 0-23, fin 1-24.")

        self.timeslot_crud.create_timeslot(name=name, start_hour=start, end_hour=end, description=self.slot_desc_var.get().strip() or None)

        self.refresh_slots()
        self.refresh_recap()
        self._update_step_lock()
        self.status_var.set("Creneau ajoute")

    def upsert_usage(self) -> None:
        device_label = self.usage_device_var.get().strip()
        slot_label = self.usage_slot_var.get().strip()
        hours = float(self.usage_hours_var.get())
        enabled = 1 if self.usage_enabled_var.get() else 0

        if device_label not in self.device_map:
            raise ValueError("Selection du materiel invalide.")
        if slot_label not in self.slot_map:
            raise ValueError("Selection du creneau invalide.")
        max_slot_hours = self.slot_duration_map.get(slot_label)
        if max_slot_hours is None:
            raise ValueError("Duree du creneau introuvable.")
        if hours < 0:
            raise ValueError("DailyUsageHours doit etre superieur ou egal a 0.")
        if hours > max_slot_hours:
            raise ValueError(f"DailyUsageHours depasse la duree du creneau selectionne ({max_slot_hours:.2f} h max).")

        self.usage_crud.upsert_usage(
            device_id=self.device_map[device_label],
            timeslot_id=self.slot_map[slot_label],
            daily_usage_hours=hours,
            is_enabled=enabled,
        )

        self.refresh_usage()
        self.refresh_recap()
        self.status_var.set("Usage enregistre")

    def generate_spec(self) -> None:
        self.refresh_recap()

        if int(self.recap_device_var.get()) == 0:
            raise ValueError("Ajoute au moins un materiel avant generation.")
        if int(self.recap_slot_var.get()) == 0:
            raise ValueError("Ajoute au moins un creneau avant generation.")

        slot_rows = self.usage_crud.list_consumption_by_slot()
        slot_hours_by_name = {
            str(row[1]).strip().upper(): self._timeslot_duration_hours(int(row[2]), int(row[3]))
            for row in self.timeslot_crud.list_timeslots()
        }
        active_config = self.config_crud.get_active()
        if not active_config:
            raise ValueError("Aucune configuration active dans SystemConfiguration.")

        spec = self.spec_service.build_spec(
            slot_rows,
            float(active_config[2]),
            float(active_config[3]),
            slot_hours_by_name=slot_hours_by_name,
        )

        self.total_var.set(f"{spec['total_wh']:.2f} Wh")
        self.panel_var.set(f"{spec['panel_w']:.2f} W")
        self.last_panel_need_w = float(spec['panel_w'])
        self.battery_var.set(f"{spec['battery_wh']:.2f} Wh")
        self.charge_window_var.set(f"{spec['charge_window_hours']:.2f} h")
        charge_power_w = spec['battery_wh'] / spec['charge_window_hours'] if spec['charge_window_hours'] > 0 else 0.0
        self.charge_energy_var.set(f"{charge_power_w:.2f} W")

        by_slot = spec.get("by_slot", {})
        self.day_need_var.set(f"{float(by_slot.get('JOUR', 0.0)):.2f} Wh")
        self.evening_need_var.set(f"{float(by_slot.get('SOIR', 0.0)):.2f} Wh")
        self.evening_solar_var.set(f"{float(spec.get('evening_solar_wh', 0.0)):.2f} Wh")
        self.evening_battery_var.set(f"{float(spec.get('evening_battery_wh', 0.0)):.2f} Wh")
        self.night_need_var.set(f"{float(by_slot.get('NUIT', 0.0)):.2f} Wh")

        self.balance_tree.delete(*self.balance_tree.get_children())
        for name, wh in spec["rows_wh"]:
            self.balance_tree.insert("", "end", values=(name, f"{float(wh):.2f}"))

        self.refresh_panel_types()

        self.status_var.set("Bilan energetique genere")

    def _clear_balance_outputs(self) -> None:
        self.total_var.set("0 Wh")
        self.panel_var.set("0 W")
        self.battery_var.set("0 Wh")
        self.balance_tree.delete(*self.balance_tree.get_children())

    def reset_devices_data(self) -> None:
        if not messagebox.askyesno(
            "Confirmation",
            "Reinitialiser les materiels ? Cela supprimera aussi Usage et Historique lies aux materiels.",
        ):
            return

        self.device_crud.truncate_devices_with_dependents()
        self._clear_balance_outputs()
        self.refresh_all()
        self.status_var.set("Materiels reinitialises (avec tables dependantes)")

    def reset_slots_data(self) -> None:
        if not messagebox.askyesno(
            "Confirmation",
            "Reinitialiser les creneaux ? Cela supprimera aussi Usage, Historique, Production solaire et mouvements batterie.",
        ):
            return

        self.timeslot_crud.truncate_timeslots_with_dependents()
        self._clear_balance_outputs()
        self.refresh_all()
        self.status_var.set("Creneaux reinitialises (avec tables dependantes)")

    def reset_usage_data(self) -> None:
        if not messagebox.askyesno("Confirmation", "Reinitialiser toutes les lignes d'usage ?"):
            return

        self.usage_crud.truncate_usage()
        self._clear_balance_outputs()
        self.refresh_all()
        self.status_var.set("Usage reinitialise")

    def reset_history_data(self) -> None:
        if not messagebox.askyesno("Confirmation", "Reinitialiser l'historique de consommation ?"):
            return

        self.history_crud.truncate_history()
        self._clear_balance_outputs()
        self.refresh_all()
        self.status_var.set("Historique reinitialise")

    def reset_all_data(self) -> None:
        if not messagebox.askyesno(
            "Confirmation",
            "Reinitialiser toutes les donnees des onglets (Materiels, Creneaux, Usage, Historique) ?\n"
            "Les types de materiels ne seront pas supprimes.",
        ):
            return

        self.device_crud.truncate_devices_with_dependents()
        self.timeslot_crud.truncate_timeslots_with_dependents()
        self._clear_balance_outputs()
        self.refresh_all()
        self.status_var.set("Toutes les donnees des onglets ont ete reinitialisees")

    def _on_close(self) -> None:
        self.connector.Disconnect()
        self.root.destroy()