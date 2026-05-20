# uninstall_unreal_engine.py
# FULL Unreal Engine Cleaner
# Garde Epic Games Launcher
# Lancer EN ADMINISTRATEUR

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import time
import winreg
from pathlib import Path

# =========================================================
# CONFIG
# =========================================================

DELETE_PROJECTS = False
FORCE_DELETE = True
SCAN_EXTRA_DRIVES = True


# =========================================================
# ADMIN
# =========================================================

def is_admin() -> bool:

    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():

    if is_admin():
        return True

    print("[INFO] Demande des droits administrateur...")

    try:

        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{os.path.abspath(__file__)}"',
            None,
            1
        )

    except Exception as e:
        print(f"[ERROR ADMIN] {e}")

    return False


# =========================================================
# LOG
# =========================================================

def log(msg: str):
    print(msg)


# =========================================================
# SAFE DELETE
# =========================================================

def remove_readonly(func, path, _):

    try:
        os.chmod(path, 0o777)
        func(path)
    except Exception:
        pass


def safe_delete(path: str | Path):

    path = Path(path)

    try:

        if not path.exists():
            return

        log(f"[DELETE] {path}")

        if path.is_file():

            path.unlink(missing_ok=True)

        else:

            shutil.rmtree(
                path,
                ignore_errors=False,
                onerror=remove_readonly
            )

    except Exception as e:

        log(f"[ERROR DELETE] {path} -> {e}")


# =========================================================
# COMMAND
# =========================================================

def run_command(cmd: str):

    try:

        log(f"[CMD] {cmd}")

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        log(f"[RETURN CODE] {result.returncode}")

        if result.stdout.strip():
            log(f"[STDOUT]\n{result.stdout}")

        if result.stderr.strip():
            log(f"[STDERR]\n{result.stderr}")

    except subprocess.TimeoutExpired:

        log("[TIMEOUT] Commande trop longue.")

    except Exception as e:

        log(f"[ERROR CMD] {e}")


# =========================================================
# KILL UE PROCESSES
# =========================================================

def kill_processes():

    processes = [

        "UnrealEditor.exe",
        "UnrealEngineLauncher.exe",
        "CrashReportClient.exe",
        "UnrealCEFSubProcess.exe"
    ]

    log("\n[KILLING UNREAL PROCESSES]")

    for proc in processes:

        try:

            subprocess.run(
                f'taskkill /F /T /IM "{proc}"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            log(f"[KILLED] {proc}")

        except Exception as e:

            log(f"[ERROR KILL] {proc} -> {e}")

    time.sleep(2)


# =========================================================
# REGISTRY
# =========================================================

def get_installed_programs():

    uninstall_keys = [

        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]

    programs = []

    for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:

        for key_path in uninstall_keys:

            try:

                key = winreg.OpenKey(root, key_path)

                for i in range(winreg.QueryInfoKey(key)[0]):

                    try:

                        subkey_name = winreg.EnumKey(key, i)

                        subkey = winreg.OpenKey(key, subkey_name)

                        try:
                            name = winreg.QueryValueEx(
                                subkey,
                                "DisplayName"
                            )[0]

                        except OSError:
                            continue

                        uninstall = None

                        try:

                            uninstall = winreg.QueryValueEx(
                                subkey,
                                "UninstallString"
                            )[0]

                        except OSError:
                            pass

                        if uninstall:

                            programs.append({
                                "name": name,
                                "uninstall": uninstall
                            })

                    except Exception:
                        pass

            except Exception:
                pass

    return programs


# =========================================================
# UNINSTALL
# =========================================================

def normalize_uninstall_cmd(cmd: str) -> str:

    cmd = cmd.strip()

    if "msiexec" in cmd.lower():

        cmd = cmd.replace("/I", "/X")
        cmd = cmd.replace("/i", "/X")

        if "/quiet" not in cmd.lower():
            cmd += " /quiet /norestart"

    return cmd


def uninstall_programs():

    targets = [

        "Unreal Engine",
        "UE_"
    ]

    programs = get_installed_programs()

    log("\n[SEARCHING UNREAL INSTALLATIONS]")

    for program in programs:

        name = program["name"]

        if any(t.lower() in name.lower() for t in targets):

            log(f"\n[FOUND] {name}")

            uninstall_cmd = normalize_uninstall_cmd(
                program["uninstall"]
            )

            run_command(uninstall_cmd)


# =========================================================
# DELETE FILES
# =========================================================

def delete_unreal_files():

    user = Path.home()

    paths = [

        # Unreal cache
        user / "AppData/Local/UnrealEngine",
        user / "AppData/Roaming/Unreal Engine",

        # Unreal projects
        user / "Documents/Unreal Projects",

        # Unreal Engine folders only
        Path("C:/Program Files/Epic Games"),

        # Temp
        Path(os.environ.get("TEMP", "")),
    ]

    log("\n[CLEANING UNREAL FILES]")

    for path in paths:

        if not DELETE_PROJECTS and "Unreal Projects" in str(path):
            continue

        # Ne pas supprimer le launcher Epic
        if str(path) == "C:\\Program Files\\Epic Games":

            if path.exists():

                for item in path.iterdir():

                    try:

                        if item.name.startswith("UE_"):

                            safe_delete(item)

                    except Exception:
                        pass

            continue

        safe_delete(path)


# =========================================================
# CLEAN REMAINING
# =========================================================

def cleanup_remaining():

    roots = ["C:/"]

    if SCAN_EXTRA_DRIVES:
        roots.extend(["D:/", "E:/", "F:/"])

    keywords = [

        "UE_",
        "Unreal"
    ]

    log("\n[SCANNING REMAINING UNREAL FOLDERS]")

    for root in roots:

        root_path = Path(root)

        if not root_path.exists():
            continue

        try:

            for item in root_path.iterdir():

                try:

                    name = item.name.lower()

                    if any(k.lower() in name for k in keywords):

                        log(f"[FOUND] {item}")

                        if FORCE_DELETE:
                            safe_delete(item)

                except Exception:
                    pass

        except Exception:
            pass


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("UNREAL ENGINE FULL CLEANER")
    print("=" * 60)

    if not relaunch_as_admin():
        return

    kill_processes()

    uninstall_programs()

    kill_processes()

    delete_unreal_files()

    cleanup_remaining()

    print("\n[DONE]")
    print("Unreal Engine supprimé.")
    print("Epic Games Launcher conservé.")

    try:
        input("\nAppuie sur Entrée pour quitter...")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()