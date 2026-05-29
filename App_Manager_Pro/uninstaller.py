import os
import shlex
import shutil
import subprocess
import winreg


class Uninstaller:

    SAFE_DIRS = [
        os.environ.get("ProgramFiles", ""),
        os.environ.get("ProgramFiles(x86)", ""),
        os.environ.get("APPDATA", ""),
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("PROGRAMDATA", "")
    ]

    FORBIDDEN_PATHS = [
        "windows",
        "system32",
        "windowsapps",
        "microsoft"
    ]

    # =========================================================
    # 🔧 UTIL
    # =========================================================

    @staticmethod
    def run_command(cmd):
        try:
            if isinstance(cmd, str):
                cmd = shlex.split(cmd)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            return result.returncode, result.stdout, result.stderr

        except Exception as e:
            return -1, "", str(e)

    @staticmethod
    def kill_process_from_path(path):
        try:
            exe = os.path.basename(path)
            subprocess.run(["taskkill", "/f", "/im", exe], capture_output=True)
        except:
            pass

    @staticmethod
    def is_safe_path(path):
        if not path:
            return False

        path = path.lower()

        if len(path) < 10:
            return False

        return not any(x in path for x in Uninstaller.FORBIDDEN_PATHS)

    # =========================================================
    # 🧠 REGISTRE (FIABLE)
    # =========================================================

    @staticmethod
    def get_uninstall_entries(program_name):
        paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        results = []

        for root, path in paths:
            try:
                with winreg.OpenKey(root, path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub) as sk:

                                name = winreg.QueryValueEx(sk, "DisplayName")[0]

                                if program_name.lower() in name.lower():

                                    try:
                                        uninstall = winreg.QueryValueEx(sk, "UninstallString")[0]
                                    except:
                                        uninstall = ""

                                    try:
                                        quiet = winreg.QueryValueEx(sk, "QuietUninstallString")[0]
                                    except:
                                        quiet = ""

                                    results.append((name, quiet or uninstall))

                        except:
                            continue
            except:
                continue

        return results

    @staticmethod
    def make_silent(cmd):
        if not cmd:
            return ""

        cmd = cmd.strip()

        if "msiexec" in cmd.lower():
            if "/quiet" not in cmd.lower():
                cmd += " /quiet /norestart"
        else:
            if not any(x in cmd.lower() for x in ["/s", "/silent", "/quiet"]):
                cmd += " /S"

        return cmd

    # =========================================================
    # 🧼 CLEAN (SAFE)
    # =========================================================

    @staticmethod
    def clean_leftovers(program_name):
        deleted = []

        for base in Uninstaller.SAFE_DIRS:
            if not base or not os.path.exists(base):
                continue

            for root, dirs, _ in os.walk(base):
                for d in dirs:
                    if program_name.lower() in d.lower():
                        full = os.path.join(root, d)

                        if not Uninstaller.is_safe_path(full):
                            continue

                        try:
                            shutil.rmtree(full, ignore_errors=True)
                            deleted.append(full)
                        except:
                            pass

        return deleted

    # =========================================================
    # 💣 PORTABLE
    # =========================================================

    @staticmethod
    def delete_portable(path):
        try:
            if not path or not os.path.exists(path):
                return False, "❌ introuvable"

            if not Uninstaller.is_safe_path(path):
                return False, "❌ refus sécurité"

            folder = path if os.path.isdir(path) else os.path.dirname(path)

            if not folder or len(folder) < 5:
                return False, "❌ dossier dangereux"

            shutil.rmtree(folder, ignore_errors=True)

            return True, "🧨 supprimé (portable)"

        except Exception as e:
            return False, str(e)

    # =========================================================
    # 🚀 UNINSTALL PRINCIPAL (COMPATIBLE SCANNER)
    # =========================================================

    @staticmethod
    def uninstall(name, path=None):
        logs = []

        if path:
            Uninstaller.kill_process_from_path(path)

        # =========================
        # 🧠 REGISTRY UNINSTALL
        # =========================
        entries = Uninstaller.get_uninstall_entries(name)

        for prog_name, cmd in entries:

            if not cmd:
                continue

            # 🔥 FIX guillemets + msiexec
            cmd = cmd.replace('"', '').strip()

            if "msiexec" in cmd.lower():
                if "/x" not in cmd.lower():
                    cmd = cmd.replace("/i", "/x")
                cmd += " /quiet /norestart"

            else:
                if not any(x in cmd.lower() for x in ["/s", "/silent", "/quiet"]):
                    cmd += " /S"

            code, out, err = Uninstaller.run_command(cmd)

            logs.append(f"{prog_name} => {code}")

            if code == 0:
                Uninstaller.clean_leftovers(name)
                return True, f"✅ Désinstallé : {prog_name}"

        # =========================
        # 💣 FALLBACK PORTABLE
        # =========================
        if path:
            success, msg = Uninstaller.delete_portable(path)
            logs.append(msg)

            if success:
                return True, msg

        return False, "❌ Échec\n" + "\n".join(logs)