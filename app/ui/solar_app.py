from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk

from app.crud.device import DeviceCrud
from app.crud.device_type import DeviceTypeCrud
from app.crud.device_usage_schedule import DeviceUsageScheduleCrud
from app.crud.energy_consumption import EnergyConsumptionCrud
from app.crud.system_configuration import SystemConfigurationCrud
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
        self.system_config_crud = SystemConfigurationCrud(connector)
        self.spec_service = EnergySpecService()

        self.device_map: dict[str, int] = {}
        self.slot_map: dict[str, int] = {}
        self.device_type_map: dict[str, int] = {}
        self.device_type_role_map: dict[str, str] = {}
        self.slot_duration_map: dict[str, float] = {}

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

        self.notebook.add(self.tab_devices, text="Materiels")
        self.notebook.add(self.tab_slots, text="Creneaux")
        self.notebook.add(self.tab_usage, text="Usage")
        self.notebook.add(self.tab_history, text="Historique")
        self.notebook.add(self.tab_balance, text="Bilan")

        self._build_devices_tab()
        self._build_slots_tab()
        self._build_usage_tab()
        self._build_history_tab()
        self._build_balance_tab()

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
        ttk.Button(act, text="Reinitialiser", command=lambda: self._safe(self.reset_devices_data)).pack(side="left")

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
        ttk.Button(act, text="Reinitialiser", command=lambda: self._safe(self.reset_slots_data)).pack(side="left")

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
        ttk.Button(act, text="Reinitialiser", command=lambda: self._safe(self.reset_usage_data)).pack(side="left")

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

        self._metric(cards, 0, "Besoin total", self.total_var)
        self._metric(cards, 1, "Panneaux requis", self.panel_var)
        self._metric(cards, 2, "Spec batterie", self.battery_var)

        detail = ttk.LabelFrame(self.tab_balance, text="Besoin en energie par tranche", padding=10)
        detail.pack(fill="both", expand=True)

        cols = ("slot", "wh")
        self.balance_tree = ttk.Treeview(detail, columns=cols, show="headings", height=8)
        self.balance_tree.heading("slot", text="Tranche")
        self.balance_tree.heading("wh", text="Besoin Wh")
        self.balance_tree.column("slot", width=220, anchor="w")
        self.balance_tree.column("wh", width=160, anchor="w")
        self.balance_tree.pack(fill="both", expand=True)

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

    def refresh_recap(self) -> None:
        self.recap_device_var.set(str(self.device_crud.count_devices()))
        self.recap_slot_var.set(str(self.timeslot_crud.count_timeslots()))
        self.recap_hours_var.set(f"{self.usage_crud.sum_enabled_usage_hours():.2f}")

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
        active_config = self.system_config_crud.get_active_config()
        if not active_config:
            raise ValueError("Aucune configuration active dans SystemConfiguration.")

        spec = self.spec_service.build_spec(slot_rows, active_config[0], active_config[1])

        self.total_var.set(f"{spec['total_wh']:.2f} Wh")
        self.panel_var.set(f"{spec['panel_w']:.2f} W")
        self.battery_var.set(f"{spec['battery_wh']:.2f} Wh")

        self.balance_tree.delete(*self.balance_tree.get_children())
        for name, wh in spec["rows"]:
            self.balance_tree.insert("", "end", values=(name, f"{float(wh):.2f}"))

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
