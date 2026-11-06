import os
from pathlib import Path


# one folder for everything the game saves, so the exe never writes next to itself
def data_folder():
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
    return Path(base) / "DecaDome"