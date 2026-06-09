# icon_manager.py

from __future__ import annotations

import ctypes
import json
import os
import re
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageTk

ICON_SIZE = 32


class IconManager:

    def __init__(self):

        self.cache = {}

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "AppManagerPro/1.0"
        })

    # =====================================================
    # MAIN
    # =====================================================

    def get_icon(self, item):

        key = item.path or item.name

        if key in self.cache:
            return self.cache[key]

        icon = (
            self.get_steam_icon(item)
            or self.get_epic_icon(item)
            or self.get_ubisoft_icon(item)
            or self.get_riot_icon(item)
            or self.get_battlenet_icon(item)
            or self.get_exe_icon(item.path)
            or self.get_web_icon(item.name)
            or self.generate_icon(item.name)
        )

        self.cache[key] = icon

        return icon

    # =====================================================
    # HELPERS
    # =====================================================

    @staticmethod
    def normalize_image(img):

        img = img.convert("RGBA")

        return img.resize(
            (ICON_SIZE, ICON_SIZE),
            Image.LANCZOS,
        )

    @staticmethod
    def to_photo(img):

        return ImageTk.PhotoImage(img)

    # =====================================================
    # STEAM
    # =====================================================

    def get_steam_icon(self, item):

        try:

            if not item.path:
                return None

            manifest = self.find_manifest(item.path)

            if not manifest:
                return None

            appid = self.extract_appid(manifest)

            if not appid:
                return None

            steam = self.get_steam_path()

            if not steam:
                return None

            cache_dir = os.path.join(
                steam,
                "appcache",
                "librarycache",
            )

            candidates = [
                f"{appid}_library_600x900.jpg",
                f"{appid}_header.jpg",
                f"{appid}_icon.jpg",
            ]

            for file in candidates:

                icon_path = os.path.join(
                    cache_dir,
                    file,
                )

                if os.path.exists(icon_path):
                    return self.load_image(icon_path)

        except Exception as e:
            print("Steam icon error:", e)

        return None

    def find_manifest(self, path):

        try:

            current = path

            for _ in range(8):

                current = os.path.dirname(current)

                steamapps = os.path.join(
                    current,
                    "steamapps",
                )

                if os.path.exists(steamapps):

                    for file in os.listdir(steamapps):

                        if file.startswith("appmanifest_"):

                            return os.path.join(
                                steamapps,
                                file,
                            )

        except Exception:
            pass

        return None

    @staticmethod
    def extract_appid(manifest):

        try:

            with open(
                manifest,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as f:

                content = f.read()

            match = re.search(
                r'"appid"\s+"(\d+)"',
                content,
            )

            if match:
                return match.group(1)

        except Exception:
            pass

        return None

    @staticmethod
    def get_steam_path():

        candidates = [
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
        ]

        for path in candidates:

            if os.path.exists(path):
                return path

        return None

    # =====================================================
    # EPIC
    # =====================================================

    def get_epic_icon(self, item):

        try:

            manifests = os.path.expandvars(
                r"%ProgramData%\Epic\EpicGamesLauncher\Data\Manifests"
            )

            if not os.path.exists(manifests):
                return None

            for file in os.listdir(manifests):

                if not file.endswith(".item"):
                    continue

                full = os.path.join(
                    manifests,
                    file,
                )

                with open(
                    full,
                    "r",
                    encoding="utf-8",
                ) as f:

                    data = json.load(f)

                display = data.get(
                    "DisplayName",
                    "",
                ).lower()

                if item.name.lower() not in display:
                    continue

                image_url = (
                    data.get("DisplayImage")
                    or data.get("Thumbnail")
                )

                if image_url:
                    return self.load_from_url(image_url)

        except Exception as e:
            print("Epic icon error:", e)

        return None

    # =====================================================
    # UBISOFT / RIOT / BATTLENET
    # =====================================================

    def search_png_in_folder(self, folder, item):

        try:

            if not os.path.exists(folder):
                return None

            item_name = item.name.lower()

            for root, _, files in os.walk(folder):

                for file in files:

                    if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                        continue

                    if item_name in file.lower():

                        return self.load_image(
                            os.path.join(root, file)
                        )

        except Exception:
            pass

        return None

    def get_ubisoft_icon(self, item):

        return self.search_png_in_folder(
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Ubisoft\Ubisoft Game Launcher\cache"
            ),
            item,
        )

    def get_riot_icon(self, item):

        return self.search_png_in_folder(
            os.path.expandvars(
                r"%ProgramData%\Riot Games"
            ),
            item,
        )

    def get_battlenet_icon(self, item):

        return self.search_png_in_folder(
            os.path.expandvars(
                r"%ProgramData%\Battle.net"
            ),
            item,
        )

    # =====================================================
    # WEB
    # =====================================================

    def get_web_icon(self, name):

        try:

            clean = (
                name.lower()
                .replace(" ", "")
                .replace("_", "")
            )

            domains = [
                f"{clean}.com",
                f"{clean}.gg",
                f"{clean}.net",
            ]

            for domain in domains:

                url = f"https://logo.clearbit.com/{domain}"

                response = self.session.get(
                    url,
                    timeout=2,
                )

                if response.status_code == 200:
                    return self.load_from_bytes(
                        response.content
                    )

        except Exception:
            pass

        return None

    # =====================================================
    # EXE
    # =====================================================

    def get_exe_icon(self, path):

        if not path:
            return None

        if not os.path.exists(path):
            return None

        if not path.lower().endswith(".exe"):
            return None

        return self.get_windows_icon(path)

    # =====================================================
    # WINDOWS
    # =====================================================

    def get_windows_icon(self, path):

        try:

            SHGFI_ICON = 0x100
            SHGFI_LARGEICON = 0x0

            class SHFILEINFO(ctypes.Structure):

                _fields_ = [
                    ("hIcon", ctypes.c_void_p),
                    ("iIcon", ctypes.c_int),
                    ("dwAttributes", ctypes.c_uint),
                    ("szDisplayName", ctypes.c_wchar * 260),
                    ("szTypeName", ctypes.c_wchar * 80),
                ]

            shinfo = SHFILEINFO()

            ctypes.windll.shell32.SHGetFileInfoW(
                path,
                0,
                ctypes.byref(shinfo),
                ctypes.sizeof(shinfo),
                SHGFI_ICON | SHGFI_LARGEICON,
            )

            hicon = shinfo.hIcon

            if not hicon:
                return None

            hdc = ctypes.windll.user32.GetDC(None)

            hdc_mem = ctypes.windll.gdi32.CreateCompatibleDC(hdc)

            bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(
                hdc,
                64,
                64,
            )

            ctypes.windll.gdi32.SelectObject(
                hdc_mem,
                bmp,
            )

            ctypes.windll.user32.DrawIconEx(
                hdc_mem,
                0,
                0,
                hicon,
                64,
                64,
                0,
                None,
                3,
            )

            buffer_len = 64 * 64 * 4

            buffer = ctypes.create_string_buffer(
                buffer_len
            )

            ctypes.windll.gdi32.GetBitmapBits(
                bmp,
                buffer_len,
                buffer,
            )

            img = Image.frombuffer(
                "RGBA",
                (64, 64),
                buffer,
                "raw",
                "BGRA",
                0,
                1,
            )

            ctypes.windll.user32.DestroyIcon(hicon)
            ctypes.windll.gdi32.DeleteObject(bmp)
            ctypes.windll.gdi32.DeleteDC(hdc_mem)
            ctypes.windll.user32.ReleaseDC(None, hdc)

            img = self.normalize_image(img)

            return self.to_photo(img)

        except Exception as e:
            print("Windows icon error:", e)

        return None

    # =====================================================
    # LOADERS
    # =====================================================

    def load_image(self, path):

        try:

            img = Image.open(path)

            img = img.convert("RGBA")

            img.thumbnail((32, 32))

            return ImageTk.PhotoImage(img)

        except Exception:
            return None

    def load_from_url(self, url):

        try:

            response = self.session.get(
                url,
                timeout=3,
            )

            if response.status_code != 200:
                return None

            return self.load_from_bytes(
                response.content
            )

        except Exception:
            return None

    def load_from_bytes(self, data):

        try:

            img = Image.open(BytesIO(data))

            img = img.convert("RGBA")

            img.thumbnail((32, 32))

            return ImageTk.PhotoImage(img)

        except Exception:
            return None

    # =====================================================
    # FALLBACK
    # =====================================================

    def generate_icon(self, name):

        img = Image.new(
            "RGBA",
            (ICON_SIZE, ICON_SIZE),
            (35, 35, 35),
        )

        draw = ImageDraw.Draw(img)

        letter = (
            name[0].upper()
            if name
            else "?"
        )

        draw.text(
            (10, 6),
            letter,
            fill="white",
        )

        return self.to_photo(img)