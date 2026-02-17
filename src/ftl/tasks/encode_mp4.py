import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ftl.files import FileSequence, PathType, as_file
from ftl.tasks.base import Task
from ftl.tasks.types import Fps, Size
from ftl.tools import get_ffmpeg

CodecH264 = Literal["h264", "h265", "vp9"]


@dataclass
class EncodeMp4(Task):
    src: Path = field(metadata={"hidden": True})
    dst: Path = field(metadata={"hidden": True})
    input_colorspace: str = field(default="srgb", kw_only=True)
    vcodec: CodecH264 = field(default="h264", kw_only=True)
    fps: Fps = field(default=-1, kw_only=True)
    max_size: Size = field(default=-1, kw_only=True)

    def command(self) -> list[str]:
        # fmt: off
        cmd = [
            get_ffmpeg(),
            "-r", str(self.fps),
            "-i", str(self.src),
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
            str(self.dst),
        ]
        # fmt: on

        # Filter Graph
        # Colorspace
        filters = []
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

        # Apply Filter Graph
        if filters:
            cmd[7:7] = [
                "-vf",
                ",".join(filters),
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

        self.log(f"  MP4: {self.src.name} -> {self.dst.name}")
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

        return self.dst
