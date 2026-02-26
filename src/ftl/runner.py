import uuid
from dataclasses import dataclass, field
from logging import StreamHandler
from typing import Any

from ftl.files import File, FileSequence, ls
from ftl.logging import Log, RichFormatter, record_type
from ftl.rules import Rule
from ftl.settings import get_rules
from ftl.signals import Signals
from ftl.tasks import Task
from ftl.types import Status


@dataclass
class RunnerInvocation:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: Status = Status.PENDING
    signals: Signals = field(default_factory=Signals)
    progress: int = 0
    current_task: int = 0
    current_rule: int = 0
    files: list[File | FileSequence] = field(repr=False, default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    tasks_by_id: dict[str, Task] = field(default_factory=dict)
    tasks_count: int = 0
    rules: list[Rule] = field(repr=False, default_factory=list)
    rules_map: list[dict[str, Any]] = field(repr=False, default_factory=list)
    artifacts: list[Any] = field(default_factory=list)
    log_records: list = field(default_factory=list)

    def __post_init__(self):
        # Setup log
        self.log = Log(name=f"ftl.runner.{self.id}", record_type="runner")
        self.log.add_filter(self.prepare_record)

        # Define signals
        self.signals.define("status_changed", "Task status has changed.")
        self.signals.define("progress_changed", "Progress value has changed.")

    def prepare_record(self, record):
        # Add run status to record
        record.run_id = self.id
        record.run_status = self.status
        record.run_progress = self.progress

        # Add rule to record
        rule = self.rules[self.current_rule]
        record.rule_name = rule.name
        record.rule_description = rule.description
        record.rule_file_type = rule.file_type
        record.rule_file_patterns = rule.file_patterns

        # Add task to record
        task = self.tasks[self.current_task]
        record.task_id = task.id
        record.task_name = task.name
        record.task_progress = task.progress

        # Capture all logging records
        self.log_records.append(record)

    def set_status(self, status: Status):
        payload = {
            "type": "status_changed",
            "scope": "run",
            "id": self.id,
            "status": status,
            "prev_status": self.status,
            "progress": self.progress,
        }
        if status != self.status:
            self.log.info(
                f"Status changed from {self.status.upper()} to {status.upper()}."
            )
            self.status = status
            self.signals.send("status_changed", payload)

    def task_status_changed(self, event):
        task = self.tasks_by_id[event.payload["id"]]
        task_index = self.tasks.index(task)
        progress_per_step = 100.0 / self.tasks_count
        progress = event.payload["progress"] / 100.0
        self.progress = int(task_index * progress_per_step + progress * progress_per_step)


@dataclass
class Runner:
    rules: list[Rule]
    gui: bool = field(default=True)

    def _prepare_run(self, files: list[File | FileSequence]):
        inv = RunnerInvocation()
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

                    # Propagate log records
                    task.log.add_filter(inv.prepare_record)
                    task.log.add_handler(inv.log.handle)
                    # Connect to signals
                    task.signals.on("status_changed", inv.task_status_changed)

                    rule_map["tasks"].append(task)
                    inv.tasks_by_id[task.id] = task

            inv.rules.append(rule)
            inv.files.extend(rule_map["files"])
            inv.rules_map.append(rule_map)
            inv.tasks.extend(
                rule_map["tasks"] + [st for t in rule_map["tasks"] for st in t.sub_tasks]
            )
            inv.tasks_count += len(rule_map["tasks"]) + sum(
                [len(t.sub_tasks) for t in rule_map["tasks"]]
            )

        handler = StreamHandler()
        handler.setFormatter(RichFormatter())
        inv.log.addHandler(handler)

        return inv

    def run(
        self, files: list[File | FileSequence], dry: bool = False
    ) -> RunnerInvocation:

        # Prepare invocation
        # Generates all the tasks and info surrounding the run
        # this enables introspection and progress tracking.
        inv = self._prepare_run(files)

        inv.log.info(f"Starting Run with {inv.tasks_count} tasks.")
        inv.set_status(Status.RUNNING)

        for rule_idx, rule_map in enumerate(inv.rules_map):
            inv.current_rule = rule_idx
            rule = rule_map["rule"]
            inv.log.info(f"Rule {rule.name}")
            with record_type(inv.log, "rule"):
                for task_idx, task in enumerate(rule_map["tasks"]):
                    inv.current_task = task_idx
                    inv.log.info(f"{task.input.name} -> {task.output.name}")
                    try:
                        task_result = task()
                        inv.artifacts.append(task_result)
                    except Exception:
                        inv.set_status(Status.FAILED)
                        break

            if inv.status == Status.FAILED:
                inv.log.error(f"Cancelling run due to failed task.\n\n{task}\n\n")
                return inv

        inv.set_status(Status.SUCCESS)

        return inv


def main():

    # Get files
    files = ls("./data/tool", max_depth=2)

    # Get rules from settings
    rules = get_rules()

    # Execute rules tasks for each file.
    runner = Runner(rules, gui=False)
    runner.run(files)


if __name__ == "__main__":
    main()
