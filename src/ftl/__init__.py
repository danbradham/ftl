import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    path = Path(sys._MEIPASS)
else:
    path = Path(__file__).parent
