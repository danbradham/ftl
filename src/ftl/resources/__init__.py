import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    path = Path(sys._MEIPASS) / "resources"
else:
    path = Path(__file__).parent


def get(name):
    return path / name
