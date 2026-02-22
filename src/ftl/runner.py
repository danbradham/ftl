import enum
from dataclasses import dataclass, field
from typing import Any

from ftl.files import File, FileSequence, ls
from ftl.rules import Rule
from ftl.settings import get_settings
from ftl.tasks import Task


class RunnerStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class RunnerInvocation:
    status: RunnerStatus = RunnerStatus.PENDING
    current_task: int = 0
    files: list[File | FileSequence] = field(repr=False, default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    tasks_count: int = 0
    rules: list[Rule] = field(repr=False, default_factory=list)
    rules_map: list[dict[str, list[Task]]] = field(repr=False, default_factory=list)
    artifacts: list[Any] = field(default_factory=list)


@dataclass
class Runner:
    rules: list[Rule]
    gui: bool = field(default=True)

    def _prepare_run(self, files: list[File | FileSequence]):
        invocation = RunnerInvocation()
        for rule in self.rules:
            rule_map = {
                "rule": rule,
                "files": [],
                "tasks": [],
            }
            for file in files:
                if not rule.accepts(file):
                    continue

                rule_map["files"].append(file)
                for parameterized_task in rule.tasks:
                    task_type = parameterized_task.task
                    task_parameters = parameterized_task.parameters
                    task_parameters["input"] = file
                    task = task_type(**task_parameters)
                    rule_map["tasks"].append(task)

            invocation.rules.append(rule)
            invocation.files.extend(rule_map["files"])
            invocation.rules_map.append(rule_map)
            invocation.tasks.extend(
                rule_map["tasks"] + [st for t in rule_map["tasks"] for st in t.sub_tasks]
            )
            invocation.tasks_count += len(rule_map["tasks"]) + sum(
                [len(t.sub_tasks) for t in rule_map["tasks"]]
            )

        return invocation

    def run(
        self, files: list[File | FileSequence], dry: bool = False
    ) -> RunnerInvocation:

        if not self.gui:
            from rich import print

        # Prepare invocation
        # Generates all the tasks and info surrounding the run
        # this will enable some better introspection and
        # progress tracking.
        invocation = self._prepare_run(files)

        for rule_map in invocation.rules_map:
            # Executing Rule
            print(rule_map["rule"].name)
            for task in rule_map["tasks"]:
                print(f"  - {task.name} - {task.input.path}")
                invocation.artifacts.append(task())

        print("Artifacts:")
        print(invocation.artifacts)

        return invocation


def main():

    # Get files
    files = ls("./data/tool", max_depth=2)

    # Get rules from settings
    rules = get_settings()["rules"]

    # Execute rules tasks for each file.
    runner = Runner(rules, gui=False)
    runner.run(files)


if __name__ == "__main__":
    main()
