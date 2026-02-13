from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Annotated, Any, Literal, Mapping, Type, get_type_hints

from typeguard import TypeCheckError, check_type

_task_registry = {}
_type_registry = {}
_missing = object()

Size = Literal[-1, 256, 512, 768, 1024, 1280, 1920, 2048, 2160, 3840, 6144]
Fps = Literal[-1, 24, 25, 30, 48, 50, 60]
CodecH264 = Literal["h264", "h265", "vp9"]
CodecProres = Literal["Prores422", "Prores4444"]


def register_type(cls):
    """Register a dataclass so that it can be decoded from a string.

    Allowing it to be decoded from a dict representation.
    """
    _type_registry[cls.__name__] = cls
    return cls


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

    src: Path = field(metadata={"hidden": True})
    dst: Path

    def __post_init__(self):
        errors = validate_task_parameters(self.__class__, self.__dict__)
        if errors:
            raise ValueError(f"Invalid values: {errors}")

    def __call__(self) -> Any:
        return self.run()

    def __init_subclass__(cls, **kwargs):
        _task_registry[cls.__name__] = cls
        _type_registry[cls.__name__] = cls

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
        value = parameters.get(name, _missing)
        if not ignore_missing and value is _missing:
            errors[name] = "Missing argument."
            continue
        try:
            check_type(value, hint)
        except TypeCheckError as e:
            errors[name] = str(e)
    return errors


@register_type
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


@register_type
@dataclass
class Rule:
    name: str
    file_type: Literal["FileSequence", "File"]
    file_extensions: list[str]
    tasks: list[ParameterizedTask]


##########################
## Task Implementations ##
##########################


@register_type
@dataclass(frozen=True)
class Colorspace:
    name: str


@dataclass
class EncodeMp4(Task):
    input_colorspace: Colorspace = field(default=Colorspace("srgb"), kw_only=True)
    max_size: Size = field(default=-1, kw_only=True)
    fps: Fps = field(default=-1, kw_only=True)
    vcodec: CodecH264 = field(default="h264", kw_only=True)

    def run(self):
        print(self)


def encode(obj: Any):
    """Encode a dataclass as a dictionary."""

    # Check for dataclass types
    if obj in _type_registry.values():
        return {"__type__": obj.__name__}

    # Check for dataclass instances
    if type(obj).__name__ in _type_registry:
        result = dict(obj.__dict__)
        result["__class__"] = type(obj).__name__
        return encode(result)

    # Handle dictionaries
    if isinstance(obj, Mapping):
        result = {}
        for k, v in obj.items():
            result[k] = encode(v)
        return result

    # Handle Sequences
    if isinstance(obj, (list, tuple)):
        result = [encode(v) for v in obj]
        return result

    # Raw value
    return obj


def decode(obj: Any, key=None):
    """Decode a dataclass from a dictionary."""

    if key is None:
        key = []

    if isinstance(obj, Mapping):
        data = {}
        data_type_name = obj.pop("__type__", None)
        data_class_name = obj.pop("__class__", None)

        # Recursively decode data
        for k, v in obj.items():
            key.append(k)
            data[k] = decode(v, key)

        # Handle dataclass instances
        if data_class_name:
            data_cls = _type_registry.get(data_class_name)
            if data_cls:
                return data_cls(**data)
            return data

        # Handle dataclass types
        if data_type_name:
            return _type_registry.get(data_type_name)

        return data

    elif isinstance(obj, (list, tuple)):
        return [decode(v) for v in obj]

    return obj


def main():
    rule1 = Rule(
        name="Encode File Sequences",
        file_type="FileSequence",
        file_extensions=["*.*"],
        tasks=[
            parameterize(
                EncodeMp4,
                input_colorspace=Colorspace("linear"),
                max_size=1920,
                fps=24,
                vcodec="h264",
            )
        ],
    )
    rule2 = Rule(
        name="Encode File Sequences",
        file_type="FileSequence",
        file_extensions=["*.*"],
        tasks=[
            parameterize(
                EncodeMp4,
                input_colorspace=Colorspace("rgb"),
                max_size=512,
                fps=24,
                vcodec="h264",
            )
        ],
    )
    rules = [rule1, rule2]
    rules_data = encode(rules)
    rules_round_tripped = decode(rules_data)

    for rule in rules_round_tripped:
        for task in rule.tasks:
            task(src=Path("."), dst=Path(".."))

    from rich import print

    print()
    print(rules)


if __name__ == "__main__":
    main()
