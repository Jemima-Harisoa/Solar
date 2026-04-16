import tkinter as tk

from app.config import load_dotenv_file, normalize_sql_host_for_local_run
from app.ui.solar_app import SolarApp
from connection import ServerConnect


def main() -> None:
    # Environment bootstrap first, then DB connector and UI wiring.
    load_dotenv_file()
    normalize_sql_host_for_local_run()

    connector = ServerConnect()
    root = tk.Tk()
    SolarApp(root, connector)
    root.mainloop()


if __name__ == "__main__":
    main()
