import os
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from connection import ServerConnect


def load_dotenv_file(dotenv_path: str = ".env") -> None:
    """Load .env key/value pairs into process environment if available."""
    path = Path(dotenv_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / dotenv_path

    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


def normalize_sql_host_for_local_run() -> None:
    """Use localhost when docker service hostname is loaded on host OS."""
    host = os.getenv("SQL_SERVER_HOST", "").strip().lower()
    if host == "sqlserver":
        os.environ["SQL_SERVER_HOST"] = "127.0.0.1"


class SolarApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Solar - Gestion energetique")
        self.root.geometry("1220x760")

        self.connector = ServerConnect()

        self.device_map: dict[str, int] = {}
        self.slot_map: dict[str, int] = {}
        self.device_type_map: dict[str, int] = {}

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

        self._entry(left, "Code", self.device_code_var)
        self._entry(left, "Nom", self.device_name_var)
        self.device_type_combo = self._combo(left, "Type", self.device_type_var)
        self._entry(left, "Puissance (W)", self.device_power_var)
        self._entry(left, "Date installation (YYYY-MM-DD)", self.device_date_var)
        self._combo(left, "Statut", self.device_status_var, ["ACTIF", "INACTIF", "MAINTEN"])
        self._entry(left, "Description", self.device_desc_var)

        act = ttk.Frame(left)
        act.pack(fill="x", pady=(8, 0))
        ttk.Button(act, text="Ajouter", command=lambda: self._safe(self.add_device)).pack(side="left")
        ttk.Button(act, text="Rafraichir", command=lambda: self._safe(self.refresh_devices)).pack(side="left", padx=6)

        cols = ("id", "code", "name", "type", "power", "status", "date")
        self.device_tree = ttk.Treeview(right, columns=cols, show="headings", height=18)
        for col, title, width in [
            ("id", "ID", 60),
            ("code", "Code", 100),
            ("name", "Materiel", 220),
            ("type", "Type", 140),
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

    def _query(self, sql: str, params: tuple = ()) -> list[tuple]:
        conn = self.connector.getConnection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def _exec(self, sql: str, params: tuple = ()) -> None:
        conn = self.connector.getConnection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
        self.connector.commit()

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
        rows = self._query("SELECT DeviceTypeId, TypeName FROM DeviceType ORDER BY TypeName")
        self.device_type_map = {name: type_id for type_id, name in rows}
        names = list(self.device_type_map.keys())
        self.device_type_combo["values"] = names
        if names and not self.device_type_var.get():
            self.device_type_var.set(names[0])

    def refresh_devices(self) -> None:
        rows = self._query(
            """
            SELECT d.DeviceId, d.DeviceCode, d.DeviceName, dt.TypeName, d.PowerW, d.Status, d.InstallationDate
            FROM Device d
            INNER JOIN DeviceType dt ON dt.DeviceTypeId = d.DeviceTypeId
            ORDER BY d.DeviceName
            """
        )
        self.device_tree.delete(*self.device_tree.get_children())
        self.device_map.clear()
        labels = []
        for row in rows:
            self.device_tree.insert("", "end", values=row)
            label = f"{row[2]} ({row[1]})"
            self.device_map[label] = row[0]
            labels.append(label)
        self.usage_device_combo["values"] = labels
        if labels and not self.usage_device_var.get():
            self.usage_device_var.set(labels[0])

    def refresh_slots(self) -> None:
        rows = self._query("SELECT TimeSlotId, SlotName, StartHour, EndHour, ISNULL(Description, '') FROM TimeSlot ORDER BY TimeSlotId")
        self.slot_tree.delete(*self.slot_tree.get_children())
        self.slot_map.clear()
        labels = []
        for row in rows:
            self.slot_tree.insert("", "end", values=row)
            label = f"{row[1]} ({row[2]}-{row[3]})"
            self.slot_map[label] = row[0]
            labels.append(label)
        self.usage_slot_combo["values"] = labels
        if labels and not self.usage_slot_var.get():
            self.usage_slot_var.set(labels[0])

    def refresh_usage(self) -> None:
        rows = self._query(
            """
            SELECT dus.UsageScheduleId, d.DeviceName, ts.SlotName, dus.DailyUsageHours,
                   (d.PowerW * dus.DailyUsageHours) AS DailyEnergyConsumptionWh,
                   dus.IsEnabled
            FROM DeviceUsageSchedule dus
            INNER JOIN Device d ON d.DeviceId = dus.DeviceId
            INNER JOIN TimeSlot ts ON ts.TimeSlotId = dus.TimeSlotId
            ORDER BY d.DeviceName, ts.TimeSlotId
            """
        )
        self.usage_tree.delete(*self.usage_tree.get_children())
        for row in rows:
            self.usage_tree.insert("", "end", values=row)

    def refresh_history(self) -> None:
        rows = self._query(
            """
            SELECT TOP 200 ec.ConsumptionId, ec.ConsumptionDate, d.DeviceName, ts.SlotName,
                   ec.EnergyConsumedWh, ec.DurationHours, ISNULL(ec.Notes, '')
            FROM EnergyConsumption ec
            INNER JOIN Device d ON d.DeviceId = ec.DeviceId
            INNER JOIN TimeSlot ts ON ts.TimeSlotId = ec.TimeSlotId
            ORDER BY ec.ConsumptionDate DESC, ec.ConsumptionId DESC
            """
        )
        self.history_tree.delete(*self.history_tree.get_children())
        for row in rows:
            self.history_tree.insert("", "end", values=row)

    def refresh_recap(self) -> None:
        device_count = self._query("SELECT COUNT(*) FROM Device")[0][0]
        slot_count = self._query("SELECT COUNT(*) FROM TimeSlot")[0][0]
        usage_hours = self._query("SELECT ISNULL(SUM(DailyUsageHours), 0) FROM DeviceUsageSchedule WHERE IsEnabled = 1")[0][0]

        self.recap_device_var.set(str(device_count))
        self.recap_slot_var.set(str(slot_count))
        self.recap_hours_var.set(f"{float(usage_hours):.2f}")

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

        self._exec(
            """
            INSERT INTO Device(DeviceCode, DeviceName, DeviceTypeId, PowerW, Description, InstallationDate, Status)
            VALUES(%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                code,
                name,
                self.device_type_map[dtype_name],
                power,
                self.device_desc_var.get().strip() or None,
                install_date,
                status,
            ),
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

        self._exec(
            "INSERT INTO TimeSlot(SlotName, StartHour, EndHour, Description) VALUES(%s, %s, %s, %s)",
            (name, start, end, self.slot_desc_var.get().strip() or None),
        )

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
        if hours < 0 or hours > 24:
            raise ValueError("DailyUsageHours doit etre entre 0 et 24.")

        device_id = self.device_map[device_label]
        slot_id = self.slot_map[slot_label]

        self._exec(
            """
            IF EXISTS (SELECT 1 FROM DeviceUsageSchedule WHERE DeviceId = %s AND TimeSlotId = %s)
                UPDATE DeviceUsageSchedule
                SET DailyUsageHours = %s, IsEnabled = %s
                WHERE DeviceId = %s AND TimeSlotId = %s
            ELSE
                INSERT INTO DeviceUsageSchedule(DeviceId, TimeSlotId, DailyUsageHours, IsEnabled)
                VALUES(%s, %s, %s, %s)
            """,
            (device_id, slot_id, hours, enabled, device_id, slot_id, device_id, slot_id, hours, enabled),
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

        slot_rows = self._query(
            """
            SELECT ts.SlotName, ISNULL(SUM(d.PowerW * dus.DailyUsageHours), 0) AS ConsumptionWh
            FROM TimeSlot ts
            LEFT JOIN DeviceUsageSchedule dus ON dus.TimeSlotId = ts.TimeSlotId AND dus.IsEnabled = 1
            LEFT JOIN Device d ON d.DeviceId = dus.DeviceId
            GROUP BY ts.SlotName
            ORDER BY ts.TimeSlotId
            """
        )

        cfg = self._query(
            """
            SELECT TOP 1 SolarPanelEfficiencyPct, BatteryOvercapacityPct
            FROM SystemConfiguration
            WHERE IsActive = 1
            ORDER BY ConfigId DESC
            """
        )
        if not cfg:
            raise ValueError("Aucune configuration active dans SystemConfiguration.")

        eff_pct, battery_pct = cfg[0]
        by_slot = {name: float(wh) for name, wh in slot_rows}
        total_wh = sum(by_slot.values())
        night_wh = by_slot.get("NUIT", 0.0)

        panel_w = 0.0 if float(eff_pct) <= 0 else total_wh * 100.0 / float(eff_pct)
        battery_wh = night_wh * (1.0 + float(battery_pct) / 100.0)

        self.total_var.set(f"{total_wh:.2f} Wh")
        self.panel_var.set(f"{panel_w:.2f} W")
        self.battery_var.set(f"{battery_wh:.2f} Wh")

        self.balance_tree.delete(*self.balance_tree.get_children())
        for name, wh in slot_rows:
            self.balance_tree.insert("", "end", values=(name, f"{float(wh):.2f}"))

        self.status_var.set("Bilan energetique genere")

    def _on_close(self) -> None:
        self.connector.Disconnect()
        self.root.destroy()


def main() -> None:
    load_dotenv_file()
    normalize_sql_host_for_local_run()

    root = tk.Tk()
    SolarApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
