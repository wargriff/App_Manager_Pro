"""Mises à jour des applications via Winget."""

from __future__ import annotations

import threading
from tkinter import messagebox
from typing import TYPE_CHECKING

from app_manager.models.app_item import AppItem
from app_manager.services.winget import WingetManager

if TYPE_CHECKING:
    from app_manager.ui.app_ui import AppUI


class UpdateManager:

    def __init__(self, ui: "AppUI"):
        self.ui = ui

    def check_updates(self):

        if self.ui._checking_updates:
            return

        self.ui._checking_updates = True
        self.ui.status.configure(text="⬆ Vérification des mises à jour...")

        def worker():

            try:
                upgrades = WingetManager().get_upgrades()
                upgrade_map = {u.id.lower(): u for u in upgrades}
                name_map = {u.name.lower(): u for u in upgrades}

                def apply():
                    for item in self.ui.all_data:
                        item.update_available = False
                        item.latest_version = ""

                        up = upgrade_map.get(item.winget_id.lower())
                        if not up:
                            up = name_map.get(item.name.lower())

                        if up:
                            item.update_available = True
                            item.latest_version = up.available
                            if not item.winget_id:
                                item.winget_id = up.id

                    self.ui.update_badge()
                    self.ui.sync_list()
                    count = sum(
                        1 for i in self.ui.all_data if i.update_available
                    )
                    self.ui.status.configure(
                        text=f"✅ {len(self.ui.all_data)} apps • {count} MAJ",
                    )

                self.ui.run_on_ui(apply)

            except Exception as error:
                self.ui.run_on_ui(
                    lambda: self.ui.status.configure(text=f"MAJ: {error}"),
                )

            finally:
                self.ui._checking_updates = False

        threading.Thread(target=worker, daemon=True).start()

    def upgrade_item(self, item: AppItem):

        if not item.winget_id:
            messagebox.showwarning(
                "Mise à jour",
                "Cette application n'est pas gérée par Winget.",
            )
            return

        if not messagebox.askyesno(
            "Mise à jour",
            f"Mettre à jour {item.name} ?",
        ):
            return

        self.ui.status.configure(text=f"⬆ Mise à jour de {item.name}...")

        def worker():

            ok, msg = WingetManager().upgrade(item.winget_id)

            def done():
                self.ui.status.configure(text=msg)
                if ok:
                    item.update_available = False
                    item.latest_version = ""
                    self.ui.update_badge()
                    self.ui.sync_list()
                    messagebox.showinfo("Mise à jour", msg)
                else:
                    messagebox.showerror("Erreur", msg)

            self.ui.run_on_ui(done)

        threading.Thread(target=worker, daemon=True).start()

    def upgrade_all(self):

        count = sum(1 for i in self.ui.all_data if i.update_available)

        if count == 0:
            messagebox.showinfo(
                "Mises à jour",
                "Aucune mise à jour disponible.\n"
                "Cliquez sur Scanner puis attendez la vérification.",
            )
            return

        if not messagebox.askyesno(
            "Mises à jour",
            f"Mettre à jour {count} application(s) via Winget ?",
        ):
            return

        self.ui.status.configure(text="⬆ Mises à jour en cours...")

        def worker():

            ok, msg = WingetManager().upgrade_all()

            def done():
                self.ui.status.configure(text=msg)
                if ok:
                    self.check_updates()
                messagebox.showinfo(
                    "Mises à jour" if ok else "Erreur",
                    msg,
                )

            self.ui.run_on_ui(done)

        threading.Thread(target=worker, daemon=True).start()
