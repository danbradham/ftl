from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path

PathType = Path | os.PathLike | str


image_formats = [
    ".exr",
    ".png",
    ".tif",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".tiff",
    ".webp",
    ".heic",
    ".heif",
    ".avif",
]
video_formats = [
    ".mov",
    ".mp4",
    ".avi",
    ".mkv",
    ".webm",
    ".gif",
]


@dataclass
class File:
    # Shared fields
    path: Path
    name: str
    stem: str
    suffix: str

    # Sequence fields
    is_sequence: bool = False
    padding: int = 0
    padding_str: str = ""
    frame_start: int = 0
    frame_end: int = 0
    files: list[Path] = field(repr=False, default_factory=list)
    missing_frames: list[int] = field(repr=False, default_factory=list)

    def format(self, relative_to: PathType | None = None) -> str:
        """Format the File object's path as a string.

        Examples:
            /path/to/file.mov
            /path/to/other_file.%04d.exr [1-120]
            /path/to/other_file.%04d.png [1-90]
              missing [24, 33, 72]
        """

        if relative_to:
            path = self.path.relative_to(Path(relative_to))
        else:
            path = self.path

        result = f"{path.as_posix()}"
        if self.is_sequence:
            result += f" [{self.frame_start}-{self.frame_end}]"
            if self.missing_frames:
                result += f"\n  missing {self.missing_frames}"
        return result

    def exists(self):
        """Check if a File object exists on disk."""

        if self.is_sequence:
            return all(f.exists() for f in self.files)
        else:
            return self.path.exists()

    def remap(
        self,
        folder: PathType,
        suffix: str | None = None,
    ) -> File:
        """Remaps a File object to a new folder.

        Example:
            file = File.from_path("/path/to/file.%04d.png)
            remapped = file.remap("/another/path", suffix=".exr")
        """

        folder = Path(folder)
        suffix = suffix or self.suffix
        if self.is_sequence:
            return replace(
                self,
                path=folder / self.name.replace(self.suffix, suffix),
                name=self.name.replace(self.suffix, suffix),
                suffix=suffix,
                files=[folder / f.name.replace(f.suffix, suffix) for f in self.files],
            )
        else:
            return replace(
                self,
                path=folder / self.name.replace(self.suffix, suffix),
                name=self.name.replace(self.suffix, suffix),
                suffix=suffix,
            )

    def as_temp_file(self, suffix: str | None = None) -> File:
        """Remap a File object to a temporary folder."""

        return self.remap(
            tempfile.mkdtemp(prefix="ftl_", suffix=suffix),
            suffix,
        )

    # Factory Methods
    @classmethod
    def from_path(cls, path: PathType) -> File:
        """Constructs a File object from a pathlib.Path object or an os.PathLike."""

        return cls._from_path_sequence(path) or cls._from_path(path)

    @classmethod
    def _from_path(cls, path: PathType) -> File:
        path = Path(path)
        name = path.name
        stem = path.stem
        suffix = path.suffix
        return cls(path, name, stem, suffix)

    @classmethod
    def _from_path_sequence(cls, path: PathType) -> File | None:
        path = Path(path)
        # Check if we're dealing with a file sequence pattern...
        match = None
        if (
            (matches := re.findall(r"#+", path.as_posix()))
            or (matches := re.findall(r"%\d+d", path.as_posix()))
            or (matches := re.findall(r"\.(\d+)\.", path.as_posix()))
        ):
            match = matches[-1]
        else:
            return

        is_sequence = True
        padding = len(match)
        suffix = path.suffix
        files = sorted(path.parent.glob(path.name.replace(match, "*")))
        frames = []
        frame_re = re.compile(path.as_posix().replace(match, r"(\d+)"))
        for f in files:
            if fmatch := frame_re.search(f.as_posix()):
                frame = int(fmatch.group(1))
                frames.append(frame)

        padding_str = f"%{padding:0>2d}d"
        name = path.name.replace(match, padding_str)
        stem = path.name.split(match)[0].strip(".")
        path = path.with_name(name)
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
            is_sequence,
            padding,
            padding_str,
            frames[0],
            frames[-1],
            files,
            missing_frames,
        )


def ls(folder: PathType, max_depth: int = 1) -> list[File]:
    """List of all the File and FileSequences in a folder."""

    results = []
    seen = []

    folder = Path(folder)
    for root, subdirs, files in os.walk(folder):
        depth = len(Path(root).relative_to(folder).parts) + 1
        if depth >= max_depth:
            subdirs[:] = []

        for file in ((Path(root) / f) for f in files):
            if file in seen:
                continue

            f = File.from_path(file)
            seen.append(file)
            if f.is_sequence:
                seen.extend(f.files)

            results.append(f)

    return sorted(
        results, key=lambda f: (-len(f.path.parts), isinstance(f, File), f.path)
    )


FileType = type[File]
