from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Any, Mapping, Type, get_type_hints

from typeguard import TypeCheckError, check_type

from ftl import registry
from ftl.files import FileType

missing = object()


@dataclass
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

    file: FileType = field(metadata={"hidden": True})
    enabled: bool = field(default=True)

    def __post_init__(self):
        errors = validate_task_parameters(self.__class__, self.__dict__)
        if errors:
            raise ValueError(f"Invalid values: {errors}")

    def __call__(self) -> Any:
        return self.run()

    def __init_subclass__(cls, **kwargs):
        registry.register_task(cls)

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
