from __future__ import annotations

import enum
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .settings import Settings, default_settings

PathType = os.PathLike | Path


def get_ffmpeg():
    for path in os.environ["PATH"].split(os.pathsep):
        candidate = os.path.join(path, "ffmpeg.exe")
        if os.path.exists(candidate):
            return candidate
        candidate = os.path.join(path, "ffmpeg")
        if os.path.exists(candidate):
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


@dataclass
class FileSequence:
    path: PathType
    name: str
    stem: str
    suffix: str
    padding: int
    frame_start: int
    frame_end: int
    files: list[Path] = field(repr=False, default_factory=list)
    missing_frames: list[int] = field(default_factory=list)

    def format(self, relative_to: PathType | None = None) -> str:
        if relative_to:
            path = self.path.relative_to(Path(relative_to))
        else:
            path = self.path
        result = f"{path.as_posix()} [{self.frame_start}-{self.frame_end}]"
        if self.missing_frames:
            result += f"\n  missing {self.missing_frames}"
        return result

    @classmethod
    def from_file(cls, file: PathType):
        file = Path(file)
        # Check if we're dealing with a file sequence pattern...
        match = None
        if matches := re.findall(r"#+", file.as_posix()):
            match = matches[-1]
        elif matches := re.findall(r"%\d+d", file.as_posix()):
            match = matches[-1]
        elif matches := re.findall(r"\.(\d+)\.", file.as_posix()):
            match = matches[-1]

        if match:
            padding = len(match)
            suffix = file.suffix
            files = sorted(file.parent.glob(file.name.replace(match, "*")))
            frames = []
            frame_re = re.compile(file.as_posix().replace(match, r"(\d+)"))
            for f in files:
                if fmatch := frame_re.search(f.as_posix()):
                    frame = int(fmatch.group(1))
                    frames.append(frame)

            name = file.name.replace(match, f"%{padding:0>2d}d")
            stem = file.name.split(match)[0].strip(".")
            path = file.with_name(name)
            missing_frames = []
            prev_frame = frames[0]
            for frame in frames[1:]:
                if frame - prev_frame > 1:
                    missing_frames.extend(range(prev_frame + 1, frame))
                prev_frame = frame

            return cls(
                path,
                name,
                stem,
                suffix,
                padding,
                frames[0],
                frames[-1],
                files,
                missing_frames,
            )

        return


def get_sequences(folder: PathType) -> list[FileSequence]:
    results = []
    seen = []

    for file in Path(folder).iterdir():
        if file in seen:
            continue
        if not file.is_file():
            continue

        seen.append(file)
        fs = FileSequence.from_file(file)
        if fs:
            results.append(fs)
            seen.extend(fs.files)

    return results


class TaskStatus(enum.Enum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class TaskLog:
    task: Task
    total: int = field(default=100)
    value: int = field(default=0)
    t: float = field(default=0.0)
    records: list[dict[str, Any]] = field(default_factory=list, repr=False)
    logger: logging.Logger = field(init=False, repr=False)
    handlers: set[Callable[[dict]]] = field(default_factory=set, repr=False)

    def __post_init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.task.name}>")

    def __call__(self, message: str, **extra: Any):
        self.emit_record(type="log", message=message, **extra)
        self.logger.info(message)

    def start(self, **extra: Any):
        self.emit_record(type="progress", event="start", message=None, **extra)

    def step(self, amount: int, message: str | None = None, **extra: Any):
        self.value = min(self.value + amount, self.total)
        self.t = float(self.value) / float(self.total)
        if message:
            self.logger.info(f"{self.t:.0%} | {message}")

        event = ("step", "finished")[self.t == 1.0]
        self.emit_record(type="progress", event=event, message=message, **extra)

    def emit_record(self, **fields: Any):
        record = dict(
            task=self.task,
            name=self.task.name,
            status=self.task.status,
            total=self.total,
            value=self.value,
            t=self.t,
        )
        record.update(fields)
        self.records.append(record)
        for handler in self.handlers:
            handler(record)

    def add_handler(self, fn: Callable[[dict], Any]):
        self.handlers.add(fn)

    def remove_handler(self, fn: Callable[[dict], Any]):
        self.handlers.remove(fn)


class Task:
    """Base for all Task types.

    Task subclasses must:
        - Implement the run method.

    Task subclasses may:
        - Implement __init__ to add arguments to a Task. Be
          sure to call super().__init__()
        - Set `self.log.total` to a maximum value for your Task's progress.
        - Report progress using `self.log.step(amount: int, message: str)`
        - Log INFO using `self.log(message: str, **extras)`
    """

    def __init__(self) -> None:
        self.result = None
        self.error = None
        self.status = TaskStatus.WAITING
        self.name = self.__class__.__name__
        self.log = TaskLog(self)

    def __call__(self):
        """Start and run the Task."""
        try:
            self.start()
            self.result = self.run()
            self.status = TaskStatus.SUCCESS
            self.log.step(self.log.total, "Task Completed.")
        except Exception as e:
            self.error = e
            self.status = TaskStatus.FAILURE
            self.log.emit_record(type="error", message="Task Failed.", error=e)
            raise

    def start(self):
        """Called internally just before `run`."""
        self.status = TaskStatus.RUNNING
        self.log.start()

    def add_handler(self, handler: Callable[[dict], Any]):
        """Add a handler, a function that receives all log records from the Task."""

        self.log.add_handler(handler)

    def remove_handler(self, handler: Callable[[dict], Any]):
        """Remvoe a handler."""

        self.log.remove_handler(handler)

    def run(self) -> Any:
        return NotImplemented


