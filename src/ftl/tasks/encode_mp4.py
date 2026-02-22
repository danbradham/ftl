import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ftl.files import FileSequence, PathType
from ftl.tasks.base import Task
from ftl.tasks.types import Fps, Size
from ftl.tools import get_ffmpeg

CodecH264 = Literal["h264"]


@dataclass
class EncodeMp4(Task):
    folder: Path | str = field(
        default=".",
        metadata={
            "help": "The folder to output the MP4 to relative to the source files."
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
    vcodec: CodecH264 = field(
        default="h264",
        kw_only=True,
        metadata={
            "hidden": True,
            "help": "The video codec of the output MP4.",
        },
    )
    fps: Fps = field(
        default=-1,
        kw_only=True,
        metadata={
            "help": "The framerate of the output MP4.",
        },
    )
    max_size: Size = field(
        default=-1,
        kw_only=True,
        metadata={
            "help": "The maximum width or height of the output MP4.",
        },
    )

    def __post_init__(self):
        super().__post_init__()
        self.output = (
            self.input.path.parent / self.folder / (self.input.stem + ".mp4")
        ).resolve()

    def command(self) -> list[str]:
        # fmt: off
        cmd = [
            get_ffmpeg(),
            "-r", str(self.fps),
            "-i", str(self.input.path),
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-x264-params", "bframes=14:ref=12",
            "-g", "1",
            "-profile:v", "main",
            "-tune", "film",
            "-preset", "veryslow",
            "-crf", "17",
            "-vendor", "apl0",
            "-color_range", "tv",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "iec61966-2-1",
            "-y",
            str(self.output),
        ]
        # fmt: on

        # Filter Graph
        # Colorspace
        filters = []
        if self.input.suffix == ".exr":
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

        # Apply Filter Graph
        if filters:
            cmd[7:7] = [
                "-vf",
                ",".join(filters),
            ]

        # Ensure correct start_number for File Sequences
        if isinstance(self.input, FileSequence):
            cmd[1:1] = ["-start_number", str(self.input.frame_start)]

        return cmd

    def run(self) -> PathType:

        # Ensure destination directory exists...
        self.output.parent.mkdir(parents=True, exist_ok=True)

        cmd = self.command()

        self.log(f"  MP4: {self.input.name} -> {self.output.name}")
        self.log(f"  CMD: {' '.join(cmd)}\n")

        try:
            subprocess.run(
                self.command(),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed with error code {e.returncode}") from e

        return self.output
