import logging
import time
import uuid
from dataclasses import dataclass, field
from threading import Thread
from typing import Any

from ftl import tasks
from ftl.files import File, ls
from ftl.logging import FileFormatter, Log, RichFormatter, record_type
from ftl.rules import Rule
from ftl.settings import USER_DATA_DIR, get_rules
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
    files: list[File]

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
        self.signals.define("before_task", "Task about to change...")

        # Prepare Runner for invocation
        self._prepare_run(self.files)

    def _add_task(self, task: Task):
        # Propagate log records
        task.log.add_filter(self.prepare_record)
        task.log.add_handler(self.log.handle)
        # Connect to signals
        task.signals.on("status_changed", self.on_task_status_changed)
        # Track task
        self.tasks_by_id[task.id] = task
        self.tasks.append(task)

    def _prepare_run(self, files: list[File]):
        # This method prepares the Runner to be executed by filtering
        # files that are accepted by each of the Runner's Rules,
        # then generating all the necessary tasks.
        # This is essential for fine-grained tracking of progress
        # throughout the encoding pipeline.

        enabled_rules = [rule for rule in self.rules if rule.enabled]
        if not enabled_rules:
            raise ValueError("At least one Rule must be enabled...")

        self.rules_map = [
            {"rule": rule, "files": [], "tasks": [], "file_tasks": []}
            for rule in enabled_rules
        ]

        for file in files:
            for rule_map in self.rules_map:
                rule = rule_map["rule"]
                rule_map["files"].append(file)
                rule_map["file_tasks"].append([])

                if not rule.accepts(file):
                    continue

                # Preprocessing Tasks
                # May include other preprocessors later...
                # Handle OCIO Color Management
                ocio_task = None
                ocio_cleanup_task = None
                colormanaged_file = None
                if rule.ocio_enabled:
                    # Color Conversion task
                    ocio_task = tasks.OCIODisplay(
                        input=file,
                        input_transform=rule.ocio_input_transform,
                        display_device=rule.ocio_display_device,
                        view_transform=rule.ocio_view_transform,
                    )
                    self._add_task(ocio_task)
                    rule_map["tasks"].append(ocio_task)
                    rule_map["file_tasks"][-1].append(ocio_task)
                    # Cleanup task
                    ocio_cleanup_task = ocio_task.cleanup_task(include_parent=True)
                    # The expected colormanaged_file
                    colormanaged_file = ocio_task.output

                # Encoding Tasks
                enabled_tasks = [t for t in rule.tasks if t.enabled]
                for parameterized_task in enabled_tasks:
                    task_type = parameterized_task.task
                    task_parameters = parameterized_task.parameters

                    task_parameters["input"] = file
                    task = task_type(**task_parameters)
                    self._add_task(task)
                    rule_map["tasks"].append(task)
                    rule_map["file_tasks"][-1].append(task)

                    # Use color managed input files if available
                    task.input = colormanaged_file or file

                # Cleanup Tasks
                if rule.ocio_enabled and ocio_cleanup_task:
                    self._add_task(ocio_cleanup_task)
                    rule_map["tasks"].append(ocio_cleanup_task)
                    rule_map["file_tasks"][-1].append(ocio_cleanup_task)

                # This ensures we only use one Rule per File or FileSequence
                # This may or may not be desireable, but it's a reasonable
                # default for now.
                # Consider making this a global option once global settings
                # are introduced. Remember to add global settings...
                break

        self.tasks_count = len(self.tasks)

        handler = logging.StreamHandler()
        handler.setFormatter(RichFormatter())
        self.log.addHandler(handler)

        self.log_file = USER_DATA_DIR / "logs" / f"{self.id}.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(FileFormatter())
        self.log.addHandler(file_handler)

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

    def is_stopping(self):
        return self.status_request and self.status_request in Status.DONE

    def is_running(self):
        return self.status == Status.RUNNING

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
        rule = self.rules_map[self.current_rule]["rule"]
        if not self.is_stopping():
            self.progress = int(
                task_index * progress_per_step + progress * progress_per_step
            )
        payload = self._new_event_payload(
            type="progress_changed",
            label=f"{rule.name}",
            message=f"{task_index + 1} of {self.tasks_count} {task.name}",
        )
        self.signals.send("progress_changed", payload)

    def prepare_record(self, record):
        # Add run status to record
        record.run_id = self.id
        record.run_status = self.status
        record.run_progress = self.progress

        # Add rule to record
        rule = self.rules_map[self.current_rule]["rule"]
        record.rule_name = rule.name
        record.rule_description = rule.description
        record.rule_file_type = rule.file_type
        record.rule_file_patterns = rule.file_patterns

        # Add task to record
        if self.tasks:
            task = self.tasks[self.current_task]
            record.task_id = task.id
            record.task_name = task.name
            record.task_progress = task.progress

        # Capture all logging records
        self.log_records.append(record)

    def try_task(self, task, dry=False):
        with record_type(self.log, "task_title"):
            self.log.info("")

        if dry:
            self.artifacts.append(task.output)
            return Status.SUCCESS

        # Start Task in Thread
        task_thread = Thread(target=task)
        task_thread.start()

        # Wait for task to finish
        while True:
            self.signals.send("await_task", self._new_event_payload(task=task))
            if self.status_request == Status.CANCELLED:
                task.request(Status.CANCELLED)
                task.wait()
                return task.status
            if task.status in Status.DONE:
                self.artifacts.append(task.output)
                return task.status
            time.sleep(0.1)

    def run(self, dry: bool = False):

        self.log.info(f"\nEnabled Rules ({len(self.rules_map)})")
        self.log.info(
            "\n".join(
                [f"  [{(' ', 'x')[rule.enabled]}] {rule.name}" for rule in self.rules]
            )
        )

        self.log.info("\nStarting Run...")
        self.set_status(Status.RUNNING)

        for rule_idx, rule_map in enumerate(self.rules_map):
            if not rule_map["tasks"]:
                continue

            self.current_rule = rule_idx
            rule = rule_map["rule"]
            task = None
            self.log.info(f"Rule {rule.name}")

            for file, file_tasks in zip(rule_map["files"], rule_map["file_tasks"]):
                self.log.info(f"  File {file.format()}")

                for task in file_tasks:
                    task_idx = rule_map["tasks"].index(task)
                    self.current_task = task_idx

                    # Send before_task signal
                    self.signals.send(
                        "before_task", self._new_event_payload(rule=rule, task=task)
                    )

                    # Check if user has requested cancel
                    if self.status_request == Status.CANCELLED:
                        break

                    # Try the task in a background thread
                    status = self.try_task(task, dry)
                    if status == Status.FAILED:
                        self.set_status(Status.FAILED)
                        break

            if self.status_request == Status.CANCELLED:
                return self.accept(Status.CANCELLED)

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
    ProgressDialog.from_runner(runner)
    runner.run()


if __name__ == "__main__":
    main()
