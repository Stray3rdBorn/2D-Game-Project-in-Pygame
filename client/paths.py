import os
import sys
from pathlib import Path


# one folder for everything the game saves, so the exe never writes next to itself
def data_folder():
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
    return Path(base) / "DecaDome"

# folder with the music and sound effects
def asset_folder():
    # inside the exe the files are unpacked to a temporary folder, PyInstaller names it _MEIPASS
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets"
    return Path(__file__).parent / "assets"