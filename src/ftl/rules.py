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
    enabled: bool = field(default=True)
    schema_version: int = field(default=1, metadata={"hidden": True})

    @classmethod
    def from_dict(cls, data):
        schema_version = data.get("schema_version", cls.schema_version)
        if schema_version > cls.schema_version:
            raise ValueError(
                f"This version of FTL only supports "
                f"Rule.schema_version <= {cls.schema_version}"
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
        if schema_version == cls.schema_version:
            return cls(**data)


@register_unstructure_hook
def unstructure_rule(rule: Rule):
    return {
        "name": rule.name,
        "file_type": rule.file_type,
        "file_patterns": rule.file_patterns,
        "enabled": rule.enabled,
        "schema_version": rule.schema_version,
        "tasks": [unstructure(t) for t in rule.tasks],
    }


@register_unstructure_hook
def unstructure_parameterized_task(pt: ParameterizedTask):
    return {
        "task_type": pt.task_type.__name__,
        "parameters": unstructure(pt.parameters),
    }


@register_structure_hook
def structure_rule(val: Any, _) -> Rule:
    return Rule(
        name=val["name"],
        file_type=val["file_type"],
        file_patterns=val["file_patterns"],
        tasks=[structure(t, ParameterizedTask) for t in val["tasks"]],
    )


@register_structure_hook
def structure_parameterized_task(val: Any, _) -> ParameterizedTask:
    task_type = registry.types.get(val["task_type"])
    parameters = {}
    hints = get_type_hints(task_type)
    for key, value in val["parameters"].items():
        hint = hints.get(key)
        if is_dataclass(hint) and isinstance(value, Mapping):
            parameters[key] = hint(**value)
        else:
            parameters[key] = unstructure(value, hint)
    return ParameterizedTask(task_type, parameters)


def main():
    from rich import print

    from ftl.files import as_file
    from ftl.tasks import EncodeMp4, parameterize

    rule1 = Rule(
        name="Encode File",
        file_type="FileSequence",
        file_patterns=["*.mov"],
        tasks=[
            parameterize(
                EncodeMp4,
                input_colorspace="linear",
                max_size=1920,
                fps=24,
                vcodec="h264",
            )
        ],
    )
    rule2 = Rule(
        name="Encode File Sequences",
        file_type="FileSequence",
        file_patterns=["*"],
        tasks=[
            parameterize(
                EncodeMp4,
                input_colorspace="rgb",
                max_size=512,
                fps=24,
                vcodec="h264",
            )
        ],
    )
    rules = [rule1, rule2]
    rules_data = unstructure(rules)
    print(rules_data)
    rules_round_tripped = structure(rules_data, list[Rule])
    print("\n\n\n")
    print(rules_round_tripped)

    for rule in rules_round_tripped:
        for task in rule.tasks:
            task(file=as_file("."))

    print("\n\n\n")
    print(rules)
    assert rules == rules_round_tripped


if __name__ == "__main__":
    main()
