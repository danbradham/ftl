from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Type

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
    path: Path
    name: str
    stem: str
    suffix: str

    def format(self, relative_to: PathType | None = None) -> str:
        if relative_to:
            path = self.path.relative_to(Path(relative_to))
        else:
            path = self.path
        return f"{path.as_posix()}"

    @classmethod
    def from_file(cls, file: PathType):
        path = Path(file)
        name = path.name
        stem = path.stem
        suffix = path.suffix
        return cls(path, name, stem, suffix)


@dataclass
class FileSequence:
    path: Path
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


def as_file(file: PathType):
    result = FileSequence.from_file(file)
    if not result:
        result = File.from_file(file)
    return result


def ls(folder: PathType, max_depth: int = 1) -> list[File | FileSequence]:
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

            f = as_file(file)
            seen.append(file)
            if isinstance(f, FileSequence):
                seen.extend(f.files)

            results.append(f)

    return sorted(
        results, key=lambda f: (-len(f.path.parts), isinstance(f, File), f.path)
    )


FileType = Type[File] | Type[FileSequence]


def main():
    for file in ls(Path("data"), max_depth=2):
        print(file.format())


if __name__ == "__main__":
    main()
