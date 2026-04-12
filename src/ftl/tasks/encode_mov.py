import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ftl.files import FileSequence, PathType
from ftl.tasks.core import Task
from ftl.tools import get_ffmpeg
from ftl.types import Fps, Size

CodecProres = Literal["Prores422", "Prores4444"]


@dataclass
class EncodeMov(Task):
    folder: Path | str = field(
        default=".",
        metadata={
            "help": "The folder to output the MOV to relative to the source files."
        },
    )
    vcodec: CodecProres = field(
        default="Prores4444",
        kw_only=True,
        metadata={
            "hidden": True,
            "help": "The video codec of the output MOV.",
        },
    )
    fps: Fps = field(
        default=-1,
        kw_only=True,
        metadata={
            "help": "The framerate of the output MOV.",
        },
    )
    max_size: Size = field(
        default=-1,
        kw_only=True,
        metadata={
            "help": "The maximum width or height of the output MOV.",
        },
    )
    background: str = field(
        default="",
        kw_only=True,
        metadata={
            "help": "The background color of the output MOV.\nOnly applies to transparent media.",
            "param_type": "color",
        },
    )

    def __post_init__(self):
        super().__post_init__()
        self.output = (
            self.input.path.parent / self.folder / (self.input.stem + ".mov")
        ).resolve()

    def command(self) -> list[str]:
        # fmt: off
        is_4444 = self.vcodec.lower() == "prores4444"
        cmd = [
            get_ffmpeg(),
            "-r", str(self.fps),
            "-i", str(self.input.path),
            "-c:v", "prores_ks",
            "-profile:v", ("422", "4444")[is_4444],
            "-qscale:v", "11",
            "-vendor", "apl0",
            "-pix_fmt", ("yuv422p10le", "yuva444p10le")[is_4444],
            *((), ("-alpha_bits", "16"))[is_4444],
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
                "colorspace=space=bt709:primaries=bt709:trc=srgb:range=tv:ispace=bt709:iprimaries=bt709:itrc=linear:irange=tv"
            )
        else:
            filters.append("scale=in_color_matrix=bt709:out_color_matrix=bt709")

        # Scale
        if self.max_size > 0:
            filters.append(
                f"scale='{self.max_size}:{self.max_size}:force_original_aspect_ratio=decrease:force_divisible_by=2'"
            )

        filter_graph = ",".join(filters)

        # Background Filter Graph
        background_graph = ""
        if self.background:
            background_graph = (
                "[s];[s]split=2[bg][fg];"
                f"[bg]drawbox=c={self.background}@1:replace=1:t=fill[bg];"
                "[bg][fg]overlay=format=auto"
            )

        # Apply Filter Graph
        if filter_graph or background_graph:
            cmd[7:7] = [
                "-filter_complex",
                filter_graph + background_graph,
            ]

        # Ensure correct start_number for File Sequences
        if isinstance(self.input, FileSequence):
            cmd[1:1] = ["-start_number", str(self.input.frame_start)]

        return cmd

    def run(self) -> PathType:
        # Ensure destination directory exists...
        self.output.parent.mkdir(parents=True, exist_ok=True)

        cmd = self.command()

        self.log.info(f"{self.input.name} -> {self.output.name}")
        self.log.info(f"command: {' '.join(cmd)}")

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

        return self.output
