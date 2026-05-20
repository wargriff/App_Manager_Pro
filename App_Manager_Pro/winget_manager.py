import subprocess
from dataclasses import dataclass


# =========================
# 📦 DATA STRUCTURE
# =========================
@dataclass
class WingetApp:
    name: str
    version: str
    id: str


# =========================
# ⚙️ MANAGER
# =========================
class WingetManager:

    def __init__(self):
        self.apps = []

    # 🔍 RÉCUPÉRER APPS
    def get_apps(self):

        try:
            result = subprocess.run(
                ["winget", "list"],
                capture_output=True,
                text=True,
                shell=True
            )

            lines = result.stdout.splitlines()

            # skip header + ligne séparateur
            data_lines = lines[2:]

            self.apps.clear()

            for line in data_lines:

                parsed = self._parse_line(line)

                if parsed:
                    self.apps.append(parsed)

            return self.apps

        except Exception as e:
            print("Erreur winget:", e)
            return []

    # 🧠 PARSING INTELLIGENT
    def _parse_line(self, line):

        if not line.strip():
            return None

        try:
            # découpe plus propre (colonnes fixes)
            name = line[:40].strip()
            app_id = line[40:70].strip()
            version = line[70:].strip()

            return WingetApp(name=name, version=version, id=app_id)

        except:
            return None

    # 🔎 RECHERCHE
    def search(self, query):

        query = query.lower()

        return [
            app for app in self.apps
            if query in app.name.lower()
        ]

    # 📦 INSTALL
    def install(self, app_id):

        subprocess.run(["winget", "install", "--id", app_id, "-e"])

    # 🗑️ UNINSTALL
    def uninstall(self, app_id):

        subprocess.run(["winget", "uninstall", "--id", app_id, "-e"])