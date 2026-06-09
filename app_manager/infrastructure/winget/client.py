import re
import subprocess
from dataclasses import dataclass


@dataclass
class WingetApp:
    name: str
    version: str
    id: str
    available: str = ""


@dataclass
class WingetUpgrade:
    name: str
    id: str
    version: str
    available: str


class WingetManager:

    def __init__(self):
        self.apps: list[WingetApp] = []

    def _run(self, args: list[str]) -> subprocess.CompletedProcess:

        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            shell=True,
        )

    def get_apps(self) -> list[WingetApp]:

        try:
            result = self._run(["winget", "list"])
            lines = result.stdout.splitlines()
            data_lines = lines[2:] if len(lines) > 2 else lines

            self.apps.clear()

            for line in data_lines:
                parsed = self._parse_line(line)
                if parsed:
                    self.apps.append(parsed)

            return self.apps

        except Exception as error:
            print("Erreur winget list:", error)
            return []

    def get_upgrades(self) -> list[WingetUpgrade]:

        upgrades: list[WingetUpgrade] = []

        try:
            result = self._run(["winget", "upgrade"])
            lines = result.stdout.splitlines()

            for line in lines:
                parsed = self._parse_upgrade_line(line)
                if parsed:
                    upgrades.append(parsed)

        except Exception as error:
            print("Erreur winget upgrade:", error)

        return upgrades

    def _parse_line(self, line: str) -> WingetApp | None:

        if not line.strip() or line.startswith("-"):
            return None

        try:
            name = line[:40].strip()
            app_id = line[40:70].strip()
            version = line[70:].strip()

            if not name or not app_id:
                return None

            return WingetApp(name=name, version=version, id=app_id)

        except Exception:
            return None

    def _parse_upgrade_line(self, line: str) -> WingetUpgrade | None:

        if not line.strip() or line.startswith("-"):
            return None

        lower = line.lower()
        if "name" in lower and "id" in lower:
            return None

        try:
            name = line[:35].strip()
            app_id = line[35:65].strip()
            rest = line[65:].strip()

            if not app_id or not rest:
                return None

            parts = re.split(r"\s{2,}|\t", rest)
            version = parts[0].strip() if parts else rest
            available = parts[1].strip() if len(parts) > 1 else ""

            if not available and " " in version:
                split = version.rsplit(" ", 1)
                if len(split) == 2:
                    version, available = split

            if not available or available == version:
                return None

            return WingetUpgrade(
                name=name or app_id,
                id=app_id,
                version=version,
                available=available,
            )

        except Exception:
            return None

    def search(self, query: str) -> list[WingetApp]:

        query = query.lower()
        return [
            app for app in self.apps
            if query in app.name.lower()
        ]

    def install(self, app_id: str) -> tuple[bool, str]:

        result = self._run([
            "winget", "install", "--id", app_id, "-e",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ])
        ok = result.returncode == 0
        msg = result.stdout.strip() or result.stderr.strip() or (
            "Installation terminée" if ok else "Échec installation"
        )
        return ok, msg

    def uninstall(self, app_id: str) -> tuple[bool, str]:

        result = self._run([
            "winget", "uninstall", "--id", app_id, "-e",
            "--accept-source-agreements",
        ])
        ok = result.returncode == 0
        msg = result.stdout.strip() or result.stderr.strip() or (
            "Désinstallation terminée" if ok else "Échec désinstallation"
        )
        return ok, msg

    def upgrade(self, app_id: str) -> tuple[bool, str]:

        result = self._run([
            "winget", "upgrade", "--id", app_id, "-e",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ])
        ok = result.returncode == 0
        msg = result.stdout.strip() or result.stderr.strip() or (
            "Mise à jour terminée" if ok else "Échec mise à jour"
        )
        return ok, msg

    def upgrade_all(self) -> tuple[bool, str]:

        result = self._run([
            "winget", "upgrade", "--all",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ])
        ok = result.returncode == 0
        msg = result.stdout.strip() or result.stderr.strip() or (
            "Mises à jour terminées" if ok else "Échec mises à jour"
        )
        return ok, msg
