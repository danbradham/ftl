from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from dataclasses import dataclass, field

from rich.style import Style


@contextmanager
def record_type(log: Log, record_type: str):
    try:
        log._record_type_stack.append(record_type)
        yield
    finally:
        log._record_type_stack.pop()


@dataclass
class Log:
    name: str
    record_type: str
    logger: logging.Logger = field(init=False, repr=False)

    def __post_init__(self):
        self.logger = logging.getLogger(self.name)
        self.setLevel(logging.INFO)
        self.add_filter(self.prepare_record)
        self._record_type_stack = []

    def __getattr__(self, attr):
        # Redirect logging methods to underlying logger
        return getattr(self.logger, attr)

    def get_record_type(self):
        if self._record_type_stack:
            return self._record_type_stack[-1]
        return self.record_type

    def prepare_record(self, record):
        if hasattr(record, "type"):
            return

        record.type = self.get_record_type()

    def add_filter(self, func):
        self.logger.addFilter(FilterFunction(func))

    def add_handler(self, func):
        self.logger.addHandler(HandlerFunction(func))


class FilterFunction(logging.Filter):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def filter(self, record):
        self.func(record)
        return True


class HandlerFunction(logging.Handler):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def emit(self, record):
        self.func(record)


class RichFormatter(logging.Formatter):
    styles = {
        "pending": (
            Style(color="yellow", bold=True),
            re.compile(r"PENDING"),
        ),
        "running": (
            Style(color="blue", bold=True),
            re.compile(r"RUNNING"),
        ),
        "success": (
            Style(color="green"),
            re.compile(r"SUCCESS"),
        ),
        "failed": (
            Style(color="red"),
            re.compile(r"FAILED"),
        ),
        "revoked": (
            Style(color="purple"),
            re.compile(r"REVOKED"),
        ),
    }

    # fmt: off
    formatters = {
        "runner": logging.Formatter("%(message)s"),
        "rule": logging.Formatter("%(task_name)s [%(run_progress)3d%%] %(message)s"),
        "task": logging.Formatter("  %(task_status)s [%(task_progress)3d%%] %(message)s"),
        "default": logging.Formatter("%(levelname)s | %(message)s")
    }
    # fmt: on

    def apply_styles(self, msg):
        for style, pattern in self.styles.values():
            for match in pattern.finditer(msg):
                substr = match.group()
                msg = msg.replace(substr, style.render(substr))
        return msg

    def format(self, record):
        formatter = self.formatters.get(record.type, self.formatters["default"])
        return self.apply_styles(formatter.format(record))
