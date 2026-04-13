from __future__ import annotations

import sys
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from time import sleep
from typing import Any, ClassVar, Mapping, Type, get_origin, get_type_hints

from typeguard import TypeCheckError, check_type

from ftl import registry
from ftl.files import File, FileSequence
from ftl.logging import Log
from ftl.signals import Signals
from ftl.types import Status

missing = object()


@dataclass(kw_only=True)
class Task(ABC):
    """Base class for all Tasks.

    Subclasses must be be decorated as a dataclass.
    ```
    @dataclass
    class MyTask(Task):
        size: Literal[-1, 16, 32, 64]

        def run(self):
            print(f"Size is {size}")
    ```
    """

    # Hidden tasks will not show up in the UI...
    hidden: ClassVar[bool] = False

    # Shared Task Parameters
    id: str = field(
        default_factory=lambda: uuid.uuid4().hex,
        metadata={
            "hidden": True,
            "help": "Unique identifier for the task.",
        },
    )
    enabled: bool = field(
        default=True,
        metadata={
            "help": "Whether the task is enabled.",
        },
    )
    input: File | FileSequence = field(
        metadata={
            "hidden": True,
            "help": "The source File or FileSequence to encode.",
        }
    )
    # output: Any = field(
    #     default=None,
    #     metadata={
    #         "hidden": True,
    #         "help": (
    #             "The output the Task is expected to produce. "
    #             "Can be any type like a Path or just a String description. "
    #             "Subclasses should initialize this in a __post_init__ method."
    #         ),
    #         "validate": False,
    #     },
    # )

    def __post_init__(self):
        errors = validate_task_parameters(self.__class__, self.__dict__)
        if errors:
            lines = "\n".join([f"{k} -> {v}" for k, v in errors.items()])
            raise ValueError(f"Invalid values:\n {lines}")

        # Setup Task Logger
        self.log = Log(name=f"ftl.task.{self.id}", record_type="task")
        self.log.add_filter(self.prepare_record)

        # Define some signals
        self.signals = Signals()
        self.signals.define("status_changed", "Task status has changed.")
        self.signals.define("started", "Task has started running.")
        self.signals.define("completed", "Task has completed.")

        # Define Task state
        self.status: Status = Status.PENDING
        self.status_request: Status | None = None
        self.progress = 0
        self.output = None
        self.result = None
        self.error = None
        self.sub_tasks = []

        # Call setup if defined
        self.setup()

    def __init_subclass__(cls, **kwargs):
        cls.name = cls.__name__
        registry.register_task(cls)

    def __call__(self):
        """Start and run the Task."""

        if self.status_request in (Status.CANCELLED, Status.REVOKED):
            return self.accept(self.status_request)

        self.set_status(Status.RUNNING, 0)
        try:
            self.result = self.run()
            self.set_status(Status.SUCCESS, 100)
            return self.result
        except Exception:
            self.error = sys.exc_info()
            self.log.exception("Task failed...")
            self.set_status(Status.FAILED)
            raise

    def prepare_record(self, record):
        """Add context to logging records."""

        record.task_id = self.id
        record.task_name = self.name
        record.task_status = self.status
        record.task_status_request = self.status_request
        record.task_progress = self.progress
        record.task_result = self.result
        record.task_error = self.error

    # Public Interface
    def set_status(
        self, status: Status, progress: int | None = None, message: str | None = None
    ):
        payload = {
            "type": "status_changed",
            "scope": "task",
            "id": self.id,
            "name": self.name,
            "status": status,
            "prev_status": self.status,
            "progress": progress or self.progress,
        }
        self.status = payload["status"]
        self.progress = payload["progress"]
        if payload["status"] != payload["prev_status"] and not message:
            message = (
                "Status changed from "
                f"{payload['prev_status'].upper()} to {payload['status'].upper()}."
            )
        self.log.info(message)
        self.signals.send("status_changed", payload)

    def set_progress(self, progress: int, message: str | None = None):
        self.set_status(
            self.status, progress, message or f"Progress changed to {progress}%"
        )

    def request(self, status):
        self.log.info(f"{status.upper()} requested...")
        self.status_request = status

    def accept(self, status):
        self.log.debug(f"{status.upper()} accepted...")
        self.set_status(status)
        self.status_request = None

    def wait(self):
        while self.status not in Status.DONE:
            sleep(0.1)
        return self.status

    # Subclassing Interface
    def setup(self):
        return NotImplemented

    @abstractmethod
    def run(self) -> Any:
        return NotImplemented


def validate_task_parameters(
    task: Type[Task],
    parameters: Mapping[str, Any],
    ignore_missing=False,
) -> dict[str, str]:
    """Validate parameters against a Task's type hints."""

    errors = {}
    for name, hint in get_type_hints(task).items():
        if get_origin(hint) is ClassVar:
            continue

        value = parameters.get(name, missing)
        if not ignore_missing and value is missing:
            errors[name] = "Missing argument."
            continue
        try:
            check_type(value, hint)
        except TypeCheckError as e:
            errors[name] = str(e)
    return errors


@registry.register_type
@dataclass
class ParameterizedTask:
    """A Task wrapper.

    This allows Tasks' to be configured / serialized to be called later.
    """

    task: Type[Task]
    parameters: dict = field(default_factory=dict)

    def __post_init__(self):
        self.name = self.task.name

    def __call__(self, *args, **kwargs) -> Any:
        kwargs = dict(self.parameters, **kwargs)
        task = self.task(*args, **kwargs)
        return task()

    def get_parameters(self, exclude_hidden: bool = True) -> dict[str, Any]:
        parameters = {}
        for param in fields(self.task):
            if exclude_hidden and param.metadata.get("hidden", False):
                continue
            parameters[param.name] = param
        return parameters


def parameterize(task: Type[Task], **parameters):
    """Wrap a Task in a ParameterizedTask."""

    return ParameterizedTask(task, parameters)
