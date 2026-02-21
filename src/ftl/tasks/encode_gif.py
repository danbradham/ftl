import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ftl.files import FileSequence, PathType, as_file
from ftl.tasks.base import Task
from ftl.tools import get_ffmpeg

MaxColors = Literal[4, 8, 16, 32, 64, 128, 256]
Fps = Literal[8, 12, 15, 24, 25, 30]
Size = Literal[256, 512, 768, 1024, 2048]


@dataclass
class EncodeGif(Task):
    src: Path = field(
        metadata={
            "hidden": True,
            "help": "The source Path to encode, could be a FileSequence or File.",
        }
    )
    dst: Path = field(
        init=False,
        metadata={
            "hidden": True,
            "help": "The Path to the output GIF.",
        },
    )
    folder: Path | str = field(
        default=".",
        metadata={
            "help": "The folder to output the GIF to relative to the source files."
        },
    )
    input_colorspace: str = field(
        default="srgb",
        kw_only=True,
        metadata={
            "hidden": True,
            "help": "The colorspace of the source media.",
        },
    )
    fps: Fps = field(
        default=24,
        kw_only=True,
        metadata={
            "help": "The frame rate of the output GIF.",
        },
    )
    max_size: Size = field(
        default=768,
        kw_only=True,
        metadata={
            "help": "The maximum width or height of the output GIF.",
        },
    )
    max_colors: MaxColors = field(
        default=256,
        kw_only=True,
        metadata={
            "help": "The maximum number of colors of the output GIF.",
        },
    )

    def command(self) -> list[str]:
        # fmt: off
        cmd = [get_ffmpeg(),
            "-i", str(self.src),
            "-y",
            str(self.dst),
        ]
        # fmt: on

        # Filter Graph
        # FPS
        filters = [f"fps=fps={self.fps}"]

        # Colorspace
        if self.src.suffix == ".exr":
            filters.append(
                "colorspace=space=bt709:primaries=bt709:trc=srgb:ispace=bt709:iprimaries=bt709:itrc=linear"
            )
        else:
            filters.append("scale=in_color_matrix=bt709:out_color_matrix=bt709")

        # Scale
        if self.max_size > 0:
            filters.append(
                f"scale='{self.max_size}:{self.max_size}:force_original_aspect_ratio=decrease:force_divisible_by=2'"
            )

        # GIF Palette Gen + Use
        palettegen = f"palettegen=max_colors={self.max_colors}:reserve_transparent=on:transparency_color=ffffff"
        palette = f"[s];[s]split[a][b];[a]{palettegen}[p];[b][p]paletteuse"

        # Apply Filter Graph
        if filters:
            cmd[3:3] = [
                "-filter_complex",
                ",".join(filters) + palette,
            ]

        # Ensure correct start_number for File Sequences
        f = as_file(self.src)
        if isinstance(f, FileSequence):
            cmd[1:1] = ["-start_number", str(f.frame_start)]

        return cmd

    def run(self) -> PathType:
        # Ensure destination directory exists...
        self.dst.parent.mkdir(parents=True, exist_ok=True)

        cmd = self.command()
        self.log(f"  GIF: {self.src.name} -> {self.dst.name}")
        self.log(f"  CMD: {' '.join(cmd)}\n")

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed with error code {e.returncode}") from e

        return self.dst
