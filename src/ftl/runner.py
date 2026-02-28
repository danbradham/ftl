import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from ftl.files import File, FileSequence, ls
from ftl.logging import Log, RichFormatter, record_type
from ftl.rules import Rule
from ftl.settings import get_rules
from ftl.signals import Signals
from ftl.tasks import Task
from ftl.types import Status


@dataclass
class Runner:
    """Executes a set of Rules against a set of Files.

    Example:
        from ftl.settings import get_files
        from ftl.files import ls

        runner = Runner(
            rules=get_rules(),
            files=ls("...", max_depth=2),
        )
        runner.run()

    Attributes:
        rules: The list of Rules to run.
        files: The list of File objects to process.

    Signals:
        status_changed: Status has changed.
        progress_changed: Progress value has changed.
    """

    # User Attributes
    rules: list[Rule]
    files: list[File | FileSequence]

    # Interface Attributes
    signals: Signals = field(default_factory=Signals, init=False, repr=False)

    # State Attributes
    id: str = field(default_factory=lambda: uuid.uuid4().hex, init=False)
    status: Status = field(default=Status.PENDING, init=False)
    status_request: Status | None = field(default=None, init=False, repr=False)
    progress: int = field(default=0, init=False, repr=False)
    current_task: int = field(default=0, init=False, repr=False)
    current_rule: int = field(default=0, init=False, repr=False)
    tasks: list[Task] = field(default_factory=list, init=False, repr=False)
    tasks_count: int = field(default=0, init=False, repr=False)
    tasks_by_id: dict[str, Task] = field(default_factory=dict, init=False, repr=False)
    rules_map: list[dict[str, Any]] = field(default_factory=list, init=False, repr=False)
    artifacts: list[Any] = field(default_factory=list, init=False, repr=False)
    log: Log = field(init=False, repr=False)
    log_records: list = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        # Setup log
        self.log = Log(name=f"ftl.runner.{self.id}", record_type="runner")
        self.log.add_filter(self.prepare_record)

        # Define signals
        self.signals.define("status_changed", "Status has changed.")
        self.signals.define("progress_changed", "Progress value has changed.")
        self.signals.define("before_task", "Progress value has changed.")

        # Prepare Runner for invocation
        self._prepare_run(self.files)

    def _prepare_run(self, files: list[File | FileSequence]):
        enabled_rules = [rule for rule in self.rules if rule.enabled]
        if not enabled_rules:
            raise ValueError("At least one Rule must be enabled...")

        for rule in enabled_rules:
            if not rule.enabled:
                continue

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
                    task.log.add_filter(self.prepare_record)
                    task.log.add_handler(self.log.handle)
                    # Connect to signals
                    task.signals.on("status_changed", self.on_task_status_changed)

                    rule_map["tasks"].append(task)
                    self.tasks_by_id[task.id] = task

            self.files.extend(rule_map["files"])
            self.rules_map.append(rule_map)
            self.tasks.extend(
                rule_map["tasks"] + [st for t in rule_map["tasks"] for st in t.sub_tasks]
            )
            self.tasks_count += len(rule_map["tasks"]) + sum(
                [len(t.sub_tasks) for t in rule_map["tasks"]]
            )

        handler = logging.StreamHandler()
        handler.setFormatter(RichFormatter())
        self.log.addHandler(handler)

    def request(self, status: Status):
        self.status_request = status

    def accept(self, status: Status):
        self.set_status(status)
        self.status_request = None

    def _new_event_payload(self, **fields):
        payload = {
            "scope": "run",
            "id": self.id,
            "status": self.status,
            "prev_status": self.status,
            "progress": self.progress,
        }
        payload.update(fields)
        return payload

    def set_status(self, status: Status):
        if status == self.status:
            return

        prev_status = self.status
        payload = self._new_event_payload(
            type="status_changed",
            status=status,
            prev_status=prev_status,
            label=status,
        )
        self.status = status
        self.log.info(f"Status changed from {prev_status.upper()} to {status.upper()}.")
        self.signals.send("status_changed", payload)

    def on_task_status_changed(self, event):
        task = self.tasks_by_id[event.payload["id"]]
        task_index = self.tasks.index(task)
        progress_per_step = 100.0 / self.tasks_count
        progress = event.payload["progress"] / 100.0
        self.progress = int(task_index * progress_per_step + progress * progress_per_step)
        payload = self._new_event_payload(
            type="progress_changed",
            label=f"{self.rules[self.current_rule].name}",
            message=f"{task_index + 1} of {self.tasks_count}",
            # message=f"{task_index + 1} of {self.tasks_count}: {task.name}",
        )
        self.signals.send("progress_changed", payload)

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

    def try_task(self, task):
        try:
            task()
            self.artifacts.append(task.result)
        except Exception as e:
            self.set_status(Status.FAILED)
            raise RuntimeError(f"Task failed: {task.name}\n{e}")

    def run(self, dry: bool = False):

        self.log.info(f"\nEnabled Rules ({len(self.rules)})")
        self.log.info("\n".join([f"  {rule.name}" for rule in self.rules]))

        self.log.info("\nStarting Run...")
        self.set_status(Status.RUNNING)

        for rule_idx, rule_map in enumerate(self.rules_map):
            self.current_rule = rule_idx
            rule = rule_map["rule"]
            self.log.info(f"Rule {rule.name}")
            with record_type(self.log, "rule"):
                for task_idx, task in enumerate(rule_map["tasks"]):
                    # Send before_task signal
                    self.signals.send("before_task", self._new_event_payload(task=task))

                    # Check if user has requested cancel
                    if self.status_request == Status.CANCELLED:
                        return self.accept(Status.CANCELLED)

                    self.current_task = task_idx
                    self.log.info(f"{task.input.name} -> {task.output.name}")
                    self.try_task(task)

            if self.status == Status.FAILED:
                self.log.error(f"Cancelling run due to failed task.\n\n{task}\n\n")
                return

        self.set_status(Status.SUCCESS)

        return


def main():
    from ftl.ui.progress import ProgressDialog

    # Execute rules tasks for each file.
    runner = Runner(
        rules=get_rules(),
        files=ls("./data/tool", max_depth=2),
    )
    progress = ProgressDialog.from_runner(runner)
    runner.run()


if __name__ == "__main__":
    main()
