from dataclasses import dataclass, field
from typing import Literal

from ftl.tasks.base import Task
from ftl.tasks.parameter_types import Fps, Size

CodecH264 = Literal["h264", "h265", "vp9"]


@dataclass
class EncodeMp4(Task):
    input_colorspace: str = field(default="srgb", kw_only=True)
    vcodec: CodecH264 = field(default="h264", kw_only=True)
    fps: Fps = field(default=-1, kw_only=True)
    max_size: Size = field(default=-1, kw_only=True)

    def run(self):
        print(self)
