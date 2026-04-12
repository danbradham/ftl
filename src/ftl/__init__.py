import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    path = Path(sys._MEIPASS)
else:
    path = Path(__file__).parent


# TODO: FORCE OCIO CONFIG TEMPORARILY
import os

os.environ["OCIO"] = (
    path / "resources" / "cg-config-v2.1.0_aces-v1.3_ocio-v2.3.ocio"
).as_posix()
