from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Literal

Size = Literal[-1, 256, 512, 768, 1024, 1280, 1920, 2048, 2160, 3840, 4096, 6144]
Fps = Literal[-1, 8, 12, 15, 24, 25, 30, 48, 50, 60]


class Status(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    REVOKED = "revoked"
    CANCELLED = "cancelled"
    DONE = ",".join([SUCCESS, FAILED, REVOKED, CANCELLED])


ColorHex = str


@dataclass
class RgbaF:
    r: float
    g: float
    b: float
    a: float


@dataclass
class Rgba:
    r: int
    g: int
    b: int
    a: int