class EncodeMov(Task):
    def __init__(self, src: PathType, dst: PathType, fps: int, max_size: int) -> None:
        self.src = Path(src)
        self.dst = Path(dst)
        self.fps = fps
        self.max_size = max_size
        super().__init__()

    def command(self) -> list[str]:
        # fmt: off
        cmd = [
            get_ffmpeg(),
            "-r", str(self.fps),
            "-i", str(self.src),
            "-c:v", "prores_ks",
            "-profile:v", "4444",
            "-qscale:v", "11",
            "-vendor", "apl0",
            "-pix_fmt", "yuva444p10le",
            "-alpha_bits", "16",
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
                "colorspace=space=bt709:primaries=bt709:trc=srgb:range=tv:ispace=bt709:iprimaries=bt709:itrc=linear:irange=tv"
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
        fs = FileSequence.from_file(self.src)
        if fs:
            cmd[1:1] = ["-start_number", str(fs.frame_start)]

        return cmd

    def run(self) -> PathType:
        # Ensure destination directory exists...
        self.dst.parent.mkdir(parents=True, exist_ok=True)

        cmd = self.command()

        self.log(f"  MOV: {self.src.name} -> {self.dst.name}")
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


class EncodeMp4(Task):
    def __init__(self, src: PathType, dst: PathType, fps: int, max_size: int) -> None:
        self.src = Path(src)
        self.dst = Path(dst)
        self.fps = fps
        self.max_size = max_size
        super().__init__()

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
        fs = FileSequence.from_file(self.src)
        if fs:
            cmd[1:1] = ["-start_number", str(fs.frame_start)]

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


class EncodeGif(Task):
    """Encode a GIF."""

    def __init__(
        self,
        src: PathType,
        dst: PathType,
        fps: int,
        max_size: int,
        max_colors: int,
    ) -> None:
        self.src = Path(src)
        self.dst = Path(dst)
        self.fps = fps
        self.max_size = max_size
        self.max_colors = max_colors
        super().__init__()

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
        fs = FileSequence.from_file(self.src)
        if fs:
            cmd[1:1] = ["-start_number", str(fs.frame_start)]

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


class EncodeFolder(Task):
    def __init__(self, folder: PathType, settings: Settings) -> None:
        super().__init__()
        self.folder = Path(folder)
        self.sequences = get_sequences(folder)
        self.settings = default_settings()
        self.settings.update(settings)
        self.prepare_tasks()

    def prepare_tasks(self):
        if not self.sequences:
            raise ValueError(f"No sequences found in '{self.folder}' ...")

        mov_folder = (self.folder / self.settings["mov_folder"]).resolve()
        mp4_folder = (self.folder / self.settings["mp4_folder"]).resolve()
        gif_folder = (self.folder / self.settings["gif_folder"]).resolve()

        task_count = 0
        task_groups = []
        for seq in self.sequences:
            task_group = []
            if self.settings["mov_enabled"]:
                mov_task = EncodeMov(
                    src=seq.path,
                    dst=mov_folder / (seq.stem + ".mov"),
                    fps=self.settings["mov_fps"],
                    max_size=self.settings["mov_size"],
                )
                task_group.append(mov_task)
                task_count += 1
            if self.settings["mp4_enabled"]:
                mp4_task = EncodeMp4(
                    src=seq.path,
                    dst=mp4_folder / (seq.stem + ".mp4"),
                    fps=self.settings["mp4_fps"],
                    max_size=self.settings["mp4_size"],
                )
                task_group.append(mp4_task)
                task_count += 1
            if self.settings["gif_enabled"]:
                gif_task = EncodeGif(
                    src=seq.path,
                    dst=gif_folder / (seq.stem + ".gif"),
                    fps=self.settings["gif_fps"],
                    max_size=self.settings["gif_size"],
                    max_colors=self.settings["gif_colors"],
                )
                task_group.append(gif_task)
                task_count += 1

            task_groups.append(task_group)

        self.task_groups = task_groups
        self.task_count = task_count
        self.log.total = task_count
        self.log(
            f"Found {len(self.task_groups)} file sequences. Prepared {self.task_count} tasks."
        )

    def run(self) -> list[PathType]:

        results = []
        for i, task_group in enumerate(self.task_groups):
            self.log(f"Sequence {i + 1} of {len(self.task_groups)}")
            for task in task_group:
                self.log.step(1)
                task()
                results.append(task.result)

        return results
