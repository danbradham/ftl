import json
from pathlib import Path
from typing import TypedDict

from platformdirs import user_data_dir

LIB_DIR = Path(__file__).parent
USER_DATA_DIR = Path(user_data_dir("ffmpeg-tools"))
USER_SETTINGS = USER_DATA_DIR / "settings.json"


class Settings(TypedDict):
    mov_enabled: bool
    mov_size: int
    mov_fps: int
    mov_folder: str
    mp4_enabled: bool
    mp4_size: int
    mp4_fps: int
    mp4_folder: str
    gif_enabled: bool
    gif_size: int
    gif_colors: int
    gif_fps: int
    gif_folder: str


def default_settings() -> Settings:
    return {
        "mov_enabled": True,
        "mov_size": -1,
        "mov_fps": 24,
        "mov_folder": ".",
        "mp4_enabled": True,
        "mp4_size": -1,
        "mp4_fps": 24,
        "mp4_folder": ".",
        "gif_enabled": True,
        "gif_size": 768,
        "gif_colors": 128,
        "gif_fps": 24,
        "gif_folder": ".",
    }


def save_settings(data: Settings):
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    USER_SETTINGS.write_text(json.dumps(data))


def get_settings() -> Settings:
    settings = default_settings()
    if USER_SETTINGS.exists():
        settings.update(json.loads(USER_SETTINGS.read_text()))
    return settings


def int_to_sizeStr(value):
    if value <= 0:
        return "original"
    return str(value)


def sizeStr_to_int(value):
    if isinstance(value, str) and value.lower() in ("original", "unchanged"):
        return -1
    return int(value)
