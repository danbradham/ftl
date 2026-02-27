import os
import subprocess

from ftl.settings import get_settings


class Tools:
    ffmpeg_executable: str | None = None


def set_ffmpeg(file: str):
    if not os.path.exists(file):
        raise FileNotFoundError(f"File does not exist: {file}")

    Tools.ffmpeg_executable = file


def get_ffmpeg(ignore_settings=False):
    if Tools.ffmpeg_executable is not None:
        return Tools.ffmpeg_executable

    if not ignore_settings:
        if candidate := get_settings().get("ffmpeg"):
            try:
                set_ffmpeg(candidate)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Configured path for ffmpeg does not exist: '{candidate}'"
                )
            return candidate

    for path in os.environ["PATH"].split(os.pathsep):
        candidate = os.path.join(path, "ffmpeg.exe")
        if os.path.exists(candidate):
            set_ffmpeg(candidate)
            return candidate

        candidate = os.path.join(path, "ffmpeg")
        if os.path.exists(candidate):
            set_ffmpeg(candidate)
            return candidate

    raise FileNotFoundError("ffmpeg not found in PATH")


def get_ffmpeg_version():
    try:
        output = subprocess.check_output([get_ffmpeg(), "-version"], text=True)
        version = output.splitlines()[0].split()[2]
        return version
    except Exception as e:
        print(f"Error getting ffmpeg version: {e}")
        return None
