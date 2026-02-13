from dataclasses import dataclass, field
from typing import Literal

from ftl.tasks.base import Task
from ftl.tasks.parameter_types import Fps, Size

MaxColors = Literal[4, 8, 16, 32, 64, 128, 256]


@dataclass
class EncodeGif(Task):
    input_colorspace: str = field(default="srgb", kw_only=True)
    fps: Fps = field(default=24, kw_only=True)
    max_size: Size = field(default=768, kw_only=True)
    max_colors: MaxColors = field(default=256, kw_only=True)

    def run(self):
        print(self)
