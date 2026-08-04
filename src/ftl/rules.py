from collections.abc import Mapping
from dataclasses import dataclass, field, is_dataclass
from fnmatch import fnmatch
from typing import Any, Literal, get_type_hints

from cattrs import (
    register_structure_hook,
    register_unstructure_hook,
    structure,
    unstructure,
)

from ftl import registry, tools
from ftl.tasks import ParameterizedTask


@registry.register_type
@dataclass
class Rule:
    name: str
    file_type: Literal["File", "FileSequence"]
    file_patterns: list[str]
    tasks: list[ParameterizedTask]
    ocio_enabled: bool = field(default=False)
    ocio_input_transform: str = field(
        default_factory=tools.get_ocio_default_input_transform,
        metadata={
            "hidden": False,
            "help": "The colorspace of the source media.",
            "param_type": "ocio_input_transform",
        },
    )
    ocio_display_device: str = field(
        default_factory=tools.get_ocio_default_display_device,
        metadata={
            "hidden": False,
            "help": "The device used to display the output media.",
            "param_type": "ocio_output_transform",
        },
    )
    ocio_view_transform: str = field(
        default_factory=tools.get_ocio_default_view_transform,
        metadata={
            "hidden": False,
            "help": "The view transform used to display the output media.",
            "param_type": "ocio_view_transform",
        },
    )
    description: str = field(default="")
    enabled: bool = field(default=True)
    schema_version: int = field(default=2, metadata={"hidden": True})

    @property
    def fname(self):
        return self.name.lower().replace(" ", "_")

    def accepts(self, file):
        is_correct_file_type = file.is_sequence == (self.file_type == "FileSequence")

        # Evaluate file_patterns to check if the file can be
        # accepted by this rule.
        is_included = False
        for pat in self.file_patterns:
            # Patterns that start with ! are exlusion patterns
            if pat.startswith("!") and fnmatch(file.name, pat.lstrip("!")):
                is_included = False
                break

            # Check if file name matches the inclusion pattern
            if fnmatch(file.name, pat):
                is_included = True

        return is_correct_file_type and is_included

    @classmethod
    def from_dict(cls, data):
        return structure(data, cls)


@register_unstructure_hook
def unstructure_rule(rule: Rule):
    return {
        "schema_version": rule.schema_version,
        "enabled": rule.enabled,
        "name": rule.name,
        "description": rule.description,
        "file_type": rule.file_type,
        "file_patterns": rule.file_patterns,
        "ocio_enabled": rule.ocio_enabled,
        "ocio_input_transform": rule.ocio_input_transform,
        "ocio_display_device": rule.ocio_display_device,
        "ocio_view_transform": rule.ocio_view_transform,
        "tasks": [unstructure(t) for t in rule.tasks],
    }


@register_unstructure_hook
def unstructure_parameterized_task(pt: ParameterizedTask):
    return {
        "task": pt.task.__name__,
        "parameters": unstructure(pt.parameters),
    }


@register_structure_hook
def structure_rule(val: Any, _) -> Rule:
    schema_version = val.get("schema_version", Rule.schema_version)
    if schema_version > Rule.schema_version:
        raise ValueError(
            f"This version of FTL only supports "
            f"Rule.schema_version <= {Rule.schema_version}"
        )

    # Apply Schema Migrations here.
    # - Apply cascading upgrades...
    # - If a migration can not fully maintain the behavior
    #   or a previous rule. Set data["enabled"] = False.
    #   This will allow users to complete the changes.
    if schema_version == 1:
        val["ocio_enabled"] = False
        val["ocio_input_transform"] = tools.get_ocio_default_input_transform()
        val["ocio_display_device"] = tools.get_ocio_default_display_device()
        val["ocio_view_transform"] = tools.get_ocio_default_view_transform()
        val["schema_version"] = 2
    # if schema_version == 2:
    #     ...
    #     data["schema_version"] = 3

    return Rule(
        enabled=val.get("enabled", True),
        description=val.get("description", ""),
        name=val["name"],
        file_type=val["file_type"],
        file_patterns=val["file_patterns"],
        ocio_enabled=val["ocio_enabled"],
        ocio_input_transform=val["ocio_input_transform"],
        ocio_display_device=val["ocio_display_device"],
        ocio_view_transform=val["ocio_view_transform"],
        tasks=[structure(t, ParameterizedTask) for t in val["tasks"]],
    )


@register_structure_hook
def structure_parameterized_task(val: Any, _) -> ParameterizedTask:
    task = registry.types.get(val["task"])
    parameters = {}
    hints = get_type_hints(task)
    for key, value in val["parameters"].items():
        hint = hints.get(key)
        if is_dataclass(hint) and isinstance(hint, type) and isinstance(value, Mapping):
            parameters[key] = hint(**value)
        else:
            parameters[key] = unstructure(value, hint)
    return ParameterizedTask(task, parameters)


def default_rules() -> list[Rule]:
    """Get the default Rules."""

    from ftl.tasks import EncodeGif, EncodeMov, EncodeMp4, parameterize

    encode_mov = parameterize(
        EncodeMov,
        enabled=True,
        folder="..",
        fps=24,
        max_size=3840,
    )
    encode_mp4 = parameterize(
        EncodeMp4,
        enabled=True,
        folder="..",
        fps=24,
        max_size=1920,
    )
    encode_gif = parameterize(
        EncodeGif,
        enabled=True,
        folder="..",
        fps=24,
        max_size=1024,
        max_colors=64,
    )

    return [
        Rule(
            name="EXR Sequence (acescg)",
            file_type="FileSequence",
            file_patterns=["*acescg*.exr"],
            ocio_enabled=True,
            ocio_input_transform="ACEScg",
            ocio_display_device="sRGB - Display",
            ocio_view_transform="ACES 1.0 - SDR Video",
            tasks=[encode_mov, encode_mp4, encode_gif],
        ),
        Rule(
            name="EXR Sequence (srgb)",
            file_type="FileSequence",
            file_patterns=["*.exr"],
            ocio_enabled=True,
            ocio_input_transform="Linear Rec.709 (sRGB)",
            ocio_display_device="sRGB - Display",
            ocio_view_transform="ACES 1.0 - SDR Video",
            tasks=[encode_mov, encode_mp4, encode_gif],
        ),
        Rule(
            name="SDR Sequence",
            file_type="FileSequence",
            file_patterns=["*"],
            ocio_enabled=False,
            tasks=[encode_mov, encode_mp4, encode_gif],
        ),
    ]
