import os
import subprocess
import sysconfig

import OpenImageIO as oiio

from ftl.settings import get_settings


class Tools:
    ffmpeg_executable: str | None = None
    oiiotool_executable: str | None = None


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

    raise FileNotFoundError("ffmpeg not found in System PATH")


def get_ffmpeg_version():
    """Get the version of FFMPEG."""

    try:
        output = subprocess.check_output([get_ffmpeg(), "-version"], text=True)
        version = output.splitlines()[0].split()[2]
        return version
    except Exception as e:
        print(f"Error getting ffmpeg version: {e}")
        return None


def set_oiiotool(file: str):
    if not os.path.exists(file):
        raise FileNotFoundError(f"File does not exist: {file}")

    Tools.oiiotool_executable = file


def get_oiiotool():
    """Get path to oiiotool executable."""
    if Tools.oiiotool_executable is not None:
        return Tools.oiiotool_executable

    paths = [
        sysconfig.get_path("scripts"),
    ]
    paths += os.environ["PATH"].split(os.pathsep)

    for path in paths:
        candidate = os.path.join(path, "oiiotool.exe")
        if os.path.exists(candidate):
            set_oiiotool(candidate)
            return candidate

        candidate = os.path.join(path, "oiiotool")
        if os.path.exists(candidate):
            set_oiiotool(candidate)
            return candidate

    raise FileNotFoundError("oiiotool not found in Python bin or System PATH.")


def get_oiio_version():
    """Get the version of OpenImageIO."""

    return oiio.__version__


def get_ocio_config() -> oiio.ColorConfig:
    return oiio.ColorConfig()


def get_ocio_config_name() -> str:
    """Get the name of the OCIO config."""

    return get_ocio_config().configname()


def get_ocio_input_transforms() -> list[str]:
    """Get OCIO config colorspaces."""

    colorspaces = get_ocio_config().getColorSpaceNames()
    return sorted(list(set(colorspaces) - set(get_ocio_display_devices())))


def get_ocio_default_input_transform() -> str:
    """Get OCIO default input transform."""

    return get_ocio_config().getColorSpaceNameByRole("scene_linear")


def get_ocio_display_devices() -> list[str]:
    """Get OCIO config display colorspaces."""

    return get_ocio_config().getDisplayNames()


def get_ocio_default_display_name() -> str:
    """Get OCIO config."""

    return get_ocio_config().getDefaultDisplayName()


def get_ocio_view_transforms(display_name: str) -> list[str]:
    """Get OCIO config display colorspaces."""

    return get_ocio_config().getViewNames(display_name)


def get_ocio_default_view_name() -> str:
    """Get OCIO config."""

    return get_ocio_config().getDefaultViewName()
