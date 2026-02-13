from typing import Any, Type

tasks = {}
types = {}


def register_task(task: Type["Task"]):
    """Register a Task with FTL.

    You don't need to use this yourself, it happens in Task.__init_subclass__.
    """

    tasks[task.__name__] = task
    types[task.__name__] = task
    return task


def register_type(type: Type[Any]):
    """Register a dataclass with FTL.

    This registry is primarily used to help with serialization of Rules.
    If you're defining a Task and one of the parameters uses a custom Type
    you should register it!

    Registering a type to be used as a Parameter for a Task:
        @register_type
        @dataclass
        class OcioDisplayTransform:
            input: Literal["ACEScg", "Linear Rec.709 (sRGB)"] = "Linear Rec.709 (sRGB)"
            display_device: Literal["sRGB - Display", "Rec.1886 Rec.709 - Display"] = "sRGB - Display"
            view_transform: Literal["ACES 1.0 - SDR Video", "Un-tone-mapped", "Raw"] = "ACES 1.0 - SDR Video"

        @dataclass
        class MyTask(Task):
            ocio_display: OcioDisplayTransform
    """

    types[type.__name__] = type
    return type
