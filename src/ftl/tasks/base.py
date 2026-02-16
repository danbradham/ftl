from __future__ import annotations

import enum
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Any, Callable, Mapping, Type, get_type_hints

from typeguard import TypeCheckError, check_type

from ftl import registry

missing = object()


class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class TaskEvent:
    task_id: str
    task_type: str
    task_status: TaskStatus
    type: str


@dataclass()
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

    enabled: bool = field(default=True)

    def __post_init__(self):
        errors = validate_task_parameters(self.__class__, self.__dict__)
        if errors:
            lines = "\n".join([f"{k} -> {v}" for k, v in errors.items()])
            raise ValueError(f"Invalid values:\n {lines}")

        self.result = None
        self.error = None
        self.status = TaskStatus.PENDING
        self.log = TaskLog(self)
        self.sub_tasks = []

    def __init_subclass__(cls, **kwargs):
        registry.register_task(cls)

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

    @property
    def name(self):
        return self.__class__.__name__

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
    task_type: Type[Task]
    parameters: dict = field(default_factory=dict)

    def __call__(self, *args, **kwargs) -> Any:
        kwargs = dict(self.parameters, **kwargs)
        task = self.task_type(*args, **kwargs)
        return task()

    def get_parameters(self, exclude_hidden: bool = True) -> dict[str, Any]:
        parameters = {}
        for param in fields(self.task_type):
            if exclude_hidden and param.metadata.get("hidden", False):
                continue
            parameters[param.name] = getattr(self.task_type, param.name)
        return parameters


def parameterize(task: Type[Task], **parameters):
    """Return a task as a ParameterizedTask."""

    return ParameterizedTask(task, parameters)
