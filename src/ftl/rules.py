from dataclasses import dataclass, field, is_dataclass
from typing import Any, Literal, Mapping, get_type_hints

from cattrs import (
    register_structure_hook,
    register_unstructure_hook,
    structure,
    unstructure,
)

from ftl import registry
from ftl.tasks import ParameterizedTask


@registry.register_type
@dataclass
class Rule:
    name: str
    file_type: Literal["File", "FileSequence"]
    file_patterns: list[str]
    tasks: list[ParameterizedTask]
    description: str = field(default="")
    enabled: bool = field(default=True)
    schema_version: int = field(default=1, metadata={"hidden": True})

    @classmethod
    def from_dict(cls, data):
        return structure(data, cls)


@register_unstructure_hook
def unstructure_rule(rule: Rule):
    return {
        "name": rule.name,
        "description": rule.description,
        "file_type": rule.file_type,
        "file_patterns": rule.file_patterns,
        "enabled": rule.enabled,
        "schema_version": rule.schema_version,
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
    # if schema_version == 1:
    #     ...
    #     data["schema_version"] = 2
    # if schema_version == 2:
    #     ...
    #     data["schema_version"] = 3

    return Rule(
        enabled=val.get("enabled", True),
        description=val.get("description", ""),
        name=val["name"],
        file_type=val["file_type"],
        file_patterns=val["file_patterns"],
        tasks=[structure(t, ParameterizedTask) for t in val["tasks"]],
    )


@register_structure_hook
def structure_parameterized_task(val: Any, _) -> ParameterizedTask:
    task = registry.types.get(val["task"])
    parameters = {}
    hints = get_type_hints(task)
    for key, value in val["parameters"].items():
        hint = hints.get(key)
        if is_dataclass(hint) and isinstance(value, Mapping):
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
        fps=-1,
        max_size=3840,
    )
    encode_mp4 = parameterize(
        EncodeMp4,
        enabled=True,
        folder="..",
        fps=-1,
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
            name="Encode Sequences",
            file_type="FileSequence",
            file_patterns=["*"],
            tasks=[encode_mov, encode_mp4, encode_gif],
        ),
    ]
