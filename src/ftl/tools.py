import os
import subprocess
import sysconfig
from pathlib import Path

import OpenImageIO as oiio

from ftl.settings import get_settings


class Tools:
    ffmpeg_executable: str | None = None
    oiiotool_executable: str | None = None
    ocio_config: oiio.ColorConfig | None = None


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


def set_ocio_config(config_path: str) -> None:
    """Set the OCIO config path."""

    Tools.ocio_config = oiio.ColorConfig(config_path)


def get_ocio_config() -> oiio.ColorConfig:
    if Tools.ocio_config is None:
        Tools.ocio_config = oiio.ColorConfig()
    return Tools.ocio_config


def get_ocio_config_name() -> str:
    """Get the name of the OCIO config."""

    return get_ocio_config().configname()


def get_ocio_input_transforms() -> list[str]:
    """Get available input colorspaces from the OCIO config."""

    colorspaces = get_ocio_config().getColorSpaceNames()
    return sorted(list(set(colorspaces) - set(get_ocio_display_devices())))


def get_ocio_default_input_transform() -> str:
    """Get the default input transform (scene_linear) from the OCIO config."""

    return get_ocio_config().getColorSpaceNameByRole("scene_linear")


def get_ocio_display_devices() -> list[str]:
    """Get a list of display colorspaces defined in the OCIO config."""

    return get_ocio_config().getDisplayNames()


def get_ocio_default_display_device() -> str:
    """Get the default display device name from the OCIO config."""

    return get_ocio_config().getDefaultDisplayName()


def get_ocio_view_transforms(display_name: str) -> list[str]:
    """Get view transforms associated with a specific display device name."""

    return get_ocio_config().getViewNames(display_name)


def get_ocio_default_view_transform() -> str:
    """Get the default view transform name from the OCIO config."""

    return get_ocio_config().getDefaultViewName()


def ocio_display(
    input: Path,
    output: Path,
    input_transform: str,
    display_device: str,
    view_transform: str,
    unpremult: bool = True,
):
    """Applies the OCIO display transform to an image."""

    in_buf = oiio.ImageBuf(input.as_posix())
    out_buf = oiio.ImageBufAlgo.ociodisplay(
        in_buf,
        fromspace=input_transform,
        display=display_device,
        view=view_transform,
        unpremult=unpremult,
    )
    out_buf.write(output.as_posix())
