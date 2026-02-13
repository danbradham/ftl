from dataclasses import dataclass, field
from typing import Literal

from ftl.tasks.base import Task
from ftl.tasks.parameter_types import Fps, Size

CodecProres = Literal["Prores422", "Prores4444"]


@dataclass
class EncodeMov(Task):
    input_colorspace: str = field(default="srgb", kw_only=True)
    vcodec: CodecProres = field(default="Prores4444", kw_only=True)
    fps: Fps = field(default=-1, kw_only=True)
    max_size: Size = field(default=-1, kw_only=True)

    def run(self):
        print(self)
