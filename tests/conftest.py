import os
import sys
from pathlib import Path

# Pygame must run without a real window or sound device in CI
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "client"))