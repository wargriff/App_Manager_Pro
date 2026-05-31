"""Contrôleur des mises à jour Winget."""

from __future__ import annotations

from tkinter import messagebox
from typing import TYPE_CHECKING

from app_manager.application.use_cases.manage_updates import ManageUpdatesUseCase
from app_manager.domain.models.app_item import AppItem

if TYPE_CHECKING:
    from app_manager.presentation.main_window import MainWindow


class UpdateController:

    def __init__(self, view: "MainWindow"):
        self.view = view
        self.use_case = ManageUpdatesUseCase(view.catalog)

    def check_updates(self):

        self.view.status_bar.set_text("⬆ Vérification des mises à jour...")

        self.use_case.check_updates(
            on_done=lambda: self.view.run_on_ui(self._on_checked),
        )

    def _on_checked(self):

        count = self.view.catalog.update_count
        total = len(self.view.catalog.all_items)
        self.view.sidebar.set_badge(
            f"⬆ {count} MAJ" if count else "✓ À jour",
        )
        self.view.sync_list()
        self.view.status_bar.set_text(f"✅ {total} apps • {count} MAJ")

    def upgrade_item(self, item: AppItem):

        if not item.winget_id:
            messagebox.showwarning(
                "Mise à jour",
                "Application non gérée par Winget.",
            )
            return

        if not messagebox.askyesno("Mise à jour", f"Mettre à jour {item.name} ?"):
            return

        self.view.status_bar.set_text(f"⬆ {item.name}...")

        def on_result(ok: bool, msg: str):
            def done():
                self.view.status_bar.set_text(msg)
                if ok:
                    item.update_available = False
                    item.latest_version = ""
                    self._on_checked()
                    messagebox.showinfo("Mise à jour", msg)
                else:
                    messagebox.showerror("Erreur", msg)

            self.view.run_on_ui(done)

        self.use_case.upgrade_one(item.winget_id, on_result)

    def upgrade_all(self):

        count = self.view.catalog.update_count

        if count == 0:
            messagebox.showinfo(
                "Mises à jour",
                "Aucune mise à jour disponible.",
            )
            return

        if not messagebox.askyesno(
            "Mises à jour",
            f"Mettre à jour {count} application(s) ?",
        ):
            return

        self.view.status_bar.set_text("⬆ Mises à jour en cours...")

        def on_result(ok: bool, msg: str):
            def done():
                self.view.status_bar.set_text(msg)
                if ok:
                    self.check_updates()
                messagebox.showinfo(
                    "Mises à jour" if ok else "Erreur",
                    msg,
                )

            self.view.run_on_ui(done)

        self.use_case.upgrade_all(on_result)
