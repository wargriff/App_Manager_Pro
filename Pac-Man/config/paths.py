import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ASSETS = os.path.join(BASE_DIR, "assets")

MAP_PATH = os.path.join(ASSETS, "map")
AUDIO_PATH = os.path.join(ASSETS, "audio")
SPRITES_PATH = os.path.join(ASSETS, "sprites")


def debug_paths():
    print("\n===== PATH DEBUG =====")
    print("BASE_DIR:", BASE_DIR)
    print("ASSETS:", ASSETS)
    print("MAP_PATH:", MAP_PATH)
    print("AUDIO_PATH:", AUDIO_PATH)
    print("SPRITES_PATH:", SPRITES_PATH)

    for path in [MAP_PATH, AUDIO_PATH, SPRITES_PATH]:
        if not os.path.exists(path):
            print(f"❌ MISSING: {path}")
        else:
            print(f"✅ OK: {path}")
            print("   files:", os.listdir(path))